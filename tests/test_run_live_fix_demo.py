import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.run_live_fix_demo import run_live_fix_demo


def test_run_live_fix_demo_iterates_and_recovers(tmp_path: Path) -> None:
    run_root = tmp_path / "runs"
    summary = run_live_fix_demo(
        run_root=run_root,
        state_space_path=ROOT / "ssot/examples/state.space.json",
        reason_codes_path=ROOT / "ssot/policy/reason.codes.json",
        event_log=tmp_path / "mcp_events.jsonl",
        run_id="pkt-livefix-test-001",
        max_retries=2,
        otel_export=False,
    )

    run_dir = run_root / "pkt-livefix-test-001"
    assert Path(summary["workbench_path"]).exists()
    assert Path(summary["work_queue_path"]).exists()
    assert Path(summary["summary_path"]).exists()
    assert Path(summary["gate_decision_path"]).exists()
    assert Path(summary["promotion_decision_path"]).exists()
    assert Path(summary["state_space_path"]).exists()
    assert Path(summary["run_manifest_path"]).exists()
    assert Path(summary["iteration_loop_path"]).exists()

    run_summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    implement_result = next(item for item in run_summary["results"] if item["task_id"].endswith("-implement"))
    assert implement_result["status"] == "PASS"
    assert implement_result["attempts"] == 2
    assert Path(implement_result["attempt_history_path"]).exists()

    gate = json.loads((run_dir / "gate" / "gate.decision.json").read_text(encoding="utf-8"))
    promotion = json.loads((run_dir / "promotion" / "promotion.decision.json").read_text(encoding="utf-8"))
    assert gate["status"] == "APPROVE"
    assert promotion["decision"] == "APPROVE"

    loop = json.loads((run_dir / "iteration.loop.json").read_text(encoding="utf-8"))
    labels = [entry["label"] for entry in loop["iterations"]]
    assert labels[:3] == ["im_helping", "choo_choo", "wookiee_repair"]
