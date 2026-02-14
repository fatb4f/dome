#!/usr/bin/env python
"""XA-10 pattern catalog ingestion pipeline."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def _latest_commit(repo: str) -> str:
    try:
        out = subprocess.run([
            "gh", "api", f"repos/{repo}/commits?per_page=1", "--jq", ".[0].sha"
        ], check=True, text=True, capture_output=True)
        return out.stdout.strip()
    except Exception:
        return "unknown"


def ingest(seed_path: Path, out_path: Path) -> dict:
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    repo = str(seed.get("repo", "nibzard/awesome-agentic-patterns"))
    commit = _latest_commit(repo)
    payload = {
        "version": "0.2.0",
        "source": {
            "repo": repo,
            "commit": commit,
            "fetched_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        },
        "patterns": list(seed.get("patterns", [])),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ingest awesome-agentic-patterns into local catalog")
    p.add_argument("--seed", type=Path, default=Path("ssot/sources/awesome_agentic_patterns.seed.json"))
    p.add_argument("--out", type=Path, default=Path("ssot/catalog/pattern.catalog.v1.json"))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    payload = ingest(args.seed, args.out)
    print(json.dumps(payload["source"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
