#!/usr/bin/env python
"""Dispatcher/supervisor for orchestrator-owned child workers."""

from __future__ import annotations

import argparse
import json
import sys
import time
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
    TOPIC_TASK_RESULT,
)


WorkerFn = Callable[[dict[str, Any]], dict[str, Any]]


def load_work_queue(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    for key in ("run_id", "max_workers", "tasks"):
        if key not in payload:
            raise ValueError(f"missing required key in work.queue: {key}")
    if not isinstance(payload["tasks"], list) or not payload["tasks"]:
        raise ValueError("work.queue tasks must be a non-empty list")
    return payload


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
        max_workers = max(1, int(work_queue["max_workers"]))

        tasks_by_id = {task["task_id"]: dict(task) for task in work_queue["tasks"]}
        pending = set(tasks_by_id.keys())
        completed: set[str] = set()
        results: list[dict[str, Any]] = []
        model_cursor = 0

        while pending:
            ready = []
            for task_id in sorted(pending):
                task = tasks_by_id[task_id]
                deps = set(task.get("dependencies", []))
                if deps.issubset(completed):
                    ready.append(task)

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
                            "task_id": task["task_id"],
                            "goal": task.get("goal", ""),
                            "worker_model": task["worker_model"],
                        },
                    )
                )

            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {pool.submit(self.worker_fn, task): task for task in wave}
                for future in as_completed(futures):
                    task = futures[future]
                    result = future.result()
                    result.setdefault("task_id", task["task_id"])
                    result.setdefault("worker_model", task["worker_model"])
                    results.append(result)
                    self.bus.publish(
                        Event(
                            topic=TOPIC_TASK_RESULT,
                            run_id=run_id,
                            payload=result,
                        )
                    )
                    completed.add(task["task_id"])
                    pending.remove(task["task_id"])

        return {
            "run_id": run_id,
            "dispatched_count": len(results),
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
