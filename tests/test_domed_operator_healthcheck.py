from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_operator_healthcheck_script_with_fake_client(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    class FakeClient:
        def __init__(self, cfg) -> None:
            self.cfg = cfg

        def health(self):
            return types.SimpleNamespace(
                status=types.SimpleNamespace(ok=True),
                daemon_version="domed-test",
            )

        def list_capabilities(self, profile: str):
            return types.SimpleNamespace(
                status=types.SimpleNamespace(ok=True),
                capabilities=[types.SimpleNamespace(name="skill-execute")],
            )

    class FakeCfg:
        def __init__(self, endpoint: str) -> None:
            self.endpoint = endpoint

    monkeypatch.setitem(
        sys.modules,
        "tools.codex.domed_client",
        types.SimpleNamespace(DomedClient=FakeClient, DomedClientConfig=FakeCfg),
    )

    mod = __import__("tools.domed.operator_healthcheck", fromlist=["main"])
    argv = sys.argv
    try:
        sys.argv = ["operator_healthcheck.py", "--endpoint", "127.0.0.1:50051"]
        rc = mod.main()
    finally:
        sys.argv = argv
    assert rc == 0

