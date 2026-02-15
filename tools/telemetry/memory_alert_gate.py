#!/usr/bin/env python
"""Alert gate for long-horizon memory daemon checkpoint health."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate memory daemon checkpoint health")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--min-processed-runs", type=int, default=1)
    parser.add_argument("--min-binder-derived-rows", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.checkpoint.exists():
        print(json.dumps({"ok": False, "reason": "checkpoint_missing"}, sort_keys=True))
        return 2

    payload = json.loads(args.checkpoint.read_text(encoding="utf-8"))
    processed = payload.get("processed_runs", [])
    count = len(processed) if isinstance(processed, list) else 0
    binder_count = int(payload.get("last_binder_derived_rows", 0))
    ok = count >= max(0, int(args.min_processed_runs)) and binder_count >= max(
        0, int(args.min_binder_derived_rows)
    )
    print(
        json.dumps(
            {
                "ok": ok,
                "processed_runs": count,
                "min_processed_runs": int(args.min_processed_runs),
                "binder_derived_rows": binder_count,
                "min_binder_derived_rows": int(args.min_binder_derived_rows),
            },
            sort_keys=True,
        )
    )
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
