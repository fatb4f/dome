#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.codex.migration_inventory import collect_callsites


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    repo_root = ROOT
    register_path = repo_root / "doc/milestone_domed/m5/m5_tool_migration_register.csv"
    register_rows = _load_csv(register_path)

    register_ids = {row["callsite_id"] for row in register_rows}
    observed_ids = {row["callsite_id"] for row in collect_callsites(repo_root)}
    if register_ids != observed_ids:
        only_register = sorted(register_ids - observed_ids)
        only_observed = sorted(observed_ids - register_ids)
        raise SystemExit(
            "subprocess policy mismatch:\n"
            f"- register_only={only_register}\n"
            f"- observed_only={only_observed}"
        )

    forbidden_production_local = [
        row["callsite_id"]
        for row in register_rows
        if row["mode"] == "production" and row["current_transport"] == "local_subprocess"
    ]
    if forbidden_production_local:
        raise SystemExit(
            "forbidden production local subprocess callsites: "
            + ", ".join(sorted(forbidden_production_local))
        )

    # Explicit safety rule: primary CLI entrypoint must not directly spawn subprocess workloads.
    forbidden_prefix = "tools/codex/dome_cli.py:"
    dome_cli_calls = sorted(cid for cid in observed_ids if cid.startswith(forbidden_prefix))
    if dome_cli_calls:
        raise SystemExit(f"forbidden subprocess in dome_cli entrypoint: {dome_cli_calls}")

    print("subprocess policy check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
