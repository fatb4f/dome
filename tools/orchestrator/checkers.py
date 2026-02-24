#!/usr/bin/env python
"""Phase 3 checker/gate harness with optional OTel provenance emission."""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

# Allow direct script execution: `python tools/orchestrator/checkers.py ...`
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.io_utils import atomic_write_json
from tools.orchestrator.mcp_loop import Event, EventBus, TOPIC_GATE_REQUESTED, TOPIC_GATE_VERDICT
from tools.orchestrator.security import assert_runtime_path
from tools.orchestrator.xa_mapping import dome_to_substrate


def _deterministic_trace_ref(run_id: str) -> dict[str, str]:
    digest = hashlib.sha256(run_id.encode("utf-8")).hexdigest()
    return {"trace_id_hex": digest[:32], "span_id_hex": digest[32:48]}


def _otel_trace_ref(run_id: str, enabled: bool) -> tuple[dict[str, str], str]:
    if not enabled:
        return _deterministic_trace_ref(run_id), "disabled"
    try:
        from opentelemetry import trace  # type: ignore
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore
    except Exception:
        return _deterministic_trace_ref(run_id), "missing_opentelemetry"

    provider = trace.get_tracer_provider()
    if provider.__class__.__name__ != "TracerProvider":
        try:
            trace.set_tracer_provider(TracerProvider())
        except Exception:
            pass

    tracer = trace.get_tracer("dome.checkers")
    with tracer.start_as_current_span("checker.gate") as span:
        span.set_attribute("dome.run_id", run_id)
        ctx = span.get_span_context()
        if not ctx.is_valid:
            return _deterministic_trace_ref(run_id), "otel_invalid_context"
        return {
            "trace_id_hex": f"{ctx.trace_id:032x}",
            "span_id_hex": f"{ctx.span_id:016x}",
        }, "otel"


def _load_reason_codes(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    codes = {item["code"] for item in payload.get("codes", []) if "code" in item}
    if not codes:
        raise ValueError("reason code catalog is empty")
    return codes


def _run_verify_command(command: str | None, cwd: Path | None = None) -> tuple[int, str]:
    if not command:
        return 0, "verify skipped"
    argv = shlex.split(command)
    proc = subprocess.run(argv, capture_output=True, text=True, cwd=str(cwd) if cwd else None)
    output = "\n".join(filter(None, [proc.stdout.strip(), proc.stderr.strip()]))
    return int(proc.returncode), output[:4000]


def _compute_status(
    summary: dict[str, Any],
    verify_rc: int,
    risk_threshold: int,
) -> tuple[str, list[str], float, int, list[str]]:
    results = summary.get("results", [])
    if verify_rc != 0:
        return "REJECT", ["VERIFY.TEST_FAILURE"], 0.98, 95, ["deterministic verify command failed"]

    if any(result.get("status") != "PASS" for result in results):
        return "REJECT", ["EXEC.NONZERO_EXIT"], 0.95, 85, ["implementer task failed"]

    hinted_risk = 0
    for result in results:
        hinted_risk = max(hinted_risk, int(result.get("risk_score_hint", 20)))
    if hinted_risk >= risk_threshold:
        return "NEEDS_HUMAN", ["POLICY.NEEDS_HUMAN"], 0.7, hinted_risk, ["risk threshold exceeded"]

    return "APPROVE", [], 0.9, max(20, hinted_risk), ["all deterministic checks passed"]


def create_gate_decision(
    run_summary: dict[str, Any],
    reason_codes_catalog: set[str],
    verify_command: str | None = None,
    verify_cwd: Path | None = None,
    risk_threshold: int = 60,
    otel_export: bool = False,
) -> tuple[dict[str, Any], str]:
    run_id = str(run_summary.get("run_id", "run-unknown"))
    verify_rc, verify_output = _run_verify_command(verify_command, cwd=verify_cwd)
    status, reason_codes, confidence, risk_score, notes = _compute_status(
        summary=run_summary,
        verify_rc=verify_rc,
        risk_threshold=risk_threshold,
    )
    for code in reason_codes:
        if code not in reason_codes_catalog:
            raise ValueError(f"reason code not in catalog: {code}")
    telemetry_ref, trace_source = _otel_trace_ref(run_id=run_id, enabled=otel_export)
    notes = list(notes)
    notes.append(f"trace_source={trace_source}")
    if verify_command:
        notes.append(f"verify_rc={verify_rc}")
        if verify_output:
            notes.append(f"verify_output={verify_output}")
    decision = {
        "version": "0.2.0",
        "run_id": run_id,
        "task_id": "wave-gate",
        "status": status,
        "substrate_status": dome_to_substrate(status),
        "reason_codes": reason_codes,
        "confidence": confidence,
        "risk_score": int(risk_score),
        "notes": notes,
        "telemetry_ref": telemetry_ref,
    }
    return decision, trace_source


def persist_gate_decision(run_root: Path, run_id: str, decision: dict[str, Any]) -> Path:
    gate_dir = run_root / run_id / "gate"
    gate_dir.mkdir(parents=True, exist_ok=True)
    out_path = gate_dir / "gate.decision.json"
    atomic_write_json(out_path, decision)
    return out_path


def validate_gate_decision_schema(decision: dict[str, Any], schema_path: Path) -> None:
    try:
        import jsonschema  # type: ignore
    except Exception:
        # Local/dev fallback: CI installs jsonschema and enforces this check.
        return
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=decision, schema=schema)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate run summary and emit gate.decision")
    parser.add_argument("--run-root", type=Path, default=Path("ops/runtime/runs"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--reason-codes", type=Path, default=Path("ssot/policy/reason.codes.json"))
    parser.add_argument("--event-log", type=Path, default=Path("ops/runtime/mcp_events.jsonl"))
    parser.add_argument("--schema", type=Path, default=Path("ssot/schemas/gate.decision.schema.json"))
    parser.add_argument("--verify-command", default="")
    parser.add_argument("--verify-cwd", type=Path)
    parser.add_argument("--risk-threshold", type=int, default=60)
    parser.add_argument("--otel-export", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    assert_runtime_path(args.run_root, ROOT, "--run-root")
    assert_runtime_path(args.event_log, ROOT, "--event-log")
    run_summary_path = args.run_root / args.run_id / "summary.json"
    run_summary = json.loads(run_summary_path.read_text(encoding="utf-8"))
    reason_codes_catalog = _load_reason_codes(args.reason_codes)

    bus = EventBus(event_log=args.event_log)
    bus.publish(
        Event(
            topic=TOPIC_GATE_REQUESTED,
            run_id=args.run_id,
            payload={"run_summary_path": str(run_summary_path)},
        )
    )
    decision, _ = create_gate_decision(
        run_summary=run_summary,
        reason_codes_catalog=reason_codes_catalog,
        verify_command=args.verify_command or None,
        verify_cwd=args.verify_cwd,
        risk_threshold=args.risk_threshold,
        otel_export=args.otel_export,
    )
    validate_gate_decision_schema(decision, args.schema)
    out_path = persist_gate_decision(args.run_root, args.run_id, decision)
    bus.publish(
        Event(
            topic=TOPIC_GATE_VERDICT,
            run_id=args.run_id,
            payload={**decision, "gate_decision_path": str(out_path)},
        )
    )
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
