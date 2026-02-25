from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from time import time
from typing import Any


TERMINAL_STATES = {"succeeded", "failed", "canceled"}


@dataclass(slots=True)
class EventRecord:
    seq: int
    event_type: str
    payload: dict[str, Any]
    ts_epoch: float = field(default_factory=time)


@dataclass(slots=True)
class JobRecord:
    job_id: str
    run_id: str
    state: str
    skill_id: str
    profile: str
    idempotency_key: str
    request_hash: str
    artifacts: list[dict[str, str]] = field(default_factory=list)
    events: list[EventRecord] = field(default_factory=list)


class RuntimeStateStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._jobs: dict[str, JobRecord] = {}
        self._idempotency: dict[tuple[str, str], tuple[str, str]] = {}

    def submit(self, *, job: JobRecord, client_id: str = "default") -> tuple[JobRecord, bool]:
        key = (client_id, job.idempotency_key)
        with self._lock:
            prior = self._idempotency.get(key)
            if prior is not None:
                prior_request_hash, job_id = prior
                if prior_request_hash != job.request_hash:
                    raise ValueError("idempotency key reused with different request hash")
                return self._jobs[job_id], True

            self._jobs[job.job_id] = job
            self._idempotency[key] = (job.request_hash, job.job_id)
            return job, False

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def transition(self, *, job_id: str, to_state: str) -> JobRecord:
        with self._lock:
            job = self._jobs[job_id]
            if job.state in TERMINAL_STATES:
                raise ValueError(f"terminal job cannot transition: {job.state} -> {to_state}")
            job.state = to_state
            return job

    def cancel(self, job_id: str) -> JobRecord:
        with self._lock:
            job = self._jobs[job_id]
            if job.state not in TERMINAL_STATES:
                job.state = "canceled"
            return job

    def append_event(self, *, job_id: str, event_type: str, payload: dict[str, Any]) -> EventRecord:
        with self._lock:
            job = self._jobs[job_id]
            seq = len(job.events) + 1
            evt = EventRecord(seq=seq, event_type=event_type, payload=payload)
            job.events.append(evt)
            return evt

    def events_since(self, *, job_id: str, since_seq: int) -> list[EventRecord]:
        with self._lock:
            events = self._jobs[job_id].events
            return [evt for evt in events if evt.seq > since_seq]

