from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.codex.domed_client import DomedClient


class _Req:
    def __init__(self, **kwargs: object) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


class _FakePB2:
    HealthRequest = _Req
    ListCapabilitiesRequest = _Req
    SkillExecuteRequest = _Req
    GetJobStatusRequest = _Req
    CancelJobRequest = _Req
    StreamJobEventsRequest = _Req


class _FakeStub:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def Health(self, req: object) -> object:
        self.calls.append(("Health", req))
        return SimpleNamespace(status=SimpleNamespace(ok=True))

    def ListCapabilities(self, req: object) -> object:
        self.calls.append(("ListCapabilities", req))
        return SimpleNamespace(status=SimpleNamespace(ok=True), capabilities=[])

    def SkillExecute(self, req: object) -> object:
        self.calls.append(("SkillExecute", req))
        return SimpleNamespace(
            status=SimpleNamespace(ok=True, message="submitted"),
            job_id="job-1",
            run_id="run-1",
            state=2,
        )

    def GetJobStatus(self, req: object) -> object:
        self.calls.append(("GetJobStatus", req))
        return SimpleNamespace(status=SimpleNamespace(ok=True), state=3)

    def CancelJob(self, req: object) -> object:
        self.calls.append(("CancelJob", req))
        return SimpleNamespace(status=SimpleNamespace(ok=True))

    def StreamJobEvents(self, req: object) -> object:
        self.calls.append(("StreamJobEvents", req))
        return iter([SimpleNamespace(seq=1), SimpleNamespace(seq=2)])


def _client_with_fake_stub() -> tuple[DomedClient, _FakeStub]:
    c = DomedClient.__new__(DomedClient)
    stub = _FakeStub()
    c._pb2 = _FakePB2()  # type: ignore[attr-defined]
    c._stub = stub  # type: ignore[attr-defined]
    return c, stub


def test_stub_matrix_health_and_capabilities() -> None:
    c, stub = _client_with_fake_stub()
    h = c.health()
    caps = c.list_capabilities("work")
    assert h.status.ok is True
    assert caps.status.ok is True
    assert [name for name, _ in stub.calls] == ["Health", "ListCapabilities"]


def test_stub_matrix_execute_and_status_and_cancel() -> None:
    c, stub = _client_with_fake_stub()
    out = c.skill_execute(
        skill_id="skill-execute",
        profile="work",
        idempotency_key="idem-x",
        task={"op": "ping"},
        constraints={"a": 1},
    )
    status = c.get_job_status("job-1")
    cancel = c.cancel_job(job_id="job-1", idempotency_key="cancel-1")
    assert out.status.ok is True
    assert status.status.ok is True
    assert cancel.status.ok is True
    call_names = [name for name, _ in stub.calls]
    assert call_names == ["SkillExecute", "GetJobStatus", "CancelJob"]


def test_stub_matrix_stream_resume_cursor() -> None:
    c, stub = _client_with_fake_stub()
    events = list(c.stream_job_events(job_id="job-1", since_seq=1, follow=False))
    assert len(events) == 2
    name, req = stub.calls[-1]
    assert name == "StreamJobEvents"
    assert getattr(req, "since_seq") == 1

