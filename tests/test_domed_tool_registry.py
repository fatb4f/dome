from __future__ import annotations

import json
from pathlib import Path


def test_tool_registry_schema_minimum() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "ssot" / "domed" / "tool_registry.v1.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload.get("version")
    tools = payload.get("tools", [])
    assert isinstance(tools, list) and tools
    required = {
        "tool_id",
        "version",
        "title",
        "short_description",
        "kind",
        "description",
        "input_schema_ref",
        "output_schema_ref",
        "executor_backend",
        "permissions",
        "side_effects",
    }
    for item in tools:
        assert required.issubset(item.keys())


def test_manifest_layout_exists_and_is_loadable() -> None:
    root = Path(__file__).resolve().parents[1]
    tools_root = root / "ssot" / "tools"
    manifests = sorted(tools_root.glob("*/manifest.yaml"))
    assert manifests, "Expected tool manifests under ssot/tools/*/manifest.yaml"
    for manifest in manifests:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        assert payload.get("tool_id")
        assert payload.get("title")
        assert payload.get("input_schema_ref")
        assert payload.get("output_schema_ref")
