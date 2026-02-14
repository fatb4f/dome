import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.runtime_config import load_runtime_profile


def test_load_runtime_profile_default_and_named() -> None:
    path = ROOT / "ssot/examples/runtime.config.json"
    schema = ROOT / "ssot/schemas/runtime.config.schema.json"

    default_profile = load_runtime_profile(path, None, schema)
    assert default_profile["name"] == "tdd"
    assert default_profile["pattern"] == "tdd"
    assert default_profile["budgets"]["max_retries"] == 2

    refactor = load_runtime_profile(path, "refactor", schema)
    assert refactor["name"] == "refactor"
    assert refactor["pattern"] == "refactor"
    assert refactor["budgets"]["risk_threshold"] == 50


def test_load_runtime_profile_unknown_raises() -> None:
    path = ROOT / "ssot/examples/runtime.config.json"
    schema = ROOT / "ssot/schemas/runtime.config.schema.json"
    with pytest.raises(ValueError):
        load_runtime_profile(path, "does-not-exist", schema)


def test_load_runtime_profile_without_file_returns_defaults(tmp_path: Path) -> None:
    profile = load_runtime_profile(None, "tdd", tmp_path / "unused.json")
    assert profile["name"] == "tdd"
    assert profile["models"] == {}
    assert profile["budgets"] == {}
