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

from tools.orchestrator.io_utils import atomic_write_json
from tools.orchestrator.mcp_loop import replay_task_result_events
from tools.orchestrator.security import assert_runtime_path
from tools.orchestrator.state_machine import apply_transition


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
        transitions = [apply_transition("QUEUED", "claim"), apply_transition("CLAIMED", "run")]
        transitions.append(apply_transition("RUNNING", "gate_pass" if approved else "gate_fail"))
        if approved:
            transitions.append(apply_transition("GATED", "gate_pass"))
        if not all(item.ok for item in transitions):
            first_fail = next(item for item in transitions if not item.ok)
            raise ValueError(f"illegal state transition for {task_id}: {first_fail.reason_code}")
        work_status = transitions[-1].next_state
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
                    "reason_code": reason_code or transitions[-1].reason_code,
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


def replay_state_space_from_events(
    state_space: dict[str, Any],
    work_queue: dict[str, Any],
    event_log: Path,
    run_id: str,
    gate_decision: dict[str, Any],
    promotion_decision: dict[str, Any],
) -> dict[str, Any]:
    events = replay_task_result_events(event_log=event_log, run_id=run_id)
    latest: dict[str, dict[str, Any]] = {}
    for event in events:
        if event.get("topic") != "task.result":
            continue
        payload = dict(event.get("payload", {}))
        task_id = str(payload.get("task_id", ""))
        if task_id:
            latest[task_id] = payload

    run_summary = {
        "run_id": run_id,
        "results": [
            {
                "task_id": task_id,
                "status": item.get("status"),
                "evidence_bundle_path": item.get("evidence_bundle_path"),
            }
            for task_id, item in latest.items()
        ],
    }
    return update_state_space(
        state_space=state_space,
        work_queue=work_queue,
        run_summary=run_summary,
        gate_decision=gate_decision,
        promotion_decision=promotion_decision,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update state.space from run artifacts")
    parser.add_argument("--run-root", type=Path, default=Path("ops/runtime/runs"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--state-space", type=Path, default=Path("ssot/examples/state.space.json"))
    parser.add_argument("--out", type=Path, default=Path("ops/runtime/state.space.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    assert_runtime_path(args.run_root, ROOT, "--run-root")
    assert_runtime_path(args.out, ROOT, "--out")
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
    atomic_write_json(args.out, updated)
    print(str(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
