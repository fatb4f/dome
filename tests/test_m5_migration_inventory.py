from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.codex.migration_inventory import collect_callsites

ALLOWED_CLASSES = {"MIGRATE_NOW", "ADAPTER_REQUIRED", "DEPRECATE_REMOVE", "KEEP_LOCAL"}


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_register_matches_generated_inventory_callsites() -> None:
    register_path = ROOT / "doc/milestone_domed/m5/m5_tool_migration_register.csv"
    register_rows = _load_csv(register_path)
    register_ids = {r["callsite_id"] for r in register_rows}

    generated = collect_callsites(ROOT)
    generated_ids = {r["callsite_id"] for r in generated}

    assert register_ids == generated_ids


def test_register_migration_classes_are_valid() -> None:
    register_path = ROOT / "doc/milestone_domed/m5/m5_tool_migration_register.csv"
    register_rows = _load_csv(register_path)
    assert register_rows
    for row in register_rows:
        assert row["migration_class"] in ALLOWED_CLASSES

