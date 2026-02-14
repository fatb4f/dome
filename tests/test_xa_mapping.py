from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.xa_mapping import dome_to_substrate, substrate_to_dome


def test_status_mapping_roundtrip() -> None:
    assert dome_to_substrate("APPROVE") == "PROMOTE"
    assert dome_to_substrate("REJECT") == "DENY"
    assert dome_to_substrate("NEEDS_HUMAN") == "STOP"
    assert substrate_to_dome("PROMOTE") == "APPROVE"


def test_status_mapping_invalid() -> None:
    with pytest.raises(ValueError):
        dome_to_substrate("UNKNOWN")
