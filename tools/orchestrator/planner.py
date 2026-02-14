#!/usr/bin/env python
"""Translate xtrlv2-style pre-contracts into dome work.queue artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools.orchestrator.io_utils import atomic_write_json


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


def validate_task_graph(tasks: list[dict[str, Any]]) -> None:
    task_ids = [str(task.get("task_id", "")) for task in tasks]
    if not all(task_ids):
        raise ValueError("all tasks must have non-empty task_id")
    if len(set(task_ids)) != len(task_ids):
        raise ValueError("duplicate task_id in work.queue tasks")

    deps = {task_id: set() for task_id in task_ids}
    for task in tasks:
        task_id = str(task["task_id"])
        for dep in task.get("dependencies", []):
            dep_id = str(dep)
            if dep_id not in deps:
                raise ValueError(f"unknown dependency '{dep_id}' for task '{task_id}'")
            deps[task_id].add(dep_id)

    temp_mark: set[str] = set()
    perm_mark: set[str] = set()

    def visit(node: str) -> None:
        if node in perm_mark:
            return
        if node in temp_mark:
            raise ValueError("dependency cycle detected in work.queue tasks")
        temp_mark.add(node)
        for child in deps[node]:
            visit(child)
        temp_mark.remove(node)
        perm_mark.add(node)

    for task_id in task_ids:
        visit(task_id)


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
    validate_task_graph(work_queue["tasks"])
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
    atomic_write_json(args.out, work_queue)
    print(str(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
