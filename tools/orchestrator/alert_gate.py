#!/usr/bin/env python
"""Machine-checkable alert threshold gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate alert thresholds for a run summary")
    p.add_argument("--summary", type=Path, required=True)
    p.add_argument("--max-fail-ratio", type=float, default=0.05)
    p.add_argument("--max-total-retries", type=int, default=10)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(args.summary.read_text(encoding="utf-8"))
    results = payload.get("results", [])
    total = len(results)
    failed = sum(1 for item in results if item.get("status") != "PASS")
    retries = sum(max(0, int(item.get("attempts", 1)) - 1) for item in results)
    fail_ratio = (failed / total) if total else 0.0

    out = {
        "total_tasks": total,
        "failed_tasks": failed,
        "fail_ratio": fail_ratio,
        "total_retries": retries,
        "max_fail_ratio": args.max_fail_ratio,
        "max_total_retries": args.max_total_retries,
        "ok": fail_ratio <= args.max_fail_ratio and retries <= args.max_total_retries,
    }
    print(json.dumps(out, sort_keys=True))
    return 0 if out["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
