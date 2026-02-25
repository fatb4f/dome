from __future__ import annotations

from dataclasses import asdict
import json
import sqlite3
from threading import Lock
from time import time
from typing import Any

from tools.domed.runtime_state import EventRecord, JobRecord, TERMINAL_STATES


class SQLiteRuntimeStateStore:
    def __init__(self, db_path: str) -> None:
        self._lock = Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS jobs (
              job_id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              state TEXT NOT NULL,
              skill_id TEXT NOT NULL,
              profile TEXT NOT NULL,
              idempotency_key TEXT NOT NULL,
              request_hash TEXT NOT NULL,
              artifacts_json TEXT NOT NULL,
              created_at REAL NOT NULL,
              updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS idempotency (
              client_id TEXT NOT NULL,
              idempotency_key TEXT NOT NULL,
              request_hash TEXT NOT NULL,
              job_id TEXT NOT NULL,
              created_at REAL NOT NULL,
              PRIMARY KEY (client_id, idempotency_key)
            );
            CREATE TABLE IF NOT EXISTS events (
              job_id TEXT NOT NULL,
              seq INTEGER NOT NULL,
              event_type TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              ts_epoch REAL NOT NULL,
              PRIMARY KEY (job_id, seq)
            );
            CREATE INDEX IF NOT EXISTS idx_jobs_state_updated ON jobs(state, updated_at);
            CREATE INDEX IF NOT EXISTS idx_events_job_seq ON events(job_id, seq);
            """
        )
        self._conn.commit()

    def _decode_job(self, row: sqlite3.Row) -> JobRecord:
        return JobRecord(
            job_id=row["job_id"],
            run_id=row["run_id"],
            state=row["state"],
            skill_id=row["skill_id"],
            profile=row["profile"],
            idempotency_key=row["idempotency_key"],
            request_hash=row["request_hash"],
            artifacts=json.loads(row["artifacts_json"]),
            events=[],
        )

    def submit(self, *, job: JobRecord, client_id: str = "default") -> tuple[JobRecord, bool]:
        now = time()
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT request_hash, job_id FROM idempotency WHERE client_id = ? AND idempotency_key = ?",
                (client_id, job.idempotency_key),
            )
            prior = cur.fetchone()
            if prior is not None:
                if prior["request_hash"] != job.request_hash:
                    raise ValueError("idempotency key reused with different request hash")
                cur.execute("SELECT * FROM jobs WHERE job_id = ?", (prior["job_id"],))
                row = cur.fetchone()
                if row is None:
                    raise ValueError("idempotency ledger references missing job")
                return self._decode_job(row), True

            cur.execute(
                """
                INSERT INTO jobs(job_id, run_id, state, skill_id, profile, idempotency_key, request_hash, artifacts_json, created_at, updated_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_id,
                    job.run_id,
                    job.state,
                    job.skill_id,
                    job.profile,
                    job.idempotency_key,
                    job.request_hash,
                    json.dumps(job.artifacts, sort_keys=True),
                    now,
                    now,
                ),
            )
            cur.execute(
                """
                INSERT INTO idempotency(client_id, idempotency_key, request_hash, job_id, created_at)
                VALUES(?, ?, ?, ?, ?)
                """,
                (client_id, job.idempotency_key, job.request_hash, job.job_id, now),
            )
            self._conn.commit()
            return job, False

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            cur = self._conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
            row = cur.fetchone()
            if row is None:
                return None
            return self._decode_job(row)

    def transition(self, *, job_id: str, to_state: str) -> JobRecord:
        with self._lock:
            cur = self._conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
            row = cur.fetchone()
            if row is None:
                raise KeyError(job_id)
            current = row["state"]
            if current in TERMINAL_STATES:
                raise ValueError(f"terminal job cannot transition: {current} -> {to_state}")
            now = time()
            self._conn.execute(
                "UPDATE jobs SET state = ?, updated_at = ? WHERE job_id = ?",
                (to_state, now, job_id),
            )
            self._conn.commit()
            return JobRecord(
                job_id=row["job_id"],
                run_id=row["run_id"],
                state=to_state,
                skill_id=row["skill_id"],
                profile=row["profile"],
                idempotency_key=row["idempotency_key"],
                request_hash=row["request_hash"],
                artifacts=json.loads(row["artifacts_json"]),
            )

    def cancel(self, job_id: str) -> JobRecord:
        with self._lock:
            cur = self._conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
            row = cur.fetchone()
            if row is None:
                raise KeyError(job_id)
            current = row["state"]
            target = current if current in TERMINAL_STATES else "canceled"
            now = time()
            self._conn.execute(
                "UPDATE jobs SET state = ?, updated_at = ? WHERE job_id = ?",
                (target, now, job_id),
            )
            self._conn.commit()
            job = self._decode_job(row)
            job.state = target
            return job

    def append_event(self, *, job_id: str, event_type: str, payload: dict[str, Any]) -> EventRecord:
        with self._lock:
            cur = self._conn.execute("SELECT COALESCE(MAX(seq), 0) + 1 AS next_seq FROM events WHERE job_id = ?", (job_id,))
            next_seq = int(cur.fetchone()["next_seq"])
            evt = EventRecord(seq=next_seq, event_type=event_type, payload=payload)
            self._conn.execute(
                "INSERT INTO events(job_id, seq, event_type, payload_json, ts_epoch) VALUES(?, ?, ?, ?, ?)",
                (job_id, evt.seq, evt.event_type, json.dumps(evt.payload, sort_keys=True), evt.ts_epoch),
            )
            self._conn.execute("UPDATE jobs SET updated_at = ? WHERE job_id = ?", (time(), job_id))
            self._conn.commit()
            return evt

    def events_since(self, *, job_id: str, since_seq: int) -> list[EventRecord]:
        with self._lock:
            cur = self._conn.execute(
                """
                SELECT seq, event_type, payload_json, ts_epoch
                FROM events
                WHERE job_id = ? AND seq > ?
                ORDER BY seq ASC
                """,
                (job_id, since_seq),
            )
            out: list[EventRecord] = []
            for row in cur.fetchall():
                out.append(
                    EventRecord(
                        seq=int(row["seq"]),
                        event_type=row["event_type"],
                        payload=json.loads(row["payload_json"]),
                        ts_epoch=float(row["ts_epoch"]),
                    )
                )
            return out

    def gc(self, ttl_seconds: int) -> int:
        cutoff = time() - ttl_seconds
        with self._lock:
            cur = self._conn.execute(
                "SELECT job_id FROM jobs WHERE state IN ('succeeded','failed','canceled') AND updated_at < ?",
                (cutoff,),
            )
            stale_ids = [r["job_id"] for r in cur.fetchall()]
            if not stale_ids:
                return 0
            qmarks = ",".join("?" for _ in stale_ids)
            self._conn.execute(f"DELETE FROM events WHERE job_id IN ({qmarks})", stale_ids)
            self._conn.execute(f"DELETE FROM idempotency WHERE job_id IN ({qmarks})", stale_ids)
            self._conn.execute(f"DELETE FROM jobs WHERE job_id IN ({qmarks})", stale_ids)
            self._conn.commit()
            return len(stale_ids)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

