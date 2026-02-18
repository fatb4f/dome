#!/usr/bin/env python
"""Fail CI when deprecated documentation paths are referenced in active docs."""

from __future__ import annotations

import argparse
from pathlib import Path


DEPRECATED_PATH = "doc/reviews/dome_review_pack_v2"


def find_deprecated_references(doc_root: Path) -> list[str]:
    hits: list[str] = []
    for path in sorted(doc_root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        if DEPRECATED_PATH in text:
            hits.append(str(path))
    return hits


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lint docs for deprecated path references")
    parser.add_argument("--doc-root", type=Path, default=Path("doc"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    hits = find_deprecated_references(args.doc_root)
    if hits:
        for hit in hits:
            print(f"deprecated reference found: {hit}")
        raise SystemExit(2)
    print("deprecated-path-lint: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
