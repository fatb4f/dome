import json
from pathlib import Path

import pytest


jsonschema = pytest.importorskip("jsonschema")


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "ssot" / "schemas" / "tool.manifest.schema.json"
TOOLS_DIR = ROOT / "ssot" / "tools"


def test_tool_manifests_validate() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator_class = jsonschema.validators.validator_for(schema)
    validator = validator_class(schema)

    manifests = sorted(TOOLS_DIR.glob("*/manifest.yaml"))
    assert manifests, "No tool manifests found under ssot/tools/*/manifest.yaml"
    for path in manifests:
        payload = json.loads(path.read_text(encoding="utf-8"))
        validator.validate(payload)
