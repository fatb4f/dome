import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.run_demo import run_demo  # noqa: E402
from tools.orchestrator.state_writer import replay_state_space_from_events  # noqa: E402


def test_replay_from_events_matches_state_space(tmp_path: Path) -> None:
    pre_contract = tmp_path / "contract.json"
    pre_contract.write_text(
        json.dumps(
            {
                "packet_id": "pkt-replay-001",
                "base_ref": "main",
                "budgets": {"iteration_budget": 2},
                "actions": {"test": ["python", "-c", "print('ok')"]},
                "plan_card": {"why": "replay", "what": "state determinism"},
            }
        ),
        encoding="utf-8",
    )

    run_root = tmp_path / "runs"
    event_log = tmp_path / "events.jsonl"
    summary = run_demo(
        pre_contract_path=pre_contract,
        run_root=run_root,
        state_space_path=ROOT / "ssot/examples/state.space.json",
        reason_codes_path=ROOT / "ssot/policy/reason.codes.json",
        event_log=event_log,
        otel_export=False,
    )
    run_id = summary["run_id"]
    run_dir = run_root / run_id

    state_original = json.loads((run_dir / "state.space.json").read_text(encoding="utf-8"))
    replayed = replay_state_space_from_events(
        state_space=json.loads((ROOT / "ssot/examples/state.space.json").read_text(encoding="utf-8")),
        work_queue=json.loads((run_dir / "work.queue.json").read_text(encoding="utf-8")),
        event_log=event_log,
        run_id=run_id,
        gate_decision=json.loads((run_dir / "gate" / "gate.decision.json").read_text(encoding="utf-8")),
        promotion_decision=json.loads((run_dir / "promotion" / "promotion.decision.json").read_text(encoding="utf-8")),
    )
    assert replayed["work_items"] == state_original["work_items"]
