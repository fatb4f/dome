import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.telemetry import memory_api  # noqa: E402


class FakeCursor:
    def __init__(self, rows, cols):
        self._rows = rows
        self.description = [(name,) for name in cols]

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class FakeConn:
    def __init__(self):
        self.last_query = ""
        self.last_params = []
        self._select_task_rows = [
            ("run-002", "task-b", "PASS", "", 1, 15, "gpt-5.3", "memory://capsule/run-002/task-b", "2026-02-15T00:00:02Z"),
            ("run-001", "task-a", "FAIL", "TRANSIENT.NETWORK", 2, 55, "gpt-5.2", "memory://capsule/run-001/task-a", "2026-02-15T00:00:01Z"),
        ]

    def execute(self, query, params=None):
        self.last_query = query
        self.last_params = list(params or [])
        q = " ".join(query.split()).lower()
        if "from task_fact where run_id =" in q:
            return FakeCursor(
                [("run-001", "task-a", "PASS", "", 1, 10, "gpt-5.3", "memory://capsule/run-001/task-a")],
                ["run_id", "task_id", "status", "reason_code", "attempts", "duration_ms", "worker_model", "evidence_capsule_path"],
            )
        if "from run_fact where run_id =" in q:
            return FakeCursor(
                [("run-001", "main", "APPROVE", "PROMOTE", "APPROVE", 12, 0.9, "abc", "summary.json", "state.space.json")],
                ["run_id", "base_ref", "gate_status", "substrate_status", "promotion_decision", "risk_score", "confidence", "repo_commit_sha", "summary_path", "state_space_path"],
            )
        if "from task_fact" in q:
            return FakeCursor(
                self._select_task_rows,
                ["run_id", "task_id", "status", "reason_code", "attempts", "duration_ms", "worker_model", "evidence_capsule_path", "updated_ts"],
            )
        return FakeCursor([], ["ok"])

    def close(self):
        pass


def test_query_priors_uses_stable_sort_and_limit(monkeypatch):
    fake = FakeConn()
    monkeypatch.setattr(memory_api, "_connect", lambda _: fake)
    out = memory_api.query_priors(
        db_path=Path("/tmp/memory.duckdb"),
        scope="task",
        filters={"reason_code": "TRANSIENT.NETWORK"},
        limit=1000,
    )
    assert len(out) == 2
    assert "order by updated_ts desc, run_id asc, task_id asc" in " ".join(fake.last_query.lower().split())
    assert fake.last_params[-1] == 200


def test_query_priors_rejects_invalid_scope() -> None:
    with pytest.raises(ValueError, match="invalid scope"):
        memory_api.query_priors(Path("/tmp/db"), scope="invalid")


def test_get_run_summary_shapes_output(monkeypatch):
    fake = FakeConn()
    monkeypatch.setattr(memory_api, "_connect", lambda _: fake)
    out = memory_api.get_run_summary(Path("/tmp/memory.duckdb"), "run-001")
    assert out["run"]["run_id"] == "run-001"
    assert out["tasks"][0]["task_id"] == "task-a"


def test_upsert_capsule_validates_schema(monkeypatch):
    fake = FakeConn()
    monkeypatch.setattr(memory_api, "_connect", lambda _: fake)
    payload = json.loads((ROOT / "ssot/examples/evidence.capsule.json").read_text(encoding="utf-8"))
    out = memory_api.upsert_capsule(
        db_path=Path("/tmp/memory.duckdb"),
        capsule_payload=payload,
        run_id="run-001",
        task_id="task-001",
        status="PASS",
        reason_code=None,
    )
    assert out["ok"] is True
    assert out["run_id"] == "run-001"


def test_health_reports_checkpoint(tmp_path: Path) -> None:
    checkpoint = tmp_path / "state.json"
    checkpoint.write_text(json.dumps({"processed_runs": ["r1", "r2"]}), encoding="utf-8")
    out = memory_api.health(checkpoint)
    assert out["daemon"] == "ok"
    assert out["processed_runs"] == 2

