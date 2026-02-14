from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.promote import create_promotion_decision


def _gate(status: str, confidence: float = 0.9, risk: int = 20) -> dict:
    return {
        "version": "0.2.0",
        "run_id": "wave-promote-001",
        "task_id": "wave-gate",
        "status": status,
        "reason_codes": [],
        "confidence": confidence,
        "risk_score": risk,
        "notes": [],
        "telemetry_ref": {"trace_id_hex": "0" * 32, "span_id_hex": "0" * 16},
    }


def test_promote_approves_when_gate_approve_and_threshold_ok() -> None:
    decision = create_promotion_decision(_gate("APPROVE", confidence=0.95, risk=25), min_confidence=0.7, max_risk=60)
    assert decision["decision"] == "APPROVE"


def test_promote_reject_passthrough() -> None:
    decision = create_promotion_decision(_gate("REJECT", confidence=0.99, risk=10), min_confidence=0.7, max_risk=60)
    assert decision["decision"] == "REJECT"


def test_promote_needs_human_on_high_risk() -> None:
    decision = create_promotion_decision(_gate("APPROVE", confidence=0.95, risk=80), min_confidence=0.7, max_risk=60)
    assert decision["decision"] == "NEEDS_HUMAN"
    assert "POLICY.NEEDS_HUMAN" in decision["reason_codes"]

