#!/usr/bin/env python
"""Dispatcher/supervisor for orchestrator-owned child workers."""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

# Allow direct script execution: `python tools/orchestrator/dispatcher.py ...`
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.mcp_loop import (
    Event,
    EventBus,
    TOPIC_TASK_ASSIGNED,
    TOPIC_TASK_RESULT_RAW,
)
from tools.orchestrator.planner import validate_task_graph


WorkerFn = Callable[[dict[str, Any]], dict[str, Any]]

TASK_DIRECT_METHOD_KEYS = {"method", "tool_method", "raw_call", "command"}
SPAWN_SPEC_REQUIRED_KEYS = {
    "run_id",
    "wave_id",
    "node_id",
    "node_execution_id",
    "task_spec_ref",
    "tool_profile_ref",
    "container_ref",
    "action_spec",
    "determinism_seed",
    "inputs_hash",
}


def _task_tiebreak_key(task: dict[str, Any]) -> tuple[str, str, str, str]:
    """Deterministic scheduler ordering key: priority -> created_at -> payload_digest -> task_id."""
    priority = str(task.get("priority", "normal"))
    created_at = str(task.get("created_at", ""))
    payload_digest = str(task.get("payload_digest", ""))
    task_id = str(task.get("task_id", ""))
    return (priority, created_at, payload_digest, task_id)


