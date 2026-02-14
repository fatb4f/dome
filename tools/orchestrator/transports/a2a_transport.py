from __future__ import annotations

import queue
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


@dataclass
class A2AMessage:
    """Generic A2A envelope.

    `kind` is intentionally protocol-agnostic and is normalized by the bridge.
    """

    kind: str
    run_id: str
    payload: dict[str, Any]
    ts: str = field(default_factory=utc_now)


class A2ATransport:
    """In-memory A2A transport adapter for local orchestration tests."""

    def __init__(self) -> None:
        self._inbox: queue.Queue[A2AMessage] = queue.Queue()
        self._outbox: queue.Queue[A2AMessage] = queue.Queue()

    def enqueue_incoming(self, message: A2AMessage) -> None:
        self._inbox.put(message)

    def recv(self, timeout: float | None = None) -> A2AMessage | None:
        try:
            return self._inbox.get(timeout=timeout)
        except queue.Empty:
            return None

    def send(self, message: A2AMessage) -> None:
        self._outbox.put(message)

    def drain_outbox(self) -> list[A2AMessage]:
        out: list[A2AMessage] = []
        while True:
            try:
                out.append(self._outbox.get_nowait())
            except queue.Empty:
                break
        return out
