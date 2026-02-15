import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.telemetry import memory_binder  # noqa: E402


class FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class FakeConn:
    def __init__(self, task_rows):
        self.task_rows = task_rows
        self.binder_rows: dict[str, list[object]] = {}

    def execute(self, query, params=None):
        q = " ".join(str(query).split()).lower()
        if q.startswith("select") and "from task_fact" in q:
            return FakeCursor(self.task_rows)
        if "insert or replace into binder_fact" in q:
            assert params is not None
            self.binder_rows[str(params[0])] = list(params)
            return self
        return self

    def close(self):
        pass


def test_fingerprint_hash_is_canonical() -> None:
    left = {"status": "FAIL", "attempts": 2, "worker_model": "gpt-5.3"}
    right = {"worker_model": "gpt-5.3", "status": "FAIL", "attempts": 2}
    assert memory_binder.fingerprint_hash(left) == memory_binder.fingerprint_hash(right)


def test_binder_run_once_is_replay_idempotent(monkeypatch, tmp_path: Path) -> None:
    fake_conn = FakeConn(
        [
            ("run-1", "task-c", "PASS", "", "POLICY.NEEDS_HUMAN", 1, 7, "gpt-5.2", "2026-02-15T00:00:02Z"),
            ("run-1", "task-b", "PASS", "", "", 1, 5, "gpt-5.3", "2026-02-15T00:00:01Z"),
            ("run-1", "task-a", "FAIL", "TRANSIENT.NETWORK", "", 2, 10, "gpt-5.3", "2026-02-15T00:00:00Z"),
        ]
    )
    fake_duckdb = types.SimpleNamespace(connect=lambda _: fake_conn)
    monkeypatch.setitem(sys.modules, "duckdb", fake_duckdb)

    db_path = tmp_path / "memory.duckdb"
    schema_path = ROOT / "tools/telemetry/memory_schema.sql"
    first = memory_binder.run_once(db_path=db_path, schema_path=schema_path, mode="strict")
    second = memory_binder.run_once(db_path=db_path, schema_path=schema_path, mode="strict")
    assert first == 2
    assert second == 2
    assert len(fake_conn.binder_rows) == 2
    task_ids = sorted(params[3] for params in fake_conn.binder_rows.values())
    assert task_ids == ["task-a", "task-c"]


def test_binder_upsert_key_is_stable(monkeypatch, tmp_path: Path) -> None:
    fake_conn = FakeConn(
        [
            ("run-1", "task-a", "FAIL", "EXEC.NONZERO_EXIT", "", 1, 9, "gpt-5.3", "2026-02-15T00:00:00Z"),
        ]
    )
    fake_duckdb = types.SimpleNamespace(connect=lambda _: fake_conn)
    monkeypatch.setitem(sys.modules, "duckdb", fake_duckdb)

    db_path = tmp_path / "memory.duckdb"
    schema_path = ROOT / "tools/telemetry/memory_schema.sql"
    memory_binder.run_once(db_path=db_path, schema_path=schema_path, mode="strict")
    first_key = next(iter(fake_conn.binder_rows.keys()))
    memory_binder.run_once(db_path=db_path, schema_path=schema_path, mode="strict")
    second_key = next(iter(fake_conn.binder_rows.keys()))
    assert first_key == second_key
