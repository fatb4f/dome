from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol


@dataclass(slots=True)
class ExecutionRequest:
    run_id: str
    job_id: str
    tool_id: str
    profile: str
    task: dict[str, Any]
    constraints: dict[str, Any]
    entrypoint: list[str]
    cwd: Path
    timeout_seconds: int = 120
    env_allowlist: list[str] | None = None


@dataclass(slots=True)
class ExecutionEvent:
    kind: str
    payload: dict[str, Any]


@dataclass(slots=True)
class ExecutionResult:
    terminal_state: str
    exit_code: int
    message: str = ""


ExecutionEventSink = Callable[[ExecutionEvent], None]


class Executor(Protocol):
    def execute(self, request: ExecutionRequest, sink: ExecutionEventSink) -> ExecutionResult:
        ...