def load_work_queue(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    for key in ("run_id", "max_workers", "tasks"):
        if key not in payload:
            raise ValueError(f"missing required key in work.queue: {key}")
    if not isinstance(payload["tasks"], list) or not payload["tasks"]:
        raise ValueError("work.queue tasks must be a non-empty list")
    validate_task_graph(payload["tasks"])
    return payload


def _requested_method(task: dict[str, Any]) -> str | None:
    if isinstance(task.get("requested_method"), str):
        return str(task["requested_method"])
    tool_call = task.get("tool_call")
    if isinstance(tool_call, dict) and isinstance(tool_call.get("method"), str):
        return str(tool_call["method"])
    return None


def validate_tool_contract(task: dict[str, Any]) -> None:
    direct = sorted(TASK_DIRECT_METHOD_KEYS.intersection(task.keys()))
    if direct:
        raise ValueError(f"task '{task.get('task_id', '?')}' contains forbidden direct method keys: {direct}")

    requested_method = _requested_method(task)
    if requested_method is None:
        return
    contract = task.get("tool_contract")
    if not isinstance(contract, dict):
        raise ValueError(
            f"task '{task.get('task_id', '?')}' requested method '{requested_method}' without tool_contract"
        )
    allowed = contract.get("allowed_methods")
    if not isinstance(allowed, list) or not all(isinstance(item, str) for item in allowed):
        raise ValueError(
            f"task '{task.get('task_id', '?')}' has invalid tool_contract.allowed_methods"
        )
    if requested_method not in set(allowed):
        raise ValueError(
            f"task '{task.get('task_id', '?')}' requested out-of-contract method '{requested_method}'"
        )


def validate_spawn_spec(spawn_spec: dict[str, Any], expected_run_id: str) -> None:
    if not isinstance(spawn_spec, dict):
        raise ValueError("spawn_spec must be an object")
    keys = set(spawn_spec.keys())
    missing = sorted(SPAWN_SPEC_REQUIRED_KEYS - keys)
    if missing:
        raise ValueError(f"spawn_spec missing required keys: {missing}")
    unknown = sorted(keys - SPAWN_SPEC_REQUIRED_KEYS)
    if unknown:
        raise ValueError(f"spawn_spec contains unknown keys: {unknown}")
    if str(spawn_spec.get("run_id")) != expected_run_id:
        raise ValueError("spawn_spec.run_id must match work_queue.run_id")
    action_spec = spawn_spec.get("action_spec")
    if not isinstance(action_spec, dict):
        raise ValueError("spawn_spec.action_spec must be an object")
    if not isinstance(action_spec.get("intent"), str) or not action_spec.get("intent"):
        raise ValueError("spawn_spec.action_spec.intent must be a non-empty string")


def _default_worker(task: dict[str, Any]) -> dict[str, Any]:
    time.sleep(0.01)
    return {
        "task_id": task["task_id"],
        "status": "FAIL" if bool(task.get("fail", False)) else "PASS",
        "notes": "dispatcher synthetic worker result",
        "worker_model": task.get("worker_model", "gpt-5.3"),
    }


class DispatcherSupervisor:
    """Schedules worker tasks while enforcing dependency and lease discipline.

    This component intentionally does not perform promotion decisions.
    """

    def __init__(
        self,
        bus: EventBus,
        worker_models: list[str] | None = None,
        worker_fn: WorkerFn | None = None,
    ) -> None:
        self.bus = bus
        self.worker_models = worker_models or ["gpt-5.3", "gpt-5.2"]
        self.worker_fn = worker_fn or _default_worker

    def dispatch(self, work_queue: dict[str, Any]) -> dict[str, Any]:
        run_id = str(work_queue["run_id"])
        wave_id = f"{run_id}-wave-001"
        max_workers = max(1, int(work_queue["max_workers"]))
        validate_task_graph(work_queue["tasks"])
        for task in work_queue["tasks"]:
            validate_tool_contract(task)
            if "spawn_spec" in task:
                validate_spawn_spec(task["spawn_spec"], expected_run_id=run_id)

        tasks_by_id = {task["task_id"]: dict(task) for task in work_queue["tasks"]}
        pending = set(tasks_by_id.keys())
        completed: set[str] = set()
        results: list[dict[str, Any]] = []
        dispatch_order: list[dict[str, Any]] = []
        model_cursor = 0

        while pending:
            ready = []
            for task_id in sorted(pending):
                task = tasks_by_id[task_id]
                deps = set(task.get("dependencies", []))
                if deps.issubset(completed):
                    ready.append(task)
            ready.sort(key=_task_tiebreak_key)

            if not ready:
                raise ValueError("no dispatchable tasks remaining; dependency cycle or missing dependency")

            wave = ready[:max_workers]
            for task in wave:
                if "worker_model" not in task:
                    task["worker_model"] = self.worker_models[model_cursor % len(self.worker_models)]
                    model_cursor += 1
                self.bus.publish(
                    Event(
                        topic=TOPIC_TASK_ASSIGNED,
                        run_id=run_id,
                        payload={
                            "wave_id": wave_id,
                            "task_id": task["task_id"],
                            "goal": task.get("goal", ""),
                            "worker_model": task["worker_model"],
                            "dispatch_tiebreak": {
                                "priority": str(task.get("priority", "normal")),
                                "created_at": str(task.get("created_at", "")),
                                "payload_digest": str(task.get("payload_digest", "")),
                                "task_id": task["task_id"],
                            },
                        },
                    )
                )
                dispatch_order.append(
                    {
                        "wave_id": wave_id,
                        "task_id": task["task_id"],
                        "dispatch_tiebreak": {
                            "priority": str(task.get("priority", "normal")),
                            "created_at": str(task.get("created_at", "")),
                            "payload_digest": str(task.get("payload_digest", "")),
                            "task_id": task["task_id"],
                        },
                    }
                )

            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {pool.submit(self.worker_fn, task): task for task in wave}
                for future in as_completed(futures):
                    task = futures[future]
                    try:
                        result = future.result()
                    except Exception as exc:
                        result = {
                            "task_id": task["task_id"],
                            "status": "FAIL",
                            "reason_code": "EXEC.NONZERO_EXIT",
                            "notes": "worker raised exception during task execution",
                            "error_type": type(exc).__name__,
                            "error_message": str(exc),
                            "error_traceback": traceback.format_exc(limit=20),
                        }
                    result.setdefault("task_id", task["task_id"])
                    result.setdefault("worker_model", task["worker_model"])
                    results.append(result)
                    attempt_history = result.get("attempt_history")
                    if isinstance(attempt_history, list) and attempt_history:
                        for attempt in attempt_history:
                            self.bus.publish(
                                Event(
                                    topic=TOPIC_TASK_RESULT_RAW,
                                    run_id=run_id,
                                    payload={
                                        "task_id": result["task_id"],
                                        "status": attempt.get("status"),
                                        "attempt": int(attempt.get("attempt", 1)),
                                        "reason_code": attempt.get("reason_code"),
                                        "notes": attempt.get("notes"),
                                        "worker_model": result.get("worker_model"),
                                        "duration_ms": int(attempt.get("duration_ms", 0)),
                                    },
                                )
                            )
                    else:
                        self.bus.publish(
                            Event(
                                topic=TOPIC_TASK_RESULT_RAW,
                                run_id=run_id,
                                payload=result,
                            )
                        )
                    completed.add(task["task_id"])
                    pending.remove(task["task_id"])

        return {
            "run_id": run_id,
            "wave_id": wave_id,
            "dispatched_count": len(results),
            "dispatch_order": dispatch_order,
            "results": sorted(results, key=lambda item: item["task_id"]),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dispatch a dome work.queue through worker supervisor")
    parser.add_argument("--work-queue", type=Path, required=True)
    parser.add_argument("--event-log", type=Path, default=Path("ops/runtime/mcp_events.jsonl"))
    parser.add_argument("--worker-models", default="gpt-5.3,gpt-5.2")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    work_queue = load_work_queue(args.work_queue)
    models = [model.strip() for model in args.worker_models.split(",") if model.strip()]
    bus = EventBus(event_log=args.event_log)
    supervisor = DispatcherSupervisor(bus=bus, worker_models=models)
    summary = supervisor.dispatch(work_queue)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
