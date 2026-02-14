#!/usr/bin/env python
"""XA-05 substrate layout compatibility scaffolding."""

from __future__ import annotations

from pathlib import Path

REQUIRED_DIRS = [
    "queue",
    "out",
    "locks",
    "promote",
    "worktrees",
    "ledger",
]


def ensure_substrate_layout(run_root: Path, run_id: str) -> Path:
    base = run_root / run_id / "substrate"
    for rel in REQUIRED_DIRS:
        (base / rel).mkdir(parents=True, exist_ok=True)
    return base
