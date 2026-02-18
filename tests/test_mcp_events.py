import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.mcp_loop import (  # noqa: E402
    Event,
    EventBus,
    TOPIC_TASK_RESULT_RAW,
    TOPIC_TASK_ASSIGNED,
    TOPIC_GATE_VERDICT,
    TOPIC_PROMOTION_DECISION,
    load_control_events,
    materialize_control_ledger,
    load_event_envelopes,
    replay_task_result_events,
)


def test_event_bus_deduplicates_by_event_id(tmp_path: Path) -> None:
    event_log = tmp_path / "events.jsonl"
    bus = EventBus(event_log=event_log)
    event = Event(
        topic=TOPIC_TASK_RESULT_RAW,
        run_id="run-1",
        payload={"task_id": "t1", "status": "PASS", "attempt": 1},
        event_id="evt-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    )
    bus.publish(event)
    bus.publish(event)
    rows = load_event_envelopes(event_log=event_log, run_id="run-1")
    assert len(rows) == 1
    assert rows[0]["event_id"] == "evt-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    assert rows[0]["sequence"] == 1


def test_replay_task_result_events_orders_by_ts_then_event_id(tmp_path: Path) -> None:
    event_log = tmp_path / "events.jsonl"
    lines = [
        {
            "schema_version": "0.2.0",
            "sequence": 2,
            "event_id": "evt-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "ts": "2026-02-14T00:00:01Z",
            "topic": TOPIC_TASK_RESULT_RAW,
            "run_id": "run-2",
            "payload": {"task_id": "t1", "attempt": 2, "status": "PASS"},
        },
        {
            "schema_version": "0.2.0",
            "sequence": 1,
            "event_id": "evt-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "ts": "2026-02-14T00:00:00Z",
            "topic": TOPIC_TASK_RESULT_RAW,
            "run_id": "run-2",
            "payload": {"task_id": "t1", "attempt": 1, "status": "FAIL"},
        },
    ]
    event_log.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")

    replayed = replay_task_result_events(event_log=event_log, run_id="run-2")
    attempts = [item["payload"]["attempt"] for item in replayed]
    assert attempts == [1, 2]


def test_control_events_materialize_deterministic_ledger(tmp_path: Path) -> None:
    event_log = tmp_path / "events.jsonl"
    lines = [
        {
            "schema_version": "0.2.0",
            "sequence": 3,
            "event_id": "evt-cccccccccccccccccccccccccccccccc",
            "ts": "2026-02-18T00:00:03Z",
            "topic": TOPIC_PROMOTION_DECISION,
            "run_id": "run-3",
            "payload": {"decision": "APPROVE"},
        },
        {
            "schema_version": "0.2.0",
            "sequence": 1,
            "event_id": "evt-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "ts": "2026-02-18T00:00:01Z",
            "topic": TOPIC_TASK_ASSIGNED,
            "run_id": "run-3",
            "payload": {"task_id": "t1"},
        },
        {
            "schema_version": "0.2.0",
            "sequence": 2,
            "event_id": "evt-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "ts": "2026-02-18T00:00:02Z",
            "topic": TOPIC_GATE_VERDICT,
            "run_id": "run-3",
            "payload": {"verdict": "APPROVE"},
        },
    ]
    event_log.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")

    control_events = load_control_events(event_log=event_log, run_id="run-3")
    assert [item.sequence for item in control_events] == [1, 2, 3]
    ledger = materialize_control_ledger(control_events)
    assert ledger["event_count"] == 3
    assert ledger["task_assigned_count"] == 1
    assert ledger["gate_verdict"]["verdict"] == "APPROVE"
    assert ledger["promotion_decision"]["decision"] == "APPROVE"
