#!/usr/bin/env python
"""Implementer execution harness for Phase 2 MVP."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from pathlib import Path
from typing import Any, Callable

# Allow direct script execution: `python tools/orchestrator/implementers.py ...`
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.dispatcher import DispatcherSupervisor, WorkerFn, load_work_queue
from tools.orchestrator.io_utils import atomic_write_json
from tools.orchestrator.mcp_loop import Event, EventBus, TOPIC_TASK_RESULT, TOPIC_TASK_RESULT_RAW
from tools.orchestrator.security import assert_runtime_path, redact_sensitive_payload


def _sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_transient_failure(result: dict[str, Any]) -> bool:
    if result.get("status") != "FAIL":
        return False
    if bool(result.get("transient", False)):
        return True
    reason = str(result.get("reason_code", ""))
    return reason.startswith("TRANSIENT.")


class RetryingWorker:
    """Retry wrapper for transient worker failures."""

    def __init__(
        self,
        worker_fn: WorkerFn,
        max_retries: int,
        base_backoff_ms: int = 50,
        max_backoff_ms: int = 2000,
        sleep_fn: Callable[[float], None] | None = None,
    ) -> None:
        self.worker_fn = worker_fn
        self.max_retries = max(0, max_retries)
        self.base_backoff_ms = max(1, int(base_backoff_ms))
        self.max_backoff_ms = max(self.base_backoff_ms, int(max_backoff_ms))
        self.sleep_fn = sleep_fn or time.sleep

    def _compute_backoff_ms(self, task_id: str, attempt: int) -> int:
        exp = self.base_backoff_ms * (2 ** max(0, attempt - 1))
        bounded = min(exp, self.max_backoff_ms)
        rng = random.Random(f"{task_id}:{attempt}")
        jitter = 1.0 + (rng.random() * 0.2)
        return int(bounded * jitter)

    def __call__(self, task: dict[str, Any]) -> dict[str, Any]:
        attempts = 0
        last: dict[str, Any] = {}
        history: list[dict[str, Any]] = []
        while True:
            attempts += 1
            started = time.perf_counter()
            raw = dict(self.worker_fn(task))
            duration_ms = int((time.perf_counter() - started) * 1000)
            raw.setdefault("task_id", task["task_id"])
            raw["attempt"] = attempts
            raw["duration_ms"] = duration_ms
            history.append(raw)
            last = dict(raw)
            last.setdefault("task_id", task["task_id"])
            last["attempts"] = attempts
            last["attempt_history"] = history
            last["retry_backoff_ms"] = [int(item.get("backoff_ms", 0)) for item in history[:-1]]
            if not _is_transient_failure(last):
                return last
            if attempts > self.max_retries:
                return last
            backoff_ms = self._compute_backoff_ms(task_id=str(task["task_id"]), attempt=attempts)
            raw["backoff_ms"] = backoff_ms
            last["retry_backoff_ms"] = [int(item.get("backoff_ms", 0)) for item in history]
            self.sleep_fn(backoff_ms / 1000.0)


class ImplementerHarness:
    """Runs dispatcher-supervised implementers and persists run artifacts."""

    def __init__(
        self,
        bus: EventBus,
        run_root: Path,
        worker_models: list[str] | None = None,
        worker_fn: WorkerFn | None = None,
        max_retries: int = 1,
        base_backoff_ms: int = 50,
        max_backoff_ms: int = 2000,
    ) -> None:
        self.bus = bus
        self.run_root = run_root
        wrapped_worker = RetryingWorker(
            worker_fn or self._default_worker,
            max_retries=max_retries,
            base_backoff_ms=base_backoff_ms,
            max_backoff_ms=max_backoff_ms,
        )
        self.dispatcher = DispatcherSupervisor(
            bus=bus,
            worker_models=worker_models or ["gpt-5.3", "gpt-5.2"],
            worker_fn=wrapped_worker,
        )

    @staticmethod
    def _default_worker(task: dict[str, Any]) -> dict[str, Any]:
        return {
            "task_id": task["task_id"],
            "status": "FAIL" if bool(task.get("fail", False)) else "PASS",
            "notes": "implementer synthetic worker result",
            "worker_model": task.get("worker_model", "gpt-5.3"),
        }

    def run(self, work_queue: dict[str, Any]) -> dict[str, Any]:
        summary = self.dispatcher.dispatch(work_queue)
        run_id = str(summary["run_id"])
        run_dir = self.run_root / run_id
        task_dir = run_dir / "task_results"
        evidence_dir = run_dir / "evidence"
        attempt_dir = run_dir / "attempts"
        dlq_dir = run_dir / "dlq"
        run_dir.mkdir(parents=True, exist_ok=True)
        task_dir.mkdir(parents=True, exist_ok=True)
        evidence_dir.mkdir(parents=True, exist_ok=True)
        attempt_dir.mkdir(parents=True, exist_ok=True)
        dlq_dir.mkdir(parents=True, exist_ok=True)

        atomic_write_json(run_dir / "work.queue.json", work_queue)
        task_records = []
        result_by_id = {str(item["task_id"]): item for item in summary["results"]}
        ordered_results: list[dict[str, Any]] = []
        for task in work_queue.get("tasks", []):
            task_id = str(task.get("task_id", ""))
            if task_id in result_by_id:
                ordered_results.append(result_by_id.pop(task_id))
        ordered_results.extend(result_by_id.values())

        for result in ordered_results:
            task_path = task_dir / f"{result['task_id']}.result.json"
            atomic_write_json(task_path, result)
            attempt_history = result.get("attempt_history", [])
            attempt_path = attempt_dir / f"{result['task_id']}.attempts.json"
            atomic_write_json(attempt_path, attempt_history)
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
            evidence = {
                "otel": {
                    "backend": "local-mvp",
                    "trace_id_hex": "0" * 32,
                    "span_id_hex": "0" * 16,
                    "project": "dome",
                    "run_id": run_id,
                },
                "signals": {
                    "run.id": run_id,
                    "task.id": result.get("task_id"),
                    "task.status": result.get("status"),
                    "task.attempts": int(result.get("attempts", 1)),
                    "task.retry_backoff_ms": int(sum(result.get("retry_backoff_ms", []) or [0])),
                    "task.notes": result.get("notes"),
                    "task.reason_code": result.get("reason_code"),
                    "task.worker_model": result.get("worker_model"),
                    "task.duration_ms": int(sum(int(item.get("duration_ms", 0)) for item in attempt_history)),
                },
                "artifacts": [
                    {
                        "path": str(task_path),
                        "sha256": _sha256_path(task_path),
                        "bytes": task_path.stat().st_size,
                    },
                    {
                        "path": str(attempt_path),
                        "sha256": _sha256_path(attempt_path),
                        "bytes": attempt_path.stat().st_size,
                    },
                ],
            }
            evidence = redact_sensitive_payload(evidence)
            evidence_path = evidence_dir / f"{result['task_id']}.evidence.bundle.telemetry.json"
            atomic_write_json(evidence_path, evidence)
            dlq_path: str | None = None
            if _is_transient_failure(result):
                dlq_payload = {
                    "run_id": run_id,
                    "task_id": result["task_id"],
                    "status": result.get("status"),
                    "reason_code": result.get("reason_code"),
                    "attempts": int(result.get("attempts", 1)),
                    "retry_backoff_ms": result.get("retry_backoff_ms", []),
                }
                dlq_file = dlq_dir / f"{result['task_id']}.dlq.json"
                atomic_write_json(dlq_file, dlq_payload)
                dlq_path = str(dlq_file)
            task_records.append(
                {
                    **result,
                    "task_result_path": str(task_path),
                    "attempt_history_path": str(attempt_path),
                    "evidence_bundle_path": str(evidence_path),
                    "dlq_path": dlq_path,
                }
            )
            self.bus.publish(
                Event(
                    topic=TOPIC_TASK_RESULT,
                    run_id=run_id,
                    payload={
                        "task_id": result["task_id"],
                        "status": result.get("status"),
                        "attempts": int(result.get("attempts", 1)),
                        "reason_code": result.get("reason_code"),
                        "worker_model": result.get("worker_model"),
                        "duration_ms": int(sum(int(item.get("duration_ms", 0)) for item in attempt_history)),
                        "evidence_bundle_path": str(evidence_path),
                    },
                )
            )

        persisted = {
            "run_id": run_id,
            "dispatched_count": len(task_records),
            "execution_order": [str(task.get("task_id", "")) for task in work_queue.get("tasks", [])],
            "results": task_records,
        }
        atomic_write_json(run_dir / "summary.json", persisted)
        return persisted


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run implementer harness from work.queue")
    parser.add_argument("--work-queue", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=Path("ops/runtime/runs"))
    parser.add_argument("--event-log", type=Path, default=Path("ops/runtime/mcp_events.jsonl"))
    parser.add_argument("--worker-models", default="gpt-5.3,gpt-5.2")
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--retry-base-ms", type=int, default=50)
    parser.add_argument("--retry-max-ms", type=int, default=2000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    assert_runtime_path(args.run_root, ROOT, "--run-root")
    assert_runtime_path(args.event_log, ROOT, "--event-log")
    work_queue = load_work_queue(args.work_queue)
    models = [model.strip() for model in args.worker_models.split(",") if model.strip()]
    bus = EventBus(event_log=args.event_log)
    harness = ImplementerHarness(
        bus=bus,
        run_root=args.run_root,
        worker_models=models,
        max_retries=args.max_retries,
        base_backoff_ms=args.retry_base_ms,
        max_backoff_ms=args.retry_max_ms,
    )
    summary = harness.run(work_queue)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
