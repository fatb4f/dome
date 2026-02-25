from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_dome_cli_list_tools(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    class FakeClient:
        def __init__(self, cfg) -> None:
            self.cfg = cfg

        def list_tools(self):
            item = types.SimpleNamespace(
                tool_id="skill-execute",
                version="v1",
                title="Skill Execute",
                short_description="desc",
                kind="skill",
            )
            return types.SimpleNamespace(status=types.SimpleNamespace(ok=True), tools=[item])

        def get_tool(self, tool_id):
            tool = types.SimpleNamespace(
                tool_id=tool_id,
                version="v1",
                title="Skill Execute",
                description="desc-long",
                short_description="desc",
                kind="skill",
                input_schema_ref="in",
                output_schema_ref="out",
                executor_backend="local-process",
                permissions=["process"],
                side_effects=["runtime-state-write"],
            )
            return types.SimpleNamespace(
                status=types.SimpleNamespace(ok=True, code=0, message="ok"),
                tool=tool,
            )

    class FakeCfg:
        def __init__(self, endpoint: str | None) -> None:
            self.endpoint = endpoint

    monkeypatch.setitem(
        sys.modules,
        "tools.codex.domed_client",
        types.SimpleNamespace(DomedClient=FakeClient, DomedClientConfig=FakeCfg),
    )

    from tools.codex import dome_cli

    old_argv, old_stdout = sys.argv, sys.stdout
    buf = io.StringIO()
    try:
        sys.argv = ["dome_cli.py", "list-tools"]
        sys.stdout = buf
        rc = dome_cli.main()
    finally:
        sys.argv = old_argv
        sys.stdout = old_stdout

    assert rc == 0
    out = json.loads(buf.getvalue())
    assert out["ok"] is True
    assert out["tools"][0]["tool_id"] == "skill-execute"
    assert "description" not in out["tools"][0]


def test_dome_cli_get_tool(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    class FakeClient:
        def __init__(self, cfg) -> None:
            self.cfg = cfg

        def list_tools(self):
            return types.SimpleNamespace(status=types.SimpleNamespace(ok=True), tools=[])

        def get_tool(self, tool_id):
            tool = types.SimpleNamespace(
                tool_id=tool_id,
                version="v1",
                title="Skill Execute",
                description="desc-long",
                short_description="desc",
                kind="skill",
                input_schema_ref="in",
                output_schema_ref="out",
                executor_backend="local-process",
                permissions=["process"],
                side_effects=["runtime-state-write"],
            )
            return types.SimpleNamespace(
                status=types.SimpleNamespace(ok=True, code=0, message="ok"),
                tool=tool,
            )

    class FakeCfg:
        def __init__(self, endpoint: str | None) -> None:
            self.endpoint = endpoint

    monkeypatch.setitem(
        sys.modules,
        "tools.codex.domed_client",
        types.SimpleNamespace(DomedClient=FakeClient, DomedClientConfig=FakeCfg),
    )

    from tools.codex import dome_cli

    old_argv, old_stdout = sys.argv, sys.stdout
    buf = io.StringIO()
    try:
        sys.argv = ["dome_cli.py", "get-tool", "--tool-id", "skill-execute"]
        sys.stdout = buf
        rc = dome_cli.main()
    finally:
        sys.argv = old_argv
        sys.stdout = old_stdout

    assert rc == 0
    out = json.loads(buf.getvalue())
    assert out["ok"] is True
    assert out["tool"]["tool_id"] == "skill-execute"
    assert out["tool"]["description"] == "desc-long"
