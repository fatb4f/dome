#!/usr/bin/env python
"""Deterministic binder v1 for TaskSpec-aligned derived artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT / "ops/memory/memory.duckdb"
SCHEMA_PATH = ROOT / "tools/telemetry/memory_schema.sql"
BINDER_VERSION = "v1"


@dataclass(frozen=True)
class BinderRow:
    derived_upsert_key: str
    idempotency_key: str
    run_id: str
    task_id: str
    group_id: str
    scope: str
    target_kind: str
    target_id: str
    action_kind: str
    failure_reason_code: str
    policy_reason_code: str
    fingerprint_hash: str
    binder_version: str
    support_count: int
    contradiction_count: int
    last_seen_ts: str


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fingerprint_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _hash_parts(parts: list[str]) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _eligible(mode: str, status: str, failure_reason_code: str, policy_reason_code: str) -> bool:
    if mode == "lenient":
        return True
    # strict/hybrid: derive only from explicit failure/denial signals.
    return status == "FAIL" or bool(failure_reason_code) or bool(policy_reason_code)


def _derive_rows(conn: Any, mode: str) -> list[BinderRow]:
    rows = conn.execute(
        """
        SELECT
          run_id,
          task_id,
          status,
          COALESCE(failure_reason_code, reason_code, '') AS failure_reason_code,
          COALESCE(policy_reason_code, '') AS policy_reason_code,
          attempts,
          duration_ms,
          worker_model,
          COALESCE(CAST(updated_ts AS VARCHAR), '1970-01-01T00:00:00Z') AS updated_ts
        FROM task_fact
        ORDER BY updated_ts DESC, run_id ASC, task_id ASC
        """
    ).fetchall()
    out: list[BinderRow] = []
    for row in rows:
        run_id, task_id, status, failure_reason_code, policy_reason_code, attempts, duration_ms, worker_model, updated_ts = (
            str(row[0]),
            str(row[1]),
            str(row[2]),
            str(row[3]),
            str(row[4]),
            int(row[5]),
            int(row[6]),
            str(row[7]),
            str(row[8]),
        )
        if not _eligible(mode, status, failure_reason_code, policy_reason_code):
            continue

        group_id = task_id
        scope = "task"
        target_kind = "task"
        target_id = task_id
        action_kind = "fix" if status == "FAIL" else "validate"
        fp_hash = fingerprint_hash(
            {
                "status": status,
                "failure_reason_code": failure_reason_code,
                "policy_reason_code": policy_reason_code,
                "attempts": attempts,
                "duration_ms": duration_ms,
                "worker_model": worker_model,
            }
        )
        idempotency_key = _hash_parts([run_id, task_id, group_id, BINDER_VERSION])
        derived_upsert_key = _hash_parts(
            [
                scope,
                target_kind,
                target_id,
                action_kind,
                failure_reason_code,
                fp_hash,
                BINDER_VERSION,
            ]
        )
        out.append(
            BinderRow(
                derived_upsert_key=derived_upsert_key,
                idempotency_key=idempotency_key,
                run_id=run_id,
                task_id=task_id,
                group_id=group_id,
                scope=scope,
                target_kind=target_kind,
                target_id=target_id,
                action_kind=action_kind,
                failure_reason_code=failure_reason_code,
                policy_reason_code=policy_reason_code,
                fingerprint_hash=fp_hash,
                binder_version=BINDER_VERSION,
                support_count=1,
                contradiction_count=0,
                last_seen_ts=updated_ts,
            )
        )
    return out


def _upsert_rows(conn: Any, rows: list[BinderRow]) -> None:
    for row in rows:
        conn.execute(
            """
            INSERT OR REPLACE INTO binder_fact (
              derived_upsert_key, idempotency_key, run_id, task_id, group_id,
              scope, target_kind, target_id, action_kind, failure_reason_code,
              policy_reason_code, fingerprint_hash, binder_version,
              support_count, contradiction_count, last_seen_ts
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                row.derived_upsert_key,
                row.idempotency_key,
                row.run_id,
                row.task_id,
                row.group_id,
                row.scope,
                row.target_kind,
                row.target_id,
                row.action_kind,
                row.failure_reason_code,
                row.policy_reason_code,
                row.fingerprint_hash,
                row.binder_version,
                row.support_count,
                row.contradiction_count,
                row.last_seen_ts,
            ],
        )


def run_once(db_path: Path, schema_path: Path, mode: str) -> int:
    try:
        import duckdb  # type: ignore
    except Exception:
        raise SystemExit("duckdb is required for memory binder")

    conn = duckdb.connect(str(db_path))
    try:
        conn.execute(schema_path.read_text(encoding="utf-8"))
        rows = _derive_rows(conn, mode=mode)
        _upsert_rows(conn, rows)
    finally:
        conn.close()
    return len(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic binder derivations over task facts")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    parser.add_argument("--mode", choices=["strict", "hybrid", "lenient"], default="strict")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    count = run_once(db_path=args.db, schema_path=args.schema, mode=args.mode)
    print(json.dumps({"binder_version": BINDER_VERSION, "mode": args.mode, "derived_rows": count}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
