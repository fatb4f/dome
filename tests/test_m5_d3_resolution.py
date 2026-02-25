from __future__ import annotations

import csv
from pathlib import Path


def test_no_adapter_required_rows_remain() -> None:
    root = Path(__file__).resolve().parents[1]
    register = root / "doc/milestone_domed/m5/m5_tool_migration_register.csv"
    with register.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    unresolved = [r["callsite_id"] for r in rows if r["migration_class"] == "ADAPTER_REQUIRED"]
    assert unresolved == []

