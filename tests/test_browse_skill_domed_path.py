from __future__ import annotations

from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.codex.browse_skill import run_task_via_domed


def test_run_task_via_domed_uses_client(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    calls: list[tuple[str, str, str]] = []

    class FakeClient:
        def __init__(self, cfg) -> None:
            self.cfg = cfg

        def skill_execute(self, *, skill_id, profile, idempotency_key, task, constraints):
            calls.append((skill_id, profile, idempotency_key))
            assert isinstance(task, dict)
            assert isinstance(constraints, dict)
            return types.SimpleNamespace(
                status=types.SimpleNamespace(ok=True, message="ok"),
                job_id="job-123",
                run_id="run-123",
                state=2,
            )

    class FakeCfg:
        def __init__(self, endpoint: str) -> None:
            self.endpoint = endpoint

    fake_module = types.SimpleNamespace(DomedClient=FakeClient, DomedClientConfig=FakeCfg)
    monkeypatch.setitem(sys.modules, "tools.codex.domed_client", fake_module)

    out = run_task_via_domed(
        task={"op": "browse.fetch", "args": {}},
        domed_endpoint="127.0.0.1:50051",
        profile="work",
        idempotency_key="idem-1",
    )
    assert out["ok"] is True
    assert out["job_id"] == "job-123"
    assert calls == [("skill-execute", "work", "idem-1")]

