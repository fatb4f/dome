#!/usr/bin/env python
"""Checkpointed long-horizon memory materialization daemon."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT / "ops/memory/memory.duckdb"
DEFAULT_RUN_ROOT = ROOT / "ops/runtime/runs"
DEFAULT_CHECKPOINT = ROOT / "ops/memory/checkpoints/materialize.state.json"
SCHEMA_PATH = ROOT / "tools/telemetry/memory_schema.sql"


@dataclass(frozen=True)
class RunSnapshot:
    run_id: str
    base_ref: str
    gate_status: str
    substrate_status: str
    promotion_decision: str
    risk_score: int
    confidence: float
    repo_commit_sha: str
    summary_path: str
    state_space_path: str


@dataclass(frozen=True)
class TaskSnapshot:
    run_id: str
    task_id: str
    status: str
    failure_reason_code: str
    policy_reason_code: str
    attempts: int
    duration_ms: int
    worker_model: str
    evidence_bundle_path: str
    evidence_capsule_path: str
    updated_ts: str


@dataclass(frozen=True)
class EventSnapshot:
    run_id: str
    event_id: str
    topic: str
    sequence: int
    ts: str
    payload_json: str


def load_checkpoint(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"processed_runs": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload.get("processed_runs"), list):
        payload["processed_runs"] = []
    return payload


def save_checkpoint(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def discover_runs(run_root: Path) -> list[str]:
    if not run_root.exists():
        return []
    return sorted(path.name for path in run_root.iterdir() if path.is_dir())


def pending_runs(discovered: list[str], processed: list[str]) -> list[str]:
    processed_set = set(processed)
    return [run_id for run_id in discovered if run_id not in processed_set]


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _deterministic_ts(path: Path) -> str:
    if path.exists():
        return datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat().replace("+00:00", "Z")
    return "1970-01-01T00:00:00Z"


def _event_log_paths(run_dir: Path, run_root: Path) -> list[Path]:
    paths = [
        run_dir / "mcp_events.jsonl",
        run_root.parent / "mcp_events.jsonl",
    ]
    out: list[Path] = []
    for item in paths:
        if item.exists() and item not in out:
            out.append(item)
    return out


def _load_event_rows(run_dir: Path, run_root: Path, run_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in _event_log_paths(run_dir, run_root):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if str(payload.get("run_id", "")) != run_id:
                continue
            rows.append(payload)
    rows.sort(
        key=lambda item: (
            int(item.get("sequence", 0)),
            str(item.get("ts", "")),
            str(item.get("event_id", "")),
        )
    )
    return rows


def _task_updated_ts(
    task_result: dict[str, Any], run_dir: Path, event_rows: list[dict[str, Any]]
) -> str:
    task_id = str(task_result.get("task_id", ""))
    candidates = [
        row
        for row in event_rows
        if str(row.get("topic", "")) == "task.result" and str(row.get("payload", {}).get("task_id", "")) == task_id
    ]
    if candidates:
        return str(candidates[-1].get("ts", "1970-01-01T00:00:00Z"))
    result_path = run_dir / "summary.json"
    return _deterministic_ts(result_path)


def task_snapshots_from_run_dir(run_dir: Path, run_root: Path) -> list[TaskSnapshot]:
    run_id = run_dir.name
    summary = _load_json(run_dir / "summary.json")
    event_rows = _load_event_rows(run_dir, run_root, run_id)
    out: list[TaskSnapshot] = []
    for item in summary.get("results", []):
        task_id = str(item.get("task_id", ""))
        if not task_id:
            continue
        raw_reason = item.get("reason_code")
        failure_reason = "" if raw_reason is None else str(raw_reason)
        evidence_bundle = str(item.get("evidence_bundle_path", ""))
        out.append(
            TaskSnapshot(
                run_id=run_id,
                task_id=task_id,
                status=str(item.get("status", "UNKNOWN")),
                failure_reason_code=failure_reason,
                policy_reason_code="",
                attempts=int(item.get("attempts", 0)),
                duration_ms=int(item.get("duration_ms", 0)),
                worker_model=str(item.get("worker_model", "unknown")),
                evidence_bundle_path=evidence_bundle,
                evidence_capsule_path="",
                updated_ts=_task_updated_ts(item, run_dir, event_rows),
            )
        )
    return sorted(out, key=lambda item: item.task_id)


def event_snapshots_from_run_dir(run_dir: Path, run_root: Path) -> list[EventSnapshot]:
    run_id = run_dir.name
    rows = _load_event_rows(run_dir, run_root, run_id)
    out: list[EventSnapshot] = []
    for row in rows:
        event_id = str(row.get("event_id", ""))
        if not event_id:
            continue
        out.append(
            EventSnapshot(
                run_id=run_id,
                event_id=event_id,
                topic=str(row.get("topic", "")),
                sequence=int(row.get("sequence", 0)),
                ts=str(row.get("ts", "1970-01-01T00:00:00Z")),
                payload_json=json.dumps(row.get("payload", {}), sort_keys=True),
            )
        )
    return out


def snapshot_from_run_dir(run_dir: Path) -> RunSnapshot:
    run_id = run_dir.name
    summary_path = run_dir / "summary.json"
    gate_path = run_dir / "gate/gate.decision.json"
    promotion_path = run_dir / "promotion/promotion.decision.json"
    manifest_path = run_dir / "run.manifest.json"
    state_space_path = run_dir / "state.space.json"
    work_queue_path = run_dir / "work.queue.json"

    gate = _load_json(gate_path)
    promotion = _load_json(promotion_path)
    manifest = _load_json(manifest_path)
    work_queue = _load_json(work_queue_path)

    return RunSnapshot(
        run_id=run_id,
        base_ref=str(work_queue.get("base_ref", "unknown")),
        gate_status=str(gate.get("status", "UNKNOWN")),
        substrate_status=str(gate.get("substrate_status", "UNKNOWN")),
        promotion_decision=str(promotion.get("decision", "UNKNOWN")),
        risk_score=int(gate.get("risk_score", 0)),
        confidence=float(gate.get("confidence", 0.0)),
        repo_commit_sha=str(manifest.get("runtime", {}).get("repo_commit_sha", "unknown")),
        summary_path=str(summary_path),
        state_space_path=str(state_space_path),
    )


def apply_schema(conn: Any, schema_path: Path) -> None:
    conn.execute(schema_path.read_text(encoding="utf-8"))


def upsert_run_fact(conn: Any, snapshot: RunSnapshot) -> None:
    now_expr = "current_timestamp"
    conn.execute(
        f"""
        INSERT OR REPLACE INTO run_fact (
          run_id, first_seen_ts, last_seen_ts, base_ref, gate_status, substrate_status,
          promotion_decision, risk_score, confidence, repo_commit_sha, summary_path, state_space_path
        )
        VALUES (?, {now_expr}, {now_expr}, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            snapshot.run_id,
            snapshot.base_ref,
            snapshot.gate_status,
            snapshot.substrate_status,
            snapshot.promotion_decision,
            snapshot.risk_score,
            snapshot.confidence,
            snapshot.repo_commit_sha,
            snapshot.summary_path,
            snapshot.state_space_path,
        ],
    )


