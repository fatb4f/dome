#!/usr/bin/env python
"""End-to-end MVP demo runner: planner -> implementers -> checker -> promotion -> state."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

# Allow direct script execution: `python tools/orchestrator/run_demo.py ...`
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.checkers import (
    create_gate_decision,
    persist_gate_decision,
    validate_gate_decision_schema,
)
from tools.orchestrator.implementers import ImplementerHarness
from tools.orchestrator.io_utils import atomic_write_json
from tools.orchestrator.mcp_loop import EventBus
from tools.orchestrator.mcp_loop import load_control_events, materialize_control_ledger
from tools.orchestrator.planner import pre_contract_to_work_queue
from tools.orchestrator.promote import (
    create_promotion_decision,
    persist_promotion_decision,
    validate_promotion_schema,
)
from tools.orchestrator.runtime_config import load_runtime_profile
from tools.orchestrator.security import assert_runtime_path
from tools.orchestrator.substrate_layout import ensure_substrate_layout
from tools.orchestrator.otel_stage import stage_span
from tools.orchestrator.state_writer import update_state_space


def _verify_command_from_pre_contract(pre_contract: dict[str, Any]) -> str | None:
    actions = pre_contract.get("actions", {})
    test_action = actions.get("test")
    if isinstance(test_action, list) and test_action:
        return " ".join(shlex.quote(str(part)) for part in test_action)
    if isinstance(test_action, str) and test_action.strip():
        return test_action.strip()
    return None


def _sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_commit_sha() -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return proc.stdout.strip()
    except Exception:
        return "unknown"


def _tool_versions() -> dict[str, str]:
    out = {"python": sys.version.split(" ")[0]}
    for package in ("pytest", "jsonschema"):
        try:
            out[package] = importlib.metadata.version(package)
        except Exception:
            out[package] = "unavailable"
    return out


def run_demo(
    pre_contract_path: Path,
    run_root: Path,
    state_space_path: Path,
    reason_codes_path: Path,
    event_log: Path,
    risk_threshold: int = 60,
    max_retries: int = 1,
    worker_models: list[str] | None = None,
    otel_export: bool = False,
    runtime_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pre_contract = json.loads(pre_contract_path.read_text(encoding="utf-8"))
    with stage_span(
        "dome.planner.translate",
        {
            "packet.id": str(pre_contract.get("packet_id", "unknown")),
            "base.ref": str(pre_contract.get("base_ref", "main")),
        },
        enabled=otel_export,
    ):
        work_queue = pre_contract_to_work_queue(pre_contract)
    verify_command = _verify_command_from_pre_contract(pre_contract)

    run_id = work_queue["run_id"]
    run_dir = run_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    ensure_substrate_layout(run_root, run_id)
    atomic_write_json(run_dir / "work.queue.json", work_queue)

    bus = EventBus(event_log=event_log)
    implementers = ImplementerHarness(
        bus=bus,
        run_root=run_root,
        max_retries=max_retries,
        worker_models=worker_models,
    )
    with stage_span(
        "dome.implementers.run",
        {
            "run.id": run_id,
            "task.count": len(work_queue.get("tasks", [])),
            "max.workers": int(work_queue.get("max_workers", 1)),
        },
        enabled=otel_export,
    ):
        run_summary = implementers.run(work_queue)

    reason_codes_payload = json.loads(reason_codes_path.read_text(encoding="utf-8"))
    reason_codes_catalog = {item["code"] for item in reason_codes_payload.get("codes", [])}
    with stage_span(
        "dome.gate.evaluate",
        {
            "run.id": run_id,
            "risk.threshold": risk_threshold,
        },
        enabled=otel_export,
    ):
        gate_decision, trace_source = create_gate_decision(
            run_summary=run_summary,
            reason_codes_catalog=reason_codes_catalog,
            verify_command=verify_command,
            risk_threshold=risk_threshold,
            otel_export=otel_export,
        )
    validate_gate_decision_schema(gate_decision, ROOT / "ssot/schemas/gate.decision.schema.json")
    gate_path = persist_gate_decision(run_root, run_id, gate_decision)

    with stage_span(
        "dome.promote.decide",
        {
            "run.id": run_id,
            "gate.status": str(gate_decision.get("status", "")),
            "max.risk": risk_threshold,
        },
        enabled=otel_export,
    ):
        promotion = create_promotion_decision(gate_decision=gate_decision, max_risk=risk_threshold)
    validate_promotion_schema(promotion, ROOT / "ssot/schemas/promotion.decision.schema.json")
    promotion_path = persist_promotion_decision(run_root, run_id, promotion)
    control_events = load_control_events(event_log=event_log, run_id=run_id)
    control_ledger = materialize_control_ledger(control_events)
    control_ledger_path = run_dir / "control.ledger.json"
    atomic_write_json(control_ledger_path, control_ledger)

    state_space = json.loads(state_space_path.read_text(encoding="utf-8"))
    with stage_span(
        "dome.state.write",
        {
            "run.id": run_id,
            "work.items": len(work_queue.get("tasks", [])),
        },
        enabled=otel_export,
    ):
        updated_state = update_state_space(
            state_space=state_space,
            work_queue=work_queue,
            run_summary=run_summary,
            gate_decision=gate_decision,
            promotion_decision=promotion,
        )
    state_out_path = run_dir / "state.space.json"
    atomic_write_json(state_out_path, updated_state)

    input_hashes = {
        "pre_contract_sha256": _sha256_path(pre_contract_path),
        "state_space_sha256": _sha256_path(state_space_path),
        "reason_codes_sha256": _sha256_path(reason_codes_path),
        "work_queue_sha256": _sha256_path(run_dir / "work.queue.json"),
    }

    manifest = {
        "version": "0.2.0",
        "run_id": run_id,
        "inputs": {
            "pre_contract_path": str(pre_contract_path),
            "pre_contract_sha256": input_hashes["pre_contract_sha256"],
            "input_hashes": input_hashes,
        },
        "commands": ["planner", "implementers", "checkers", "promote", "state_writer"],
        "refs": {
            "policy_ref": "ssot/policy/reason.codes.json",
            "pattern_ref": (runtime_profile or {}).get("pattern_catalog_ref"),
            "packet_contract_ref": str(pre_contract_path),
        },
        "budgets": {
            "time_minutes": int(pre_contract.get("budgets", {}).get("time_minutes", 30)),
            "iteration_budget": int(pre_contract.get("budgets", {}).get("iteration_budget", 1)),
        },
        "desired_state": {
            "gate": gate_decision.get("substrate_status"),
        },
        "artifacts": {
            "work_queue_path": str(run_dir / "work.queue.json"),
            "summary_path": str(run_dir / "summary.json"),
            "gate_decision_path": str(gate_path),
            "promotion_decision_path": str(promotion_path),
            "control_ledger_path": str(control_ledger_path),
            "state_space_path": str(state_out_path),
        },
        "runtime": {
            "repo_commit_sha": _git_commit_sha(),
            "tool_versions": _tool_versions(),
            "environment_fingerprint": {
                "platform": platform.platform(),
                "python_implementation": platform.python_implementation(),
                "cwd": os.getcwd(),
            },
            "trace_source": trace_source,
            "runtime_profile": (runtime_profile or {}).get("name"),
            "runtime_pattern": (runtime_profile or {}).get("pattern"),
            "max_retries": max_retries,
            "risk_threshold": risk_threshold,
            "worker_models": worker_models or ["gpt-5.3", "gpt-5.2"],
        },
    }
    manifest_path = run_dir / "run.manifest.json"
    atomic_write_json(manifest_path, manifest)

    return {
        "run_id": run_id,
        "trace_source": trace_source,
        "work_queue_path": str(run_dir / "work.queue.json"),
        "summary_path": str(run_dir / "summary.json"),
        "gate_decision_path": str(gate_path),
        "promotion_decision_path": str(promotion_path),
        "state_space_path": str(state_out_path),
        "run_manifest_path": str(manifest_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run full dome MVP demo loop")
    parser.add_argument("--pre-contract", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=Path("ops/runtime/runs"))
    parser.add_argument("--state-space", type=Path, default=Path("ssot/examples/state.space.json"))
    parser.add_argument("--reason-codes", type=Path, default=Path("ssot/policy/reason.codes.json"))
    parser.add_argument("--event-log", type=Path, default=Path("ops/runtime/mcp_events.jsonl"))
    parser.add_argument("--runtime-config", type=Path)
    parser.add_argument("--profile")
    parser.add_argument("--worker-models")
    parser.add_argument("--risk-threshold", type=int)
    parser.add_argument("--max-retries", type=int)
    parser.add_argument("--otel-export", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    assert_runtime_path(args.run_root, ROOT, "--run-root")
    assert_runtime_path(args.event_log, ROOT, "--event-log")
    runtime_profile = load_runtime_profile(
        runtime_config_path=args.runtime_config,
        profile=args.profile,
        schema_path=ROOT / "ssot/schemas/runtime.config.schema.json",
    )
    models_cfg = runtime_profile.get("models", {}).get("implementers", [])
    worker_models = (
        [item.strip() for item in args.worker_models.split(",") if item.strip()]
        if isinstance(args.worker_models, str) and args.worker_models.strip()
        else list(models_cfg)
    )
    if not worker_models:
        worker_models = ["gpt-5.3", "gpt-5.2"]
    budget_cfg = runtime_profile.get("budgets", {})
    risk_threshold = int(args.risk_threshold) if args.risk_threshold is not None else int(budget_cfg.get("risk_threshold", 60))
    max_retries = int(args.max_retries) if args.max_retries is not None else int(budget_cfg.get("max_retries", 1))

    summary = run_demo(
        pre_contract_path=args.pre_contract,
        run_root=args.run_root,
        state_space_path=args.state_space,
        reason_codes_path=args.reason_codes,
        event_log=args.event_log,
        risk_threshold=risk_threshold,
        max_retries=max_retries,
        worker_models=worker_models,
        otel_export=args.otel_export,
        runtime_profile=runtime_profile,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
