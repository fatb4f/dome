from __future__ import annotations

from pathlib import Path
import json
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest.importorskip("grpc")
pytest.importorskip("google.protobuf")

from tools.codex.domed_client import DomedClient, DomedClientConfig
from tools.domed.service import start_insecure_server


def test_skill_execute_routes_real_local_process_tool() -> None:
    server, port, _service = start_insecure_server()
    client = DomedClient(DomedClientConfig(endpoint=f"127.0.0.1:{port}"))
    try:
        submit = client.skill_execute(
            skill_id="domed.exec-probe",
            profile="work",
            idempotency_key="idem-exec-probe",
            task={"stdout": ["alpha"], "stderr": ["beta"], "progress": [0.5], "exit_code": 0},
            constraints={},
        )
        assert submit.status.ok is True
        status = client.get_job_status(submit.job_id)
        assert status.status.ok is True
        assert status.state != 0
        events = list(client.stream_job_events(job_id=submit.job_id, since_seq=0, follow=False))
        payloads = [json.loads(e.payload_json) for e in events]
        assert any(p.get("line") == "alpha" for p in payloads)
        assert any(p.get("line") == "beta" for p in payloads)
        assert any("progress" in p or "value" in p for p in payloads)
        assert any(p.get("exit_code") == 0 for p in payloads if isinstance(p, dict))
    finally:
        server.stop(grace=0).wait()


def test_skill_execute_unknown_tool_rejected() -> None:
    server, port, _service = start_insecure_server()
    client = DomedClient(DomedClientConfig(endpoint=f"127.0.0.1:{port}"))
    try:
        out = client.skill_execute(
            skill_id="does.not.exist",
            profile="work",
            idempotency_key="idem-no-tool",
            task={},
            constraints={},
        )
        assert out.status.ok is False
        assert "not found" in out.status.message
        assert out.job_id == ""
    finally:
        server.stop(grace=0).wait()