def upsert_task_fact(conn: Any, snapshot: TaskSnapshot) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO task_fact (
          run_id, task_id, status, failure_reason_code, policy_reason_code, reason_code,
          attempts, duration_ms, worker_model, evidence_bundle_path, evidence_capsule_path, updated_ts
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            snapshot.run_id,
            snapshot.task_id,
            snapshot.status,
            snapshot.failure_reason_code,
            snapshot.policy_reason_code,
            snapshot.failure_reason_code,
            snapshot.attempts,
            snapshot.duration_ms,
            snapshot.worker_model,
            snapshot.evidence_bundle_path,
            snapshot.evidence_capsule_path,
            snapshot.updated_ts,
        ],
    )


def upsert_event_fact(conn: Any, snapshot: EventSnapshot) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO event_fact (
          run_id, event_id, topic, sequence, ts, payload_json
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            snapshot.run_id,
            snapshot.event_id,
            snapshot.topic,
            snapshot.sequence,
            snapshot.ts,
            snapshot.payload_json,
        ],
    )


def run_once(db_path: Path, run_root: Path, checkpoint_path: Path, schema_path: Path) -> int:
    checkpoint = load_checkpoint(checkpoint_path)
    discovered = discover_runs(run_root)
    todo = pending_runs(discovered, checkpoint.get("processed_runs", []))
    if not todo:
        return 0

    try:
        import duckdb  # type: ignore
    except Exception:
        raise SystemExit("duckdb is required for memoryd materialization")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path))
    try:
        apply_schema(conn, schema_path)
        for run_id in todo:
            run_dir = run_root / run_id
            snapshot = snapshot_from_run_dir(run_dir)
            upsert_run_fact(conn, snapshot)
            for task_snapshot in task_snapshots_from_run_dir(run_dir, run_root):
                upsert_task_fact(conn, task_snapshot)
            for event_snapshot in event_snapshots_from_run_dir(run_dir, run_root):
                upsert_event_fact(conn, event_snapshot)
            checkpoint["processed_runs"].append(run_id)
        checkpoint["processed_runs"] = sorted(set(str(item) for item in checkpoint["processed_runs"]))
        save_checkpoint(checkpoint_path, checkpoint)
    finally:
        conn.close()
    return len(todo)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize long-horizon run memory into DuckDB")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    parser.add_argument("--poll-seconds", type=int, default=10)
    parser.add_argument("--once", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.once:
        processed = run_once(args.db, args.run_root, args.checkpoint, args.schema)
        print(json.dumps({"mode": "once", "processed_runs": processed}, sort_keys=True))
        return 0

    while True:
        processed = run_once(args.db, args.run_root, args.checkpoint, args.schema)
        print(json.dumps({"mode": "loop", "processed_runs": processed}, sort_keys=True))
        time.sleep(max(1, int(args.poll_seconds)))


if __name__ == "__main__":
    raise SystemExit(main())
