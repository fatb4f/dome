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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.checkpoint.exists():
        print(json.dumps({"ok": False, "reason": "checkpoint_missing"}, sort_keys=True))
        return 2

    payload = json.loads(args.checkpoint.read_text(encoding="utf-8"))
    processed = payload.get("processed_runs", [])
    count = len(processed) if isinstance(processed, list) else 0
    ok = count >= max(0, int(args.min_processed_runs))
    print(
        json.dumps(
            {"ok": ok, "processed_runs": count, "min_processed_runs": int(args.min_processed_runs)},
            sort_keys=True,
        )
    )
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

