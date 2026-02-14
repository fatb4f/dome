#!/usr/bin/env python
"""XA-01 helpers for dome<->xtrl decision semantics mapping."""

from __future__ import annotations

from typing import Literal

DomeStatus = Literal["APPROVE", "REJECT", "NEEDS_HUMAN"]
SubstrateStatus = Literal["PROMOTE", "DENY", "STOP"]


DOME_TO_SUBSTRATE: dict[str, SubstrateStatus] = {
    "APPROVE": "PROMOTE",
    "REJECT": "DENY",
    "NEEDS_HUMAN": "STOP",
}
SUBSTRATE_TO_DOME: dict[str, DomeStatus] = {
    "PROMOTE": "APPROVE",
    "DENY": "REJECT",
    "STOP": "NEEDS_HUMAN",
}


def dome_to_substrate(status: str) -> SubstrateStatus:
    if status not in DOME_TO_SUBSTRATE:
        raise ValueError(f"unknown dome status: {status}")
    return DOME_TO_SUBSTRATE[status]


def substrate_to_dome(status: str) -> DomeStatus:
    if status not in SUBSTRATE_TO_DOME:
        raise ValueError(f"unknown substrate status: {status}")
    return SUBSTRATE_TO_DOME[status]
