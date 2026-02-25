from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from time import sleep

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.domed.runtime_state import JobRecord
from tools.domed.sqlite_state import SQLiteRuntimeStateStore


def _job(job_id: str, *, idem: str, req_hash: str, state: str = "queued") -> JobRecord:
    return JobRecord(
        job_id=job_id,
        run_id=f"run-{job_id}",
        state=state,
        skill_id="skill-execute",
        profile="work",
        idempotency_key=idem,
        request_hash=req_hash,
    )


def test_sqlite_store_submit_and_replay() -> None:
    with TemporaryDirectory(prefix="domed-state-") as td:
        store = SQLiteRuntimeStateStore(f"{td}/state.db")
        first, replay1 = store.submit(job=_job("j1", idem="k1", req_hash="h1"), client_id="c1")
        second, replay2 = store.submit(job=_job("j2", idem="k1", req_hash="h1"), client_id="c1")
        assert replay1 is False
        assert replay2 is True
        assert second.job_id == first.job_id == "j1"
        store.close()


def test_sqlite_store_gc_ttl() -> None:
    with TemporaryDirectory(prefix="domed-state-") as td:
        store = SQLiteRuntimeStateStore(f"{td}/state.db")
        store.submit(job=_job("j1", idem="k1", req_hash="h1"), client_id="c1")
        store.transition(job_id="j1", to_state="running")
        store.transition(job_id="j1", to_state="succeeded")
        store.append_event(job_id="j1", event_type="state_change", payload={"to": "succeeded"})
        sleep(0.02)
        deleted = store.gc(ttl_seconds=0)
        assert deleted == 1
        assert store.get("j1") is None
        store.close()

