#!/usr/bin/env python
"""XA-06 bounded outer loop tick controller."""

from __future__ import annotations

import argparse
from typing import Callable


def next_iter_plan(iteration: int, max_iterations: int, last_status: str) -> dict[str, object]:
    stop = iteration >= max_iterations or last_status in {"APPROVE", "REJECT"}
    return {"iteration": iteration, "continue": not stop, "stop_reason": None if not stop else f"status={last_status}"}


def run_loop(max_iterations: int, run_once: Callable[[int], str]) -> list[dict[str, object]]:
    history: list[dict[str, object]] = []
    last_status = "NEEDS_HUMAN"
    for i in range(1, max_iterations + 1):
        status = run_once(i)
        plan = next_iter_plan(i, max_iterations=max_iterations, last_status=status)
        history.append({"iteration": i, "status": status, **plan})
        last_status = status
        if not plan["continue"]:
            break
    return history


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run bounded outer loop ticks")
    p.add_argument("--max-iterations", type=int, default=3)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    history = run_loop(args.max_iterations, lambda i: "APPROVE" if i >= 2 else "NEEDS_HUMAN")
    print(history)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
