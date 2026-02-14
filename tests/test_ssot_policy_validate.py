import json
from pathlib import Path

import pytest


jsonschema = pytest.importorskip("jsonschema")


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "ssot" / "schemas"
POLICY_DIR = ROOT / "ssot" / "policy"


def _schema_for_policy(policy_path: Path) -> Path:
    return SCHEMAS_DIR / f"{policy_path.stem}.schema.json"


def test_each_policy_json_has_schema_file() -> None:
    policy_files = sorted(POLICY_DIR.glob("*.json"))
    assert policy_files, "No policy JSON files found under ssot/policy"
    missing = [str(path.name) for path in policy_files if not _schema_for_policy(path).exists()]
    assert not missing, f"Missing schema files for policy JSON: {missing}"


def test_policy_json_validates_against_matching_schema() -> None:
    policy_files = sorted(POLICY_DIR.glob("*.json"))
    for policy_path in policy_files:
        schema_path = _schema_for_policy(policy_path)
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        instance = json.loads(policy_path.read_text(encoding="utf-8"))
        validator_class = jsonschema.validators.validator_for(schema)
        validator = validator_class(schema)
        validator.validate(instance)
