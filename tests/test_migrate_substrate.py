import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.migrate_substrate import build_report


def test_migration_bridge_report(tmp_path: Path) -> None:
    run_dir = tmp_path / "r1"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
    out = tmp_path / "report.json"
    report = build_report(tmp_path, "r1", out, apply=True)
    assert report["entries"]
    target = run_dir / "substrate" / "ledger" / "migration.report.json"
    assert target.exists()
