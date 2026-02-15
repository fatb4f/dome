import json
from pathlib import Path
import sys
import types


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.telemetry import memoryd  # noqa: E402


def test_pending_runs_is_stable_and_filtered() -> None:
    discovered = ["run-001", "run-002", "run-003"]
    processed = ["run-002"]
    assert memoryd.pending_runs(discovered, processed) == ["run-001", "run-003"]


def test_checkpoint_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    payload = {"processed_runs": ["run-001", "run-002"]}
    memoryd.save_checkpoint(path, payload)
    out = memoryd.load_checkpoint(path)
    assert out == payload


def test_snapshot_from_run_dir_defaults_when_artifacts_missing(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-xyz"
    run_dir.mkdir(parents=True)
    out = memoryd.snapshot_from_run_dir(run_dir)
    assert out.run_id == "run-xyz"
    assert out.base_ref == "unknown"
    assert out.gate_status == "UNKNOWN"
    assert out.promotion_decision == "UNKNOWN"


def test_snapshot_from_run_dir_reads_primary_fields(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-abc"
    (run_dir / "gate").mkdir(parents=True)
    (run_dir / "promotion").mkdir(parents=True)
    (run_dir / "work.queue.json").write_text(json.dumps({"base_ref": "main"}), encoding="utf-8")
    (run_dir / "gate" / "gate.decision.json").write_text(
        json.dumps({"status": "APPROVE", "substrate_status": "PROMOTE", "risk_score": 12, "confidence": 0.91}),
        encoding="utf-8",
    )
    (run_dir / "promotion" / "promotion.decision.json").write_text(
        json.dumps({"decision": "APPROVE"}),
        encoding="utf-8",
    )
    (run_dir / "run.manifest.json").write_text(
        json.dumps({"runtime": {"repo_commit_sha": "abc123"}}),
        encoding="utf-8",
    )
    out = memoryd.snapshot_from_run_dir(run_dir)
    assert out.base_ref == "main"
    assert out.gate_status == "APPROVE"
    assert out.substrate_status == "PROMOTE"
    assert out.risk_score == 12
    assert abs(out.confidence - 0.91) < 0.0001
    assert out.repo_commit_sha == "abc123"


def test_task_and_event_snapshots_from_run_dir(tmp_path: Path) -> None:
    run_root = tmp_path / "runs"
    run_dir = run_root / "run-123"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "task_id": "task-a",
                        "status": "FAIL",
                        "reason_code": "TRANSIENT.NETWORK",
                        "attempts": 2,
                        "duration_ms": 42,
                        "worker_model": "gpt-5.3",
                        "evidence_bundle_path": "ev-a.json",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (run_root.parent / "mcp_events.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "schema_version": "0.2.0",
                        "sequence": 1,
                        "event_id": "evt-1",
                        "ts": "2026-02-15T00:00:00Z",
                        "topic": "task.result",
                        "run_id": "run-123",
                        "payload": {"task_id": "task-a", "status": "FAIL"},
                    }
                )
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    tasks = memoryd.task_snapshots_from_run_dir(run_dir, run_root)
    events = memoryd.event_snapshots_from_run_dir(run_dir, run_root)
    assert len(tasks) == 1
    assert tasks[0].failure_reason_code == "TRANSIENT.NETWORK"
    assert tasks[0].updated_ts == "2026-02-15T00:00:00Z"
    assert len(events) == 1
    assert events[0].event_id == "evt-1"


def test_run_once_upserts_task_and_event_facts(monkeypatch, tmp_path: Path) -> None:
    run_root = tmp_path / "runs"
    run_dir = run_root / "run-xyz"
    (run_dir / "gate").mkdir(parents=True)
    (run_dir / "promotion").mkdir(parents=True)
    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "task_id": "task-a",
                        "status": "PASS",
                        "reason_code": None,
                        "attempts": 1,
                        "duration_ms": 1,
                        "worker_model": "gpt-5.3",
                        "evidence_bundle_path": "ev-a.json",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "work.queue.json").write_text(json.dumps({"base_ref": "main"}), encoding="utf-8")
    (run_dir / "gate" / "gate.decision.json").write_text(
        json.dumps({"status": "APPROVE", "substrate_status": "PROMOTE", "risk_score": 1, "confidence": 0.9}),
        encoding="utf-8",
    )
    (run_dir / "promotion" / "promotion.decision.json").write_text(
        json.dumps({"decision": "APPROVE"}),
        encoding="utf-8",
    )
    (run_root.parent / "mcp_events.jsonl").write_text(
        json.dumps(
            {
                "schema_version": "0.2.0",
                "sequence": 1,
                "event_id": "evt-xyz",
                "ts": "2026-02-15T00:00:00Z",
                "topic": "task.result",
                "run_id": "run-xyz",
                "payload": {"task_id": "task-a", "status": "PASS"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    checkpoint = tmp_path / "checkpoints/state.json"
    schema = tmp_path / "schema.sql"
    schema.write_text("-- no-op", encoding="utf-8")

    class FakeConn:
        def __init__(self) -> None:
            self.queries: list[str] = []

        def execute(self, query, params=None):
            self.queries.append(" ".join(str(query).split()).lower())
            return self

        def close(self):
            pass

    fake_conn = FakeConn()
    fake_duckdb = types.SimpleNamespace(connect=lambda _: fake_conn)
    monkeypatch.setitem(sys.modules, "duckdb", fake_duckdb)

    processed = memoryd.run_once(tmp_path / "memory.duckdb", run_root, checkpoint, schema)
    assert processed == 1
    assert any("insert or replace into task_fact" in q for q in fake_conn.queries)
    assert any("insert or replace into event_fact" in q for q in fake_conn.queries)

    processed_second = memoryd.run_once(tmp_path / "memory.duckdb", run_root, checkpoint, schema)
    assert processed_second == 0
