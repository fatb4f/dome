from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.evidence_capsule import to_capsule


def test_evidence_capsule_translation() -> None:
    payload = {
        "otel": {
            "backend": "local",
            "trace_id_hex": "0" * 32,
            "span_id_hex": "1" * 16,
            "run_id": "r1",
        },
        "signals": {"task.status": "PASS"},
        "artifacts": [{"path": "x", "sha256": "a" * 64}],
    }
    out = to_capsule(payload)
    assert out["trace"]["trace_id_hex"] == "0" * 32
    assert out["signals"]["task.status"] == "PASS"
