import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_profiles_have_catalog_mapping() -> None:
    cfg = json.loads((ROOT / "ssot/examples/runtime.config.json").read_text(encoding="utf-8"))
    pmap = json.loads((ROOT / "ssot/examples/profile.catalog.map.json").read_text(encoding="utf-8"))
    mapped = set(pmap["profiles"].keys())
    for profile_name in cfg["profiles"].keys():
        assert profile_name in mapped
