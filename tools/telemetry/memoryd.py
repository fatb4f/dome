#!/usr/bin/env python
"""Checkpointed long-horizon memory materialization daemon."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
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
            snapshot = snapshot_from_run_dir(run_root / run_id)
            upsert_run_fact(conn, snapshot)
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

