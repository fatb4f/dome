from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest.importorskip("grpc")
pytest.importorskip("google.protobuf")

from tools.codex.domed_client import DomedClient, DomedClientConfig
from tools.domed.service import start_insecure_server


def test_stream_follow_true_tails_until_terminal() -> None:
    server, port, _service = start_insecure_server()
    client = DomedClient(DomedClientConfig(endpoint=f"127.0.0.1:{port}"))
    try:
        submit = client.skill_execute(
            skill_id="domed.exec-probe",
            profile="work",
            idempotency_key="idem-follow-1",
            task={"stdout": ["s1", "s2"], "progress": [0.3], "exit_code": 0},
            constraints={},
        )
        events = list(client.stream_job_events(job_id=submit.job_id, since_seq=0, follow=True))
        assert events, "expected tail stream events"
        payloads = [json.loads(e.payload_json) for e in events]
        assert any(p.get("line") == "s1" for p in payloads)
        assert any(p.get("exit_code") == 0 for p in payloads if isinstance(p, dict))
        status = client.get_job_status(submit.job_id)
        assert status.state != 0
    finally:
        server.stop(grace=0).wait()


def test_stream_since_seq_resume_is_deterministic() -> None:
    server, port, _service = start_insecure_server()
    client = DomedClient(DomedClientConfig(endpoint=f"127.0.0.1:{port}"))
    try:
        submit = client.skill_execute(
            skill_id="job.log",
            profile="work",
            idempotency_key="idem-resume-1",
            task={"lines": ["a", "b", "c"]},
            constraints={},
        )
        first = list(client.stream_job_events(job_id=submit.job_id, since_seq=0, follow=False))
        assert len(first) >= 2
        cursor = first[1].seq
        resumed = list(client.stream_job_events(job_id=submit.job_id, since_seq=cursor, follow=False))
        assert resumed
        assert all(e.seq > cursor for e in resumed)
        tail = [e.seq for e in first if e.seq > cursor]
        assert [e.seq for e in resumed] == tail
    finally:
        server.stop(grace=0).wait()

