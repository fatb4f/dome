#!/usr/bin/env python
"""Audit drill utility for compliance evidence collection."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_audit_bundle(run_root: Path, run_id: str) -> dict[str, Any]:
    run_dir = run_root / run_id
    manifest_path = run_dir / "run.manifest.json"
    work_queue_path = run_dir / "work.queue.json"
    summary_path = run_dir / "summary.json"
    gate_path = run_dir / "gate" / "gate.decision.json"
    evidence_paths = sorted((run_dir / "evidence").glob("*.json"))

    bundle = {
        "run_id": run_id,
        "manifest_path": str(manifest_path),
        "work_queue_path": str(work_queue_path),
        "summary_path": str(summary_path),
        "gate_decision_path": str(gate_path),
        "hashes": {
            "work_queue_sha256": _sha256_path(work_queue_path),
            "summary_sha256": _sha256_path(summary_path),
            "gate_sha256": _sha256_path(gate_path),
            "manifest_sha256": _sha256_path(manifest_path),
        },
        "evidence_bundles": [
            {"path": str(path), "sha256": _sha256_path(path)} for path in evidence_paths
        ],
    }
    return bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect audit evidence bundle for a run")
    parser.add_argument("--run-root", type=Path, default=Path("ops/runtime/runs"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--out", type=Path, default=Path("ops/runtime/audit.bundle.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = collect_audit_bundle(args.run_root, args.run_id)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(str(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
