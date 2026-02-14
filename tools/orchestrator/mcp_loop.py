#!/usr/bin/env python
"""MCP-first concurrent orchestrator scaffold.

The orchestrator owns pub/sub topics and authoritative state transitions.
Planner/Orchestrator/Gatekeeper default to a high-reliability control model.
Workers can use mixed models from a configurable pool.
"""

from __future__ import annotations

import argparse
import json
import queue
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

TOPIC_PLAN_CREATED = "plan.wave.created"
TOPIC_TASK_ASSIGNED = "task.assigned"
TOPIC_TASK_RESULT_RAW = "task.result.raw"
TOPIC_TASK_RESULT = "task.result"
TOPIC_GATE_REQUESTED = "gate.requested"
TOPIC_GATE_VERDICT = "gate.verdict"
TOPIC_PROMOTION_DECISION = "promotion.decision"


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


@dataclass
class Event:
    topic: str
    run_id: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: f"evt-{uuid.uuid4().hex}")
    schema_version: str = "0.2.0"
    ts: str = field(default_factory=utc_now)


class EventBus:
    """In-process pub/sub bus with optional JSONL event persistence."""

    def __init__(self, event_log: Path | None = None) -> None:
        self._topics: dict[str, queue.Queue[Event]] = {}
        self._event_log = event_log
        self._lock = threading.Lock()
        self._seen_event_ids: set[str] = set()
        self._sequence = 0
        if event_log is not None:
            event_log.parent.mkdir(parents=True, exist_ok=True)

    def subscribe(self, topic: str) -> queue.Queue[Event]:
        q = self._topics.get(topic)
        if q is None:
            q = queue.Queue()
            self._topics[topic] = q
        return q

    def publish(self, event: Event) -> None:
        with self._lock:
            if event.event_id in self._seen_event_ids:
                return
            self._seen_event_ids.add(event.event_id)
            self._sequence += 1
            sequence = self._sequence
            q = self.subscribe(event.topic)
            q.put(event)
            if self._event_log is not None:
                with self._event_log.open("a", encoding="utf-8") as fh:
                    fh.write(
                        json.dumps(
                            {
                                "schema_version": event.schema_version,
                                "sequence": sequence,
                                "event_id": event.event_id,
                                "ts": event.ts,
                                "topic": event.topic,
                                "run_id": event.run_id,
                                "payload": event.payload,
                            },
                            sort_keys=True,
                        )
                    )
                    fh.write("\n")


def load_event_envelopes(event_log: Path, run_id: str | None = None) -> list[dict[str, Any]]:
    if not event_log.exists():
        return []
    rows: list[dict[str, Any]] = []
    with event_log.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            event = json.loads(line)
            if run_id is not None and event.get("run_id") != run_id:
                continue
            rows.append(event)
    rows.sort(
        key=lambda item: (
            int(item.get("sequence", 0)),
            str(item.get("ts", "")),
            str(item.get("event_id", "")),
        )
    )
    return rows


def replay_task_result_events(event_log: Path, run_id: str) -> list[dict[str, Any]]:
    events = load_event_envelopes(event_log=event_log, run_id=run_id)
    return [
        event for event in events if event.get("topic") in {TOPIC_TASK_RESULT_RAW, TOPIC_TASK_RESULT}
    ]


@dataclass
class Task:
    task_id: str
    goal: str
    fail: bool = False
    worker_model: str | None = None


@dataclass
class WorkerResult:
    task_id: str
    status: str
    worker_model: str
    notes: str


@dataclass
class GateVerdict:
    verdict: str
    confidence: float
    risk: int
    model: str
    reasons: list[str]


