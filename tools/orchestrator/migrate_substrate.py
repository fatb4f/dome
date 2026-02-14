#!/usr/bin/env python
"""XA-09 deterministic migration bridge report generator."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def build_report(run_root: Path, run_id: str, out: Path, apply: bool) -> dict:
    run_dir = run_root / run_id
    files = sorted([p for p in run_dir.rglob("*.json") if "substrate" not in p.parts], key=lambda p: str(p))
    entries = [{"path": str(p), "sha256": _sha256(p)} for p in files]
    target = run_dir / "substrate" / "ledger" / "migration.report.json"
    report = {"run_id": run_id, "mode": "apply" if apply else "dry-run", "entries": entries, "target": str(target)}
    if apply:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate substrate migration report")
    p.add_argument("--run-root", type=Path, default=Path("ops/runtime/runs"))
    p.add_argument("--run-id", required=True)
    p.add_argument("--out", type=Path, default=Path("ops/runtime/migration.report.json"))
    p.add_argument("--apply", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.run_root, args.run_id, args.out, args.apply)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
