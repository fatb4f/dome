from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.loop_tick import run_loop


def test_loop_tick_stops_on_approve() -> None:
    hist = run_loop(5, lambda i: "NEEDS_HUMAN" if i < 2 else "APPROVE")
    assert len(hist) == 2
    assert hist[-1]["status"] == "APPROVE"
