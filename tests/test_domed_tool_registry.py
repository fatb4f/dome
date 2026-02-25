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
        "description",
        "input_schema_ref",
        "output_schema_ref",
        "executor_backend",
    }
    for item in tools:
        assert required.issubset(item.keys())

