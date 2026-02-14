from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.state_machine import apply_transition  # noqa: E402


def test_legal_state_transitions() -> None:
    assert apply_transition("QUEUED", "claim").next_state == "CLAIMED"
    assert apply_transition("CLAIMED", "run").next_state == "RUNNING"
    assert apply_transition("RUNNING", "gate_pass").next_state == "GATED"
    assert apply_transition("GATED", "gate_pass").next_state == "DONE"


def test_illegal_transition_rejected() -> None:
    out = apply_transition("DONE", "run")
    assert out.ok is False
    assert out.reason_code == "STATE.INVALID_TRANSITION.DONE.run"
