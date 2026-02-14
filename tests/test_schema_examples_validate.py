import json
from pathlib import Path

import pytest


jsonschema = pytest.importorskip("jsonschema")
referencing = pytest.importorskip("referencing")


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "ssot" / "schemas"
EXAMPLES_DIR = ROOT / "ssot" / "examples"


def _schema_registry():
    registry = referencing.Registry()
    for schema_path in sorted(SCHEMAS_DIR.glob("*.json")):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        resource = referencing.Resource.from_contents(schema)
        registry = registry.with_resource(schema_path.as_uri(), resource)
        registry = registry.with_resource(schema_path.name, resource)
        registry = registry.with_resource(f"./{schema_path.name}", resource)
    return registry


def _schema_for_example(example_path: Path) -> Path:
    schema_name = f"{example_path.stem}.schema.json"
    return SCHEMAS_DIR / schema_name


def test_each_example_has_schema_file() -> None:
    examples = sorted(EXAMPLES_DIR.glob("*.json"))
    assert examples, "No examples found under ssot/examples"
    missing = [str(path.name) for path in examples if not _schema_for_example(path).exists()]
    assert not missing, f"Missing schema files for examples: {missing}"


def test_examples_validate_against_matching_schemas() -> None:
    registry = _schema_registry()
    examples = sorted(EXAMPLES_DIR.glob("*.json"))
    for example_path in examples:
        schema_path = _schema_for_example(example_path)
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        instance = json.loads(example_path.read_text(encoding="utf-8"))
        validator_class = jsonschema.validators.validator_for(schema)
        validator = validator_class(schema, registry=registry)
        validator.validate(instance)
