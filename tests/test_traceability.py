from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.traceability import build_traceability_report  # noqa: E402


def test_traceability_report_has_required_ids() -> None:
    report = build_traceability_report(ROOT)
    assert report["status"] == "PASS"
    requirements = report["requirements"]
    assert "CL-REQ-0001" in requirements
    assert "CL-REQ-0005" in requirements
