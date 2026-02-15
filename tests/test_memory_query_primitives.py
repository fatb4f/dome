from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_query_primitives_views_exist_and_return_rows(tmp_path: Path) -> None:
    duckdb = pytest.importorskip("duckdb", reason="duckdb required for primitive view tests")

    db_path = tmp_path / "memory.duckdb"
    conn = duckdb.connect(str(db_path))
    try:
        schema_sql = (ROOT / "tools/telemetry/memory_schema.sql").read_text(encoding="utf-8")
        conn.execute(schema_sql)
        conn.execute(
            """
            INSERT INTO task_fact (
              run_id, task_id, status, failure_reason_code, policy_reason_code, reason_code,
              attempts, duration_ms, worker_model, evidence_bundle_path, evidence_capsule_path, updated_ts
            )
            VALUES
              ('run-1','task-a','FAIL','TRANSIENT.NETWORK','','TRANSIENT.NETWORK',2,10,'gpt-5.3','','memory://capsule/run-1/task-a','2026-02-15T00:00:00Z'),
              ('run-1','task-b','PASS','','','',1,5,'gpt-5.3','','memory://capsule/run-1/task-b','2026-02-15T00:00:01Z'),
              ('run-1','task-c','FAIL','', 'POLICY.NEEDS_HUMAN','',1,7,'gpt-5.2','','memory://capsule/run-1/task-c','2026-02-15T00:00:02Z')
            """
        )

        recent_failures = conn.execute(
            "SELECT task_id FROM mv_recent_failures_by_taskspec ORDER BY updated_ts DESC, task_id ASC"
        ).fetchall()
        assert [row[0] for row in recent_failures] == ["task-c", "task-a"]

        rollup = conn.execute(
            "SELECT failure_reason_code, status, task_count FROM mv_gate_rollup_by_failure_reason_code ORDER BY failure_reason_code, status"
        ).fetchall()
        assert rollup

        denials = conn.execute(
            "SELECT task_id, policy_reason_code FROM mv_guard_denials_by_policy_reason_code ORDER BY task_id"
        ).fetchall()
        assert denials == [("task-c", "POLICY.NEEDS_HUMAN")]
    finally:
        conn.close()
