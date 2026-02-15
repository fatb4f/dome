import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def test_pin_manifest_hashes_match() -> None:
    manifest_path = ROOT / "ssot/pins/xtrlv2/pin_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for artifact in manifest["artifacts"]:
        path = ROOT / artifact["path"]
        assert path.exists(), f"missing pinned artifact: {artifact['path']}"
        assert _sha256(path) == artifact["sha256"], f"hash mismatch for {artifact['path']}"


def test_guardrails_pin_has_expected_contract_shape() -> None:
    schema = json.loads(
        (ROOT / "ssot/pins/xtrlv2/guardrails_bundle.schema.json").read_text(encoding="utf-8")
    )
    assert schema.get("title") == "GuardrailsBundle"
    assert "properties" in schema
    assert "guards" in schema["properties"]


def test_reason_codes_pin_has_classes_precedence() -> None:
    reason_codes = json.loads((ROOT / "ssot/pins/xtrlv2/reason_codes.json").read_text(encoding="utf-8"))
    assert reason_codes.get("schema_version") == "0.1"
    precedence = reason_codes.get("classes_precedence")
    assert isinstance(precedence, list)
    assert "structural" in precedence
