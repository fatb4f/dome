import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.telemetry import memory_binder, memoryd  # noqa: E402


def _binder_input_rows_from_snapshots(snapshots: list[memoryd.TaskSnapshot]) -> list[tuple[object, ...]]:
    rows: list[tuple[object, ...]] = []
    for item in snapshots:
        rows.append(
            (
                item.run_id,
                item.task_id,
                item.status,
                item.failure_reason_code,
                item.policy_reason_code,
                item.attempts,
                item.duration_ms,
                item.worker_model,
                item.updated_ts,
            )
        )
    rows.sort(key=lambda row: (str(row[8]), str(row[0]), str(row[1])), reverse=True)
    return rows


def test_memoryd_to_binder_derivation_is_deterministic(tmp_path: Path) -> None:
    run_root = tmp_path / "runs"
    run_dir = run_root / "run-100"
    run_dir.mkdir(parents=True)

    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "task_id": "task-a",
                        "status": "FAIL",
                        "failure_reason_code": "EXEC.NONZERO_EXIT",
                        "attempts": 2,
                        "duration_ms": 30,
                        "worker_model": "gpt-5.3",
                        "evidence_bundle_path": "ev-a.json",
                    },
                    {
                        "task_id": "task-b",
                        "status": "PASS",
                        "policy_reason_code": "POLICY.NEEDS_HUMAN",
                        "attempts": 1,
                        "duration_ms": 10,
                        "worker_model": "gpt-5.3",
                        "evidence_bundle_path": "ev-b.json",
                    },
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
                        "event_id": "evt-a",
                        "ts": "2026-02-15T00:00:00Z",
                        "topic": "task.result",
                        "run_id": "run-100",
                        "payload": {"task_id": "task-a", "status": "FAIL"},
                    }
                ),
                json.dumps(
                    {
                        "schema_version": "0.2.0",
                        "sequence": 2,
                        "event_id": "evt-b",
                        "ts": "2026-02-15T00:00:01Z",
                        "topic": "task.result",
                        "run_id": "run-100",
                        "payload": {"task_id": "task-b", "status": "PASS"},
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    snapshots = memoryd.task_snapshots_from_run_dir(run_dir, run_root)
    rows = _binder_input_rows_from_snapshots(snapshots)
    derived_left = memory_binder.derive_rows_from_task_rows(rows, mode="strict")
    derived_right = memory_binder.derive_rows_from_task_rows(rows, mode="strict")

    keys_left = [(item.task_id, item.derived_upsert_key, item.fingerprint_hash) for item in derived_left]
    keys_right = [(item.task_id, item.derived_upsert_key, item.fingerprint_hash) for item in derived_right]
    assert keys_left == keys_right
    assert sorted(item.task_id for item in derived_left) == ["task-a", "task-b"]
