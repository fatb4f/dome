#!/usr/bin/env python
"""State-space writer using telemetry-backed evidence only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Allow direct script execution: `python tools/orchestrator/state_writer.py ...`
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_evidence_bundle(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    if "otel" not in payload or "signals" not in payload:
        raise ValueError(f"invalid telemetry evidence bundle: {path}")
    otel = payload["otel"]
    if "trace_id_hex" not in otel or "span_id_hex" not in otel:
        raise ValueError(f"missing trace reference in telemetry evidence bundle: {path}")
    return payload


def update_state_space(
    state_space: dict[str, Any],
    work_queue: dict[str, Any],
    run_summary: dict[str, Any],
    gate_decision: dict[str, Any],
    promotion_decision: dict[str, Any],
) -> dict[str, Any]:
    tasks_by_id = {task["task_id"]: task for task in work_queue.get("tasks", [])}
    new_items = []
    for result in run_summary.get("results", []):
        task_id = result["task_id"]
        task = tasks_by_id.get(task_id, {"dependencies": []})
        evidence_path = Path(str(result.get("evidence_bundle_path", "")))
        if not evidence_path.exists():
            raise ValueError(f"missing evidence bundle path for task {task_id}")
        evidence = _validate_evidence_bundle(evidence_path)
        approved = promotion_decision.get("decision") == "APPROVE" and result.get("status") == "PASS"
        work_status = "DONE" if approved else "BLOCKED"
        gate_status = "DONE" if approved else "BLOCKED"
        reason_code = None
        if not approved:
            reason_codes = list(promotion_decision.get("reason_codes", []))
            reason_code = reason_codes[0] if reason_codes else "POLICY.NEEDS_HUMAN"

        new_items.append(
            {
                "work_id": task_id,
                "status": work_status,
                "node": {
                    "reqs": [],
                    "deps": list(task.get("dependencies", [])),
                    "provs": ["telemetry"],
                    "assert": ["gate_passes"],
                },
                "telemetry": evidence,
                "gate": {
                    "status": gate_status,
                    "reason_code": reason_code,
                    "notes": "; ".join(gate_decision.get("notes", [])) if gate_decision.get("notes") else None,
                },
            }
        )

    out = dict(state_space)
    out.setdefault("version", "0.2.0")
    out.setdefault("memory", [])
    out.setdefault("task_preferences", {"telemetry_is_ssot": True})
    out["work_items"] = new_items
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update state.space from run artifacts")
    parser.add_argument("--run-root", type=Path, default=Path("ops/runtime/runs"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--state-space", type=Path, default=Path("ssot/examples/state.space.json"))
    parser.add_argument("--out", type=Path, default=Path("ops/runtime/state.space.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state_space = _load_json(args.state_space)
    work_queue = _load_json(args.run_root / args.run_id / "work.queue.json")
    run_summary = _load_json(args.run_root / args.run_id / "summary.json")
    gate_decision = _load_json(args.run_root / args.run_id / "gate" / "gate.decision.json")
    promotion_decision = _load_json(args.run_root / args.run_id / "promotion" / "promotion.decision.json")
    updated = update_state_space(
        state_space=state_space,
        work_queue=work_queue,
        run_summary=run_summary,
        gate_decision=gate_decision,
        promotion_decision=promotion_decision,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(updated, indent=2), encoding="utf-8")
    print(str(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

