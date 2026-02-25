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

