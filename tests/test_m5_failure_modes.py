from __future__ import annotations

from pathlib import Path
import sys
import types

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.codex.browse_skill import run_task_via_domed


def test_run_task_via_domed_retries_then_succeeds(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    attempts = {"n": 0}

    class FakeClient:
        def __init__(self, cfg) -> None:
            self.cfg = cfg

        def skill_execute(self, **kwargs):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise TimeoutError("simulated timeout")
            return types.SimpleNamespace(
                status=types.SimpleNamespace(ok=True, message="ok"),
                job_id="job-r",
                run_id="run-r",
                state=3,
            )

    class FakeCfg:
        def __init__(self, endpoint: str) -> None:
            self.endpoint = endpoint

    monkeypatch.setitem(
        sys.modules,
        "tools.codex.domed_client",
        types.SimpleNamespace(DomedClient=FakeClient, DomedClientConfig=FakeCfg),
    )

    out = run_task_via_domed(
        task={"op": "x"},
        domed_endpoint="127.0.0.1:50051",
        max_attempts=2,
        retry_sleep_seconds=0.0,
    )
    assert out["ok"] is True
    assert attempts["n"] == 2


def test_run_task_via_domed_retries_then_fails(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    class FakeClient:
        def __init__(self, cfg) -> None:
            self.cfg = cfg

        def skill_execute(self, **kwargs):
            raise TimeoutError("always timeout")

    class FakeCfg:
        def __init__(self, endpoint: str) -> None:
            self.endpoint = endpoint

    monkeypatch.setitem(
        sys.modules,
        "tools.codex.domed_client",
        types.SimpleNamespace(DomedClient=FakeClient, DomedClientConfig=FakeCfg),
    )

    with pytest.raises(RuntimeError, match="failed after 2 attempts"):
        run_task_via_domed(
            task={"op": "x"},
            domed_endpoint="127.0.0.1:50051",
            max_attempts=2,
            retry_sleep_seconds=0.0,
        )


def test_idempotency_conflict_integration() -> None:
    pytest.importorskip("grpc")
    pytest.importorskip("google.protobuf")
    from tools.codex.domed_client import DomedClient, DomedClientConfig
    from tools.domed.service import start_insecure_server

    server, port, _ = start_insecure_server()
    endpoint = f"127.0.0.1:{port}"
    client = DomedClient(DomedClientConfig(endpoint=endpoint))
    try:
        first = client.skill_execute(
            skill_id="skill-execute",
            profile="work",
            idempotency_key="idem-conflict",
            task={"a": 1},
            constraints={},
        )
        second = client.skill_execute(
            skill_id="skill-execute",
            profile="work",
            idempotency_key="idem-conflict",
            task={"a": 2},
            constraints={},
        )
        assert first.status.ok is True
        assert second.status.ok is False
        assert "idempotency key reused" in second.status.message
    finally:
        server.stop(grace=0).wait()


def test_daemon_unavailable_path() -> None:
    pytest.importorskip("grpc")
    pytest.importorskip("google.protobuf")
    with pytest.raises(RuntimeError, match="failed after 1 attempts"):
        run_task_via_domed(
            task={"op": "x"},
            domed_endpoint="127.0.0.1:9",
            max_attempts=1,
            retry_sleep_seconds=0.0,
        )
