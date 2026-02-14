#!/usr/bin/env python
"""Minimal DLQ reprocessing utility."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Reprocess DLQ entries")
    p.add_argument("--run-root", type=Path, default=Path("ops/runtime/runs"))
    p.add_argument("--run-id", required=True)
    p.add_argument("--out", type=Path, default=Path("ops/runtime/dlq.reprocess.json"))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    dlq_dir = args.run_root / args.run_id / "dlq"
    results = []
    for path in sorted(dlq_dir.glob("*.dlq.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        results.append(
            {
                "path": str(path),
                "task_id": payload.get("task_id"),
                "reason_code": payload.get("reason_code"),
                "attempts": payload.get("attempts"),
                "action": "manual_review_required",
            }
        )

    out = {
        "run_id": args.run_id,
        "dlq_count": len(results),
        "entries": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(str(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
