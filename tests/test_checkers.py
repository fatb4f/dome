import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator import checkers


def _catalog() -> set[str]:
    payload = json.loads((ROOT / "ssot/examples/reason.codes.json").read_text(encoding="utf-8"))
    return {item["code"] for item in payload["codes"]}


def _summary(statuses: list[str], risk_hint: int = 20) -> dict:
    return {
        "run_id": "wave-check-001",
        "results": [
            {"task_id": f"t{i}", "status": status, "risk_score_hint": risk_hint}
            for i, status in enumerate(statuses, start=1)
        ],
    }


def test_checker_rejects_on_deterministic_failure() -> None:
    decision, _ = checkers.create_gate_decision(
        run_summary=_summary(["FAIL"]),
        reason_codes_catalog=_catalog(),
    )
    assert decision["status"] == "REJECT"
    assert "EXEC.NONZERO_EXIT" in decision["reason_codes"]


def test_checker_approves_when_low_risk_and_pass() -> None:
    decision, _ = checkers.create_gate_decision(
        run_summary=_summary(["PASS", "PASS"], risk_hint=25),
        reason_codes_catalog=_catalog(),
        risk_threshold=60,
    )
    assert decision["status"] == "APPROVE"
    assert decision["risk_score"] < 60


def test_checker_needs_human_when_high_risk() -> None:
    decision, _ = checkers.create_gate_decision(
        run_summary=_summary(["PASS", "PASS"], risk_hint=80),
        reason_codes_catalog=_catalog(),
        risk_threshold=60,
    )
    assert decision["status"] == "NEEDS_HUMAN"
    assert "POLICY.NEEDS_HUMAN" in decision["reason_codes"]


def test_checker_persists_gate_decision_file(tmp_path: Path) -> None:
    run_root = tmp_path / "runs"
    run_id = "wave-check-file"
    (run_root / run_id).mkdir(parents=True, exist_ok=True)
    decision, _ = checkers.create_gate_decision(
        run_summary={"run_id": run_id, "results": [{"task_id": "t1", "status": "PASS"}]},
        reason_codes_catalog=_catalog(),
    )
    out_path = checkers.persist_gate_decision(run_root, run_id, decision)
    assert out_path.exists()
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == run_id

