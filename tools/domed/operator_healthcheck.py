#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.codex.domed_client import DomedClient, DomedClientConfig
from tools.domed.endpoints import default_client_endpoint


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="domed operator healthcheck")
    p.add_argument("--endpoint")
    p.add_argument("--profile", default="work")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    endpoint = args.endpoint or default_client_endpoint()
    client = DomedClient(DomedClientConfig(endpoint=endpoint))
    health = client.health()
    caps = client.list_capabilities(args.profile)
    out = {
        "endpoint": endpoint,
        "health_ok": bool(health.status.ok),
        "daemon_version": str(getattr(health, "daemon_version", "")),
        "capability_count": len(getattr(caps, "capabilities", [])),
        "capabilities_ok": bool(caps.status.ok),
    }
    print(json.dumps(out, sort_keys=True))
    return 0 if out["health_ok"] and out["capabilities_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
