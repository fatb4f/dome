#!/usr/bin/env python
"""Promotion decision policy for Phase 4."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Allow direct script execution: `python tools/orchestrator/promote.py ...`
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.mcp_loop import Event, EventBus, TOPIC_PROMOTION_DECISION


def create_promotion_decision(
    gate_decision: dict[str, Any],
    min_confidence: float = 0.7,
    max_risk: int = 60,
) -> dict[str, Any]:
    status = str(gate_decision.get("status", "REJECT"))
    confidence = float(gate_decision.get("confidence", 0.0))
    risk = int(gate_decision.get("risk_score", 100))
    reason_codes = list(gate_decision.get("reason_codes", []))
    notes = list(gate_decision.get("notes", []))

    if status == "REJECT":
        decision = "REJECT"
    elif status == "NEEDS_HUMAN":
        decision = "NEEDS_HUMAN"
        if "POLICY.NEEDS_HUMAN" not in reason_codes:
            reason_codes.append("POLICY.NEEDS_HUMAN")
    elif confidence < min_confidence or risk > max_risk:
        decision = "NEEDS_HUMAN"
        if "POLICY.NEEDS_HUMAN" not in reason_codes:
            reason_codes.append("POLICY.NEEDS_HUMAN")
    else:
        decision = "APPROVE"

    return {
        "version": "0.2.0",
        "run_id": str(gate_decision.get("run_id", "run-unknown")),
        "decision": decision,
        "reason_codes": reason_codes,
        "confidence": confidence,
        "risk_score": risk,
        "notes": notes,
        "gate_decision_ref": {
            "task_id": str(gate_decision.get("task_id", "wave-gate")),
            "telemetry_ref": gate_decision.get("telemetry_ref", {}),
        },
    }


def persist_promotion_decision(run_root: Path, run_id: str, payload: dict[str, Any]) -> Path:
    out_dir = run_root / run_id / "promotion"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "promotion.decision.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def append_promotion_audit(run_root: Path, run_id: str, payload: dict[str, Any]) -> Path:
    audit_path = run_root / "promotion_audit.jsonl"
    row = {
        "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "run_id": run_id,
        "decision": payload.get("decision"),
        "reason_codes": payload.get("reason_codes", []),
        "confidence": payload.get("confidence"),
        "risk_score": payload.get("risk_score"),
        "telemetry_ref": payload.get("gate_decision_ref", {}).get("telemetry_ref", {}),
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True))
        fh.write("\n")
    return audit_path


def validate_promotion_schema(payload: dict[str, Any], schema_path: Path) -> None:
    try:
        import jsonschema  # type: ignore
    except Exception:
        # Local/dev fallback: CI installs jsonschema and enforces this check.
        return
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=payload, schema=schema)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply promotion policy from gate decision")
    parser.add_argument("--run-root", type=Path, default=Path("ops/runtime/runs"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--event-log", type=Path, default=Path("ops/runtime/mcp_events.jsonl"))
    parser.add_argument("--schema", type=Path, default=Path("ssot/schemas/promotion.decision.schema.json"))
    parser.add_argument("--min-confidence", type=float, default=0.7)
    parser.add_argument("--max-risk", type=int, default=60)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    gate_path = args.run_root / args.run_id / "gate" / "gate.decision.json"
    gate_decision = json.loads(gate_path.read_text(encoding="utf-8"))
    promotion = create_promotion_decision(
        gate_decision=gate_decision,
        min_confidence=args.min_confidence,
        max_risk=args.max_risk,
    )
    validate_promotion_schema(promotion, args.schema)
    out_path = persist_promotion_decision(args.run_root, args.run_id, promotion)
    audit_path = append_promotion_audit(args.run_root, args.run_id, promotion)
    bus = EventBus(event_log=args.event_log)
    bus.publish(
        Event(
            topic=TOPIC_PROMOTION_DECISION,
            run_id=args.run_id,
            payload={
                **promotion,
                "promotion_decision_path": str(out_path),
                "promotion_audit_path": str(audit_path),
            },
        )
    )
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
