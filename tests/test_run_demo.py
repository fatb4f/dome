import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.run_demo import run_demo


def test_run_demo_end_to_end(tmp_path: Path) -> None:
    pre_contract = tmp_path / "contract.json"
    pre_contract.write_text(
        json.dumps(
            {
                "packet_id": "pkt-demo-001",
                "base_ref": "main",
                "budgets": {"iteration_budget": 2},
                "actions": {"test": ["python", "-c", "print('ok')"]},
                "plan_card": {"why": "demo", "what": "run mvp"},
            }
        ),
        encoding="utf-8",
    )

    run_root = tmp_path / "runs"
    state_space = ROOT / "ssot/examples/state.space.json"
    reason_codes = ROOT / "ssot/policy/reason.codes.json"
    event_log = tmp_path / "mcp_events.jsonl"

    summary = run_demo(
        pre_contract_path=pre_contract,
        run_root=run_root,
        state_space_path=state_space,
        reason_codes_path=reason_codes,
        event_log=event_log,
        risk_threshold=60,
        max_retries=1,
        otel_export=False,
    )

    assert Path(summary["work_queue_path"]).exists()
    assert Path(summary["summary_path"]).exists()
    assert Path(summary["gate_decision_path"]).exists()
    assert Path(summary["promotion_decision_path"]).exists()
    assert Path(summary["state_space_path"]).exists()

    gate = json.loads(Path(summary["gate_decision_path"]).read_text(encoding="utf-8"))
    promotion = json.loads(Path(summary["promotion_decision_path"]).read_text(encoding="utf-8"))
    state = json.loads(Path(summary["state_space_path"]).read_text(encoding="utf-8"))
    assert gate["status"] in {"APPROVE", "REJECT", "NEEDS_HUMAN"}
    assert any(note.startswith("verify_rc=") for note in gate.get("notes", []))
    assert promotion["decision"] in {"APPROVE", "REJECT", "NEEDS_HUMAN"}
    assert state["work_items"]
