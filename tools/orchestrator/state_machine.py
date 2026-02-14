#!/usr/bin/env python
"""State transition helpers for orchestrator work items."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


State = Literal["QUEUED", "CLAIMED", "RUNNING", "GATED", "DONE", "BLOCKED"]
Signal = Literal["claim", "run", "gate_pass", "gate_fail", "block"]


@dataclass(frozen=True)
class TransitionResult:
    ok: bool
    next_state: State
    reason_code: str | None = None


LEGAL_TRANSITIONS: dict[State, dict[Signal, State]] = {
    "QUEUED": {"claim": "CLAIMED", "block": "BLOCKED"},
    "CLAIMED": {"run": "RUNNING", "block": "BLOCKED"},
    "RUNNING": {"gate_pass": "GATED", "gate_fail": "BLOCKED", "block": "BLOCKED"},
    "GATED": {"gate_pass": "DONE", "gate_fail": "BLOCKED", "block": "BLOCKED"},
    "DONE": {},
    "BLOCKED": {},
}


def apply_transition(prev_state: State, signal: Signal) -> TransitionResult:
    table = LEGAL_TRANSITIONS.get(prev_state, {})
    if signal not in table:
        return TransitionResult(
            ok=False,
            next_state=prev_state,
            reason_code=f"STATE.INVALID_TRANSITION.{prev_state}.{signal}",
        )
    return TransitionResult(ok=True, next_state=table[signal], reason_code=None)
