#!/usr/bin/env python
"""Runtime profile loader for demo orchestrator runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _validate_runtime_config(payload: dict[str, Any], schema_path: Path) -> None:
    try:
        import jsonschema  # type: ignore
    except Exception:
        return
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=payload, schema=schema)


def load_runtime_profile(
    runtime_config_path: Path | None,
    profile: str | None,
    schema_path: Path,
) -> dict[str, Any]:
    if runtime_config_path is None:
        return {"name": profile or "default", "pattern": None, "models": {}, "budgets": {}}

    payload = json.loads(runtime_config_path.read_text(encoding="utf-8"))
    _validate_runtime_config(payload, schema_path)
    default_profile = str(payload.get("default_profile", "default"))
    selected = profile or default_profile
    profiles = payload.get("profiles", {})
    if selected not in profiles:
        raise ValueError(f"runtime profile not found: {selected}")
    node = dict(profiles[selected])
    return {
        "name": selected,
        "pattern": node.get("pattern"),
        "models": dict(node.get("models", {})),
        "budgets": dict(node.get("budgets", {})),
    }
