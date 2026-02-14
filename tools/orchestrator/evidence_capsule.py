#!/usr/bin/env python
"""XA-04 telemetry bundle to evidence capsule adapter."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def to_capsule(payload: dict[str, Any]) -> dict[str, Any]:
    otel = payload.get("otel", {})
    return {
        "version": "0.2.0",
        "trace": {
            "trace_id_hex": otel.get("trace_id_hex", ""),
            "span_id_hex": otel.get("span_id_hex", ""),
            "backend": otel.get("backend", ""),
            "run_id": otel.get("run_id", ""),
        },
        "signals": dict(payload.get("signals", {})),
        "artifacts": list(payload.get("artifacts", [])),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Translate evidence bundle to canonical capsule")
    p.add_argument("--in", dest="in_path", type=Path, required=True)
    p.add_argument("--out", dest="out_path", type=Path, required=True)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(args.in_path.read_text(encoding="utf-8"))
    out = to_capsule(payload)
    args.out_path.parent.mkdir(parents=True, exist_ok=True)
    args.out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(str(args.out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
