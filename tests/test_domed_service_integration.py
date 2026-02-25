from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

grpc = pytest.importorskip("grpc")
pytest.importorskip("google.protobuf")

from tools.codex.domed_client import DomedClient, DomedClientConfig
from tools.domed.service import start_insecure_server


def test_domed_service_lifecycle_roundtrip() -> None:
    server, port, _service = start_insecure_server()
    endpoint = f"127.0.0.1:{port}"
    client = DomedClient(DomedClientConfig(endpoint=endpoint))
    try:
        health = client.health()
        assert health.status.ok is True
        assert health.daemon_version

        caps = client.list_capabilities("work")
        assert caps.status.ok is True
        assert any(c.name == "skill-execute" for c in caps.capabilities)
        tools = client.list_tools()
        assert tools.status.ok is True
        assert any(t.tool_id == "skill-execute" for t in tools.tools)
        assert all(hasattr(t, "short_description") for t in tools.tools)
        tool_detail = client.get_tool("skill-execute")
        assert tool_detail.status.ok is True
        assert tool_detail.tool.tool_id == "skill-execute"
        assert tool_detail.tool.executor_backend
        assert tool_detail.tool.input_schema_ref.startswith("ssot/tools/")

        submit = client.skill_execute(
            skill_id="skill-execute",
            profile="work",
            idempotency_key="idem-1",
            task={"task": "demo"},
            constraints={"mode": "test"},
        )
        assert submit.status.ok is True
        assert submit.job_id
        assert submit.run_id

        status = client.get_job_status(submit.job_id)
        assert status.status.ok is True
        assert status.job_id == submit.job_id

        events = list(client.stream_job_events(job_id=submit.job_id, since_seq=0, follow=False))
        assert len(events) >= 1
        assert events[0].seq >= 1

        cancel = client.cancel_job(job_id=submit.job_id, idempotency_key="cancel-1")
        assert cancel.status.ok is True

        status2 = client.get_job_status(submit.job_id)
        assert status2.state != 0
    finally:
        server.stop(grace=0).wait()


def test_domed_service_concrete_job_types() -> None:
    server, port, _service = start_insecure_server()
    endpoint = f"127.0.0.1:{port}"
    client = DomedClient(DomedClientConfig(endpoint=endpoint))
    try:
        log_job = client.skill_execute(
            skill_id="job.log",
            profile="work",
            idempotency_key="idem-log",
            task={"lines": ["a", "b"]},
            constraints={},
        )
        assert log_job.status.ok is True
        log_events = list(client.stream_job_events(job_id=log_job.job_id, since_seq=0, follow=False))
        assert any(e.event_type != 0 and "line" in e.payload_json for e in log_events)

        fail_job = client.skill_execute(
            skill_id="job.fail",
            profile="work",
            idempotency_key="idem-fail",
            task={"reason": "expected"},
            constraints={},
        )
        fail_status = client.get_job_status(fail_job.job_id)
        assert fail_status.state != 0
    finally:
        server.stop(grace=0).wait()
