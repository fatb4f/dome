#!/usr/bin/env python
"""Bounded MCP/A2A-compatible memory API helpers over DuckDB."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT / "ops/memory/memory.duckdb"
DEFAULT_CHECKPOINT = ROOT / "ops/memory/checkpoints/materialize.state.json"
CAPSULE_SCHEMA = ROOT / "ssot/schemas/evidence.capsule.schema.json"


def _connect(db_path: Path) -> Any:
    try:
        import duckdb  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("duckdb is required for memory API operations") from exc
    return duckdb.connect(str(db_path))


def _row_to_dict(columns: list[str], row: list[Any] | tuple[Any, ...]) -> dict[str, Any]:
    return {columns[idx]: row[idx] for idx in range(len(columns))}


def _validate_capsule_minimum(payload: dict[str, Any]) -> None:
    required_top = ("version", "trace", "signals", "artifacts")
    for key in required_top:
        if key not in payload:
            raise ValueError(f"missing capsule key: {key}")
    trace = payload.get("trace", {})
    for key in ("trace_id_hex", "span_id_hex", "backend", "run_id"):
        if key not in trace:
            raise ValueError(f"missing trace key: {key}")
    artifacts = payload.get("artifacts", [])
    if not isinstance(artifacts, list):
        raise ValueError("artifacts must be a list")


def _limit(value: int, default: int = 20, max_limit: int = 200) -> int:
    if value <= 0:
        return default
    return min(value, max_limit)


def query_priors(
    db_path: Path,
    scope: str,
    filters: dict[str, str] | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    filters = filters or {}
    limit = _limit(limit)
    allowed_scope = {"task", "run", "repo"}
    if scope not in allowed_scope:
        raise ValueError(f"invalid scope: {scope}")

    where = []
    params: list[Any] = []
    if filters.get("reason_code"):
        where.append("reason_code = ?")
        params.append(filters["reason_code"])
    if filters.get("task_status"):
        where.append("status = ?")
        params.append(filters["task_status"])

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    query = (
        "SELECT run_id, task_id, status, reason_code, attempts, duration_ms, "
        "worker_model, evidence_capsule_path, updated_ts "
        f"FROM task_fact {where_sql} "
        "ORDER BY updated_ts DESC, run_id ASC, task_id ASC "
        "LIMIT ?"
    )
    params.append(limit)

    conn = _connect(db_path)
    try:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        cols = [item[0] for item in cursor.description]
        return [_row_to_dict(cols, row) for row in rows]
    finally:
        conn.close()


def upsert_capsule(
    db_path: Path,
    capsule_payload: dict[str, Any],
    run_id: str,
    task_id: str,
    status: str,
    reason_code: str | None,
    schema_path: Path = CAPSULE_SCHEMA,
) -> dict[str, Any]:
    try:
        import jsonschema
    except Exception:
        _validate_capsule_minimum(capsule_payload)
    else:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.validate(capsule_payload, schema)

    conn = _connect(db_path)
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO task_fact (
              run_id, task_id, status, reason_code, attempts, duration_ms,
              worker_model, evidence_bundle_path, evidence_capsule_path, updated_ts
            )
            VALUES (?, ?, ?, ?, COALESCE((SELECT attempts FROM task_fact WHERE run_id = ? AND task_id = ?), 1),
                    COALESCE((SELECT duration_ms FROM task_fact WHERE run_id = ? AND task_id = ?), 0),
                    COALESCE((SELECT worker_model FROM task_fact WHERE run_id = ? AND task_id = ?), 'unknown'),
                    COALESCE((SELECT evidence_bundle_path FROM task_fact WHERE run_id = ? AND task_id = ?), ''),
                    ?, current_timestamp)
            """,
            [
                run_id,
                task_id,
                status,
                reason_code or "",
                run_id,
                task_id,
                run_id,
                task_id,
                run_id,
                task_id,
                run_id,
                task_id,
                f"memory://capsule/{run_id}/{task_id}",
            ],
        )
    finally:
        conn.close()
    return {"ok": True, "run_id": run_id, "task_id": task_id}


def get_run_summary(db_path: Path, run_id: str) -> dict[str, Any]:
    conn = _connect(db_path)
    try:
        run_cursor = conn.execute(
            """
            SELECT run_id, base_ref, gate_status, substrate_status, promotion_decision,
                   risk_score, confidence, repo_commit_sha, summary_path, state_space_path
            FROM run_fact
            WHERE run_id = ?
            """,
            [run_id],
        )
        run_row = run_cursor.fetchone()
        run_cols = [item[0] for item in run_cursor.description]
        run_fact = _row_to_dict(run_cols, run_row) if run_row else {}

        task_cursor = conn.execute(
            """
            SELECT run_id, task_id, status, reason_code, attempts, duration_ms, worker_model, evidence_capsule_path
            FROM task_fact
            WHERE run_id = ?
            ORDER BY task_id ASC
            """,
            [run_id],
        )
        task_rows = task_cursor.fetchall()
        task_cols = [item[0] for item in task_cursor.description]
        tasks = [_row_to_dict(task_cols, row) for row in task_rows]
        return {"run": run_fact, "tasks": tasks}
    finally:
        conn.close()


def health(checkpoint_path: Path = DEFAULT_CHECKPOINT) -> dict[str, Any]:
    if not checkpoint_path.exists():
        return {"daemon": "unknown", "checkpoint_exists": False, "processed_runs": 0}
    payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    processed = payload.get("processed_runs", [])
    return {
        "daemon": "ok",
        "checkpoint_exists": True,
        "processed_runs": len(processed) if isinstance(processed, list) else 0,
    }
