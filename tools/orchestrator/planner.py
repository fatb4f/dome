#!/usr/bin/env python
"""Translate xtrlv2-style pre-contracts into dome work.queue artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _required(payload: dict[str, Any], key: str) -> Any:
    if key not in payload:
        raise ValueError(f"missing required key: {key}")
    return payload[key]


def _build_default_tasks(contract: dict[str, Any]) -> list[dict[str, Any]]:
    packet_id = str(contract.get("packet_id", "packet"))
    plan_card = contract.get("plan_card", {})
    why = plan_card.get("why", "Execute objective")
    what = plan_card.get("what", "Implement requested change")

    tasks = [
        {
            "task_id": f"{packet_id}-plan",
            "goal": f"Plan execution scope: {why}",
            "status": "QUEUED",
            "dependencies": [],
        },
        {
            "task_id": f"{packet_id}-implement",
            "goal": str(what),
            "status": "QUEUED",
            "dependencies": [f"{packet_id}-plan"],
        },
    ]
    if contract.get("actions", {}).get("test"):
        tasks.append(
            {
                "task_id": f"{packet_id}-verify",
                "goal": "Run deterministic verification from pre-contract actions.test",
                "status": "QUEUED",
                "dependencies": [f"{packet_id}-implement"],
            }
        )
    return tasks


def pre_contract_to_work_queue(contract: dict[str, Any]) -> dict[str, Any]:
    _required(contract, "packet_id")
    base_ref = str(contract.get("base_ref", "main"))
    budgets = contract.get("budgets", {})
    max_workers = max(1, int(budgets.get("iteration_budget", 2)))

    work_queue = {
        "version": "0.2.0",
        "run_id": str(contract["packet_id"]),
        "base_ref": base_ref,
        "max_workers": max_workers,
        "tasks": _build_default_tasks(contract),
    }
    return work_queue


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Translate xtrlv2 pre-contract JSON to dome work.queue JSON"
    )
    parser.add_argument("--pre-contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    contract = json.loads(args.pre_contract.read_text(encoding="utf-8"))
    work_queue = pre_contract_to_work_queue(contract)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(work_queue, indent=2), encoding="utf-8")
    print(str(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

