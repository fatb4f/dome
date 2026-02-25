from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.domed.runtime_state import JobRecord, RuntimeStateStore


def _job(job_id: str, *, idem: str, req_hash: str) -> JobRecord:
    return JobRecord(
        job_id=job_id,
        run_id=f"run-{job_id}",
        state="queued",
        skill_id="skill-execute",
        profile="work",
        idempotency_key=idem,
        request_hash=req_hash,
    )


def test_submit_idempotent_replay_returns_existing_job() -> None:
    store = RuntimeStateStore()
    first, replay = store.submit(job=_job("j1", idem="k1", req_hash="h1"), client_id="c1")
    second, replay2 = store.submit(job=_job("j2", idem="k1", req_hash="h1"), client_id="c1")
    assert replay is False
    assert replay2 is True
    assert first.job_id == second.job_id == "j1"


def test_submit_idempotency_conflict_rejected() -> None:
    store = RuntimeStateStore()
    store.submit(job=_job("j1", idem="k1", req_hash="h1"), client_id="c1")
    try:
        store.submit(job=_job("j2", idem="k1", req_hash="h2"), client_id="c1")
    except ValueError as exc:
        assert "idempotency key reused" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected idempotency conflict")


def test_event_sequence_and_since_cursor() -> None:
    store = RuntimeStateStore()
    store.submit(job=_job("j1", idem="k1", req_hash="h1"), client_id="c1")
    e1 = store.append_event(job_id="j1", event_type="state_change", payload={"to": "running"})
    e2 = store.append_event(job_id="j1", event_type="log", payload={"line": "x"})
    assert (e1.seq, e2.seq) == (1, 2)
    events = store.events_since(job_id="j1", since_seq=1)
    assert len(events) == 1
    assert events[0].seq == 2


def test_terminal_state_blocks_transition() -> None:
    store = RuntimeStateStore()
    store.submit(job=_job("j1", idem="k1", req_hash="h1"), client_id="c1")
    store.cancel("j1")
    try:
        store.transition(job_id="j1", to_state="running")
    except ValueError as exc:
        assert "terminal job cannot transition" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected terminal transition rejection")
