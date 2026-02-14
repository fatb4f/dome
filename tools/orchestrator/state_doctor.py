#!/usr/bin/env python
"""Validate substrate layout compatibility directories."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow direct script execution.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.substrate_layout import REQUIRED_DIRS


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate substrate layout")
    p.add_argument("--run-root", type=Path, default=Path("ops/runtime/runs"))
    p.add_argument("--run-id", required=True)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    base = args.run_root / args.run_id / "substrate"
    missing = [item for item in REQUIRED_DIRS if not (base / item).is_dir()]
    out = {"run_id": args.run_id, "base": str(base), "missing": missing, "ok": not missing}
    print(json.dumps(out, sort_keys=True))
    return 0 if out["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
