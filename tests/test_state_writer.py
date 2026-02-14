import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.state_writer import update_state_space


def _state() -> dict:
    return {
        "version": "0.2.0",
        "memory": [],
        "task_preferences": {"telemetry_is_ssot": True},
        "work_items": [],
    }


def _work_queue() -> dict:
    return {
        "version": "0.2.0",
        "run_id": "wave-state-001",
        "base_ref": "main",
        "max_workers": 1,
        "tasks": [{"task_id": "t1", "goal": "a", "status": "QUEUED", "dependencies": []}],
    }


def _gate() -> dict:
    return {
        "version": "0.2.0",
        "run_id": "wave-state-001",
        "task_id": "wave-gate",
        "status": "APPROVE",
        "reason_codes": [],
        "confidence": 0.9,
        "risk_score": 20,
        "notes": ["ok"],
        "telemetry_ref": {"trace_id_hex": "0" * 32, "span_id_hex": "0" * 16},
    }


def _promo(decision: str = "APPROVE") -> dict:
    return {
        "version": "0.2.0",
        "run_id": "wave-state-001",
        "decision": decision,
        "reason_codes": [],
        "confidence": 0.9,
        "risk_score": 20,
        "notes": [],
        "gate_decision_ref": {"task_id": "wave-gate", "telemetry_ref": {"trace_id_hex": "0" * 32, "span_id_hex": "0" * 16}},
    }


def test_state_writer_requires_telemetry_evidence(tmp_path: Path) -> None:
    run_summary = {
        "run_id": "wave-state-001",
        "results": [{"task_id": "t1", "status": "PASS", "evidence_bundle_path": str(tmp_path / "missing.json")}],
    }
    with pytest.raises(ValueError, match="missing evidence bundle"):
        update_state_space(_state(), _work_queue(), run_summary, _gate(), _promo())


def test_state_writer_updates_done_from_approved_decision(tmp_path: Path) -> None:
    evidence_path = tmp_path / "t1.evidence.bundle.telemetry.json"
    evidence_path.write_text(
        json.dumps(
            {
                "otel": {"trace_id_hex": "0" * 32, "span_id_hex": "0" * 16, "backend": "local", "project": "dome", "run_id": "wave-state-001"},
                "signals": {"task.status": "PASS"},
                "artifacts": [],
            }
        ),
        encoding="utf-8",
    )
    run_summary = {
        "run_id": "wave-state-001",
        "results": [{"task_id": "t1", "status": "PASS", "evidence_bundle_path": str(evidence_path)}],
    }
    updated = update_state_space(_state(), _work_queue(), run_summary, _gate(), _promo("APPROVE"))
    assert updated["work_items"][0]["status"] == "DONE"
    assert updated["work_items"][0]["gate"]["status"] == "DONE"