class RalphOrchestrator:
    """Concurrent wave runner with deterministic-first promotion policy."""

    def __init__(
        self,
        bus: EventBus,
        max_workers: int,
        control_model: str,
        worker_models: list[str],
    ) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        if not worker_models:
            raise ValueError("worker_models cannot be empty")
        self.bus = bus
        self.max_workers = max_workers
        self.control_model = control_model
        self.worker_models = worker_models

    def run_wave(self, goal: str, tasks: list[Task]) -> dict[str, Any]:
        run_id = f"wave-{uuid.uuid4().hex[:10]}"
        self.bus.publish(
            Event(
                topic=TOPIC_PLAN_CREATED,
                run_id=run_id,
                payload={
                    "goal": goal,
                    "task_count": len(tasks),
                    "control_model": self.control_model,
                    "worker_models": self.worker_models,
                },
            )
        )

        for idx, task in enumerate(tasks):
            task.worker_model = self.worker_models[idx % len(self.worker_models)]
            self.bus.publish(
                Event(
                    topic=TOPIC_TASK_ASSIGNED,
                    run_id=run_id,
                    payload={
                        "task_id": task.task_id,
                        "goal": task.goal,
                        "worker_model": task.worker_model,
                    },
                )
            )

        results: list[WorkerResult] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = [pool.submit(self._run_worker, run_id, task) for task in tasks]
            for future in as_completed(futures):
                results.append(future.result())

        self.bus.publish(
            Event(
                topic=TOPIC_GATE_REQUESTED,
                run_id=run_id,
                payload={"result_count": len(results), "control_model": self.control_model},
            )
        )
        verdict = self._gate(results)
        self.bus.publish(
            Event(
                topic=TOPIC_GATE_VERDICT,
                run_id=run_id,
                payload=verdict.__dict__,
            )
        )
        promotion = "APPROVE" if verdict.verdict == "APPROVE" else "REJECT"
        self.bus.publish(
            Event(
                topic=TOPIC_PROMOTION_DECISION,
                run_id=run_id,
                payload={"decision": promotion},
            )
        )

        return {
            "run_id": run_id,
            "goal": goal,
            "control_model": self.control_model,
            "worker_models": self.worker_models,
            "results": [r.__dict__ for r in sorted(results, key=lambda x: x.task_id)],
            "gate": verdict.__dict__,
            "promotion": promotion,
        }

    def _run_worker(self, run_id: str, task: Task) -> WorkerResult:
        time.sleep(0.01)
        status = "FAIL" if task.fail else "PASS"
        result = WorkerResult(
            task_id=task.task_id,
            status=status,
            worker_model=task.worker_model or self.worker_models[0],
            notes="synthetic worker result",
        )
        self.bus.publish(Event(topic=TOPIC_TASK_RESULT, run_id=run_id, payload=result.__dict__))
        return result

    def _gate(self, results: list[WorkerResult]) -> GateVerdict:
        failed = [result.task_id for result in results if result.status != "PASS"]
        if failed:
            return GateVerdict(
                verdict="REJECT",
                confidence=0.95,
                risk=85,
                model=self.control_model,
                reasons=[f"deterministic failures: {', '.join(sorted(failed))}"],
            )
        return GateVerdict(
            verdict="APPROVE",
            confidence=0.9,
            risk=20,
            model=self.control_model,
            reasons=["all deterministic checks passed"],
        )


def parse_tasks(path: Path) -> list[Task]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    tasks = []
    for item in payload.get("tasks", []):
        tasks.append(
            Task(
                task_id=item["task_id"],
                goal=item.get("goal", ""),
                fail=bool(item.get("fail", False)),
            )
        )
    return tasks


def build_default_tasks() -> list[Task]:
    return [
        Task(task_id="task-001", goal="Run deterministic verification"),
        Task(task_id="task-002", goal="Apply constrained patch"),
        Task(task_id="task-003", goal="Re-run focused tests"),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one MCP-first concurrent orchestrator wave")
    parser.add_argument("--goal", default="stabilize concurrent loop baseline")
    parser.add_argument("--tasks-json", type=Path)
    parser.add_argument("--max-workers", type=int, default=2)
    parser.add_argument("--event-log", type=Path, default=Path("ops/runtime/mcp_events.jsonl"))
    parser.add_argument("--control-model", default="gpt-5.3-codex-high")
    parser.add_argument("--worker-models", default="gpt-5.3,gpt-5.2")
    args = parser.parse_args()

    tasks = parse_tasks(args.tasks_json) if args.tasks_json else build_default_tasks()
    worker_models = [model.strip() for model in args.worker_models.split(",") if model.strip()]
    bus = EventBus(event_log=args.event_log)
    orchestrator = RalphOrchestrator(
        bus=bus,
        max_workers=args.max_workers,
        control_model=args.control_model,
        worker_models=worker_models,
    )
    print(json.dumps(orchestrator.run_wave(goal=args.goal, tasks=tasks), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
