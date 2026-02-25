from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.codex.browse_skill import validate_codex_browse_contract, validate_identity_graph_contracts


def _write(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


def test_validate_identity_graph_contracts(tmp_path: Path) -> None:
    ig = tmp_path / "identity-graph"
    spec = ig / "spec"
    spec.mkdir(parents=True)
    _write(
        spec / "version.json",
        {
            "contracts": {
                "browse_feedback_event": "1.0.0",
                "browse_feedback_batch": "1.0.0",
                "feedforward_policy_bundle": "1.0.0",
            }
        },
    )
    for schema in [
        "browse_feedback_event.schema.json",
        "browse_feedback_batch.schema.json",
        "feedforward_policy_bundle.schema.json",
    ]:
        _write(spec / schema, {"type": "object"})
    validate_identity_graph_contracts(ig)


def test_validate_codex_browse_contract_with_fake_skill(tmp_path: Path) -> None:
    root = tmp_path / "codex-browse"
    skill = root / "docs" / "codex-web-browse-skill"
    schemas = skill / "schemas"
    scripts = skill / "scripts"
    scripts.mkdir(parents=True)
    schemas.mkdir(parents=True)

    _write(
        skill / "contract.json",
        {
            "skill": {"entrypoint": "scripts/runner.py"},
            "schemas": {
                "task": "schemas/task.schema.json",
                "result": "schemas/result.schema.json",
                "prefs": "schemas/prefs.schema.json",
            },
        },
    )
    _write(
        schemas / "task.schema.json",
        {
            "type": "object",
            "required": ["op", "args"],
            "properties": {"op": {"type": "string"}, "args": {"type": "object"}},
        },
    )
    _write(
        schemas / "result.schema.json",
        {
            "type": "object",
            "required": ["ok", "op"],
            "properties": {"ok": {"type": "boolean"}, "op": {"type": "string"}},
        },
    )
    _write(schemas / "prefs.schema.json", {"type": "object"})
    (scripts / "runner.py").write_text("#!/usr/bin/env python3\nprint('ok')\n", encoding="utf-8")
    paths = validate_codex_browse_contract(root)
    assert paths["runner"].exists()
