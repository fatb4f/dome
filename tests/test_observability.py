import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.mcp_loop import load_event_envelopes  # noqa: E402
from tools.orchestrator.run_demo import run_demo  # noqa: E402


def test_golden_telemetry_fields_and_correlation(tmp_path: Path) -> None:
    pre_contract = tmp_path / "contract.json"
    pre_contract.write_text(
        json.dumps(
            {
                "packet_id": "pkt-obs-001",
                "base_ref": "main",
                "budgets": {"iteration_budget": 2},
                "actions": {"test": ["python", "-c", "print('ok')"]},
                "plan_card": {"why": "observability", "what": "golden telemetry"},
            }
        ),
        encoding="utf-8",
    )
    run_root = tmp_path / "runs"
    event_log = tmp_path / "events.jsonl"
    out = run_demo(
        pre_contract_path=pre_contract,
        run_root=run_root,
        state_space_path=ROOT / "ssot/examples/state.space.json",
        reason_codes_path=ROOT / "ssot/policy/reason.codes.json",
        event_log=event_log,
        otel_export=False,
    )
    run_id = out["run_id"]
    summary = json.loads(Path(out["summary_path"]).read_text(encoding="utf-8"))
    events = load_event_envelopes(event_log=event_log, run_id=run_id)
    assert events
    for event in events:
        for key in ("schema_version", "sequence", "event_id", "ts", "topic", "run_id", "payload"):
            assert key in event

    for item in summary["results"]:
        evidence = json.loads(Path(item["evidence_bundle_path"]).read_text(encoding="utf-8"))
        signals = evidence["signals"]
        for field in (
            "run.id",
            "task.id",
            "task.status",
            "task.attempts",
            "task.reason_code",
            "task.worker_model",
            "task.duration_ms",
        ):
            assert field in signals
        assert signals["run.id"] == run_id
        assert signals["task.id"] == item["task_id"]
