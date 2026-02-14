#!/usr/bin/env python
"""End-to-end MVP demo runner: planner -> implementers -> checker -> promotion -> state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Allow direct script execution: `python tools/orchestrator/run_demo.py ...`
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.checkers import create_gate_decision, persist_gate_decision
from tools.orchestrator.implementers import ImplementerHarness
from tools.orchestrator.mcp_loop import EventBus
from tools.orchestrator.planner import pre_contract_to_work_queue
from tools.orchestrator.promote import create_promotion_decision, persist_promotion_decision
from tools.orchestrator.state_writer import update_state_space


def run_demo(
    pre_contract_path: Path,
    run_root: Path,
    state_space_path: Path,
    reason_codes_path: Path,
    event_log: Path,
    risk_threshold: int = 60,
    max_retries: int = 1,
    otel_export: bool = False,
) -> dict[str, Any]:
    pre_contract = json.loads(pre_contract_path.read_text(encoding="utf-8"))
    work_queue = pre_contract_to_work_queue(pre_contract)

    run_id = work_queue["run_id"]
    run_dir = run_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "work.queue.json").write_text(json.dumps(work_queue, indent=2), encoding="utf-8")

    bus = EventBus(event_log=event_log)
    implementers = ImplementerHarness(bus=bus, run_root=run_root, max_retries=max_retries)
    run_summary = implementers.run(work_queue)

    reason_codes_payload = json.loads(reason_codes_path.read_text(encoding="utf-8"))
    reason_codes_catalog = {item["code"] for item in reason_codes_payload.get("codes", [])}
    gate_decision, trace_source = create_gate_decision(
        run_summary=run_summary,
        reason_codes_catalog=reason_codes_catalog,
        risk_threshold=risk_threshold,
        otel_export=otel_export,
    )
    gate_path = persist_gate_decision(run_root, run_id, gate_decision)

    promotion = create_promotion_decision(gate_decision=gate_decision, max_risk=risk_threshold)
    promotion_path = persist_promotion_decision(run_root, run_id, promotion)

    state_space = json.loads(state_space_path.read_text(encoding="utf-8"))
    updated_state = update_state_space(
        state_space=state_space,
        work_queue=work_queue,
        run_summary=run_summary,
        gate_decision=gate_decision,
        promotion_decision=promotion,
    )
    state_out_path = run_dir / "state.space.json"
    state_out_path.write_text(json.dumps(updated_state, indent=2), encoding="utf-8")

    return {
        "run_id": run_id,
        "trace_source": trace_source,
        "work_queue_path": str(run_dir / "work.queue.json"),
        "summary_path": str(run_dir / "summary.json"),
        "gate_decision_path": str(gate_path),
        "promotion_decision_path": str(promotion_path),
        "state_space_path": str(state_out_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run full dome MVP demo loop")
    parser.add_argument("--pre-contract", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=Path("ops/runtime/runs"))
    parser.add_argument("--state-space", type=Path, default=Path("ssot/examples/state.space.json"))
    parser.add_argument("--reason-codes", type=Path, default=Path("ssot/examples/reason.codes.json"))
    parser.add_argument("--event-log", type=Path, default=Path("ops/runtime/mcp_events.jsonl"))
    parser.add_argument("--risk-threshold", type=int, default=60)
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--otel-export", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_demo(
        pre_contract_path=args.pre_contract,
        run_root=args.run_root,
        state_space_path=args.state_space,
        reason_codes_path=args.reason_codes,
        event_log=args.event_log,
        risk_threshold=args.risk_threshold,
        max_retries=args.max_retries,
        otel_export=args.otel_export,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

