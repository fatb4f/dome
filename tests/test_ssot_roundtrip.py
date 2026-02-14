import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SSOT_DIR = ROOT / "ssot"


def test_ssot_json_roundtrip() -> None:
    json_files = sorted(SSOT_DIR.rglob("*.json"))
    assert json_files, "No JSON files found under ssot/"
    for path in json_files:
        original = json.loads(path.read_text(encoding="utf-8"))
        encoded = json.dumps(original, sort_keys=True, separators=(",", ":"))
        round_tripped = json.loads(encoded)
        assert round_tripped == original, f"Round-trip mismatch for {path.relative_to(ROOT)}"
