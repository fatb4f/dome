import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator import planner


def test_pre_contract_to_work_queue_basic_mapping() -> None:
    contract = {
        "packet_id": "pkt-v2-migrate-0002-runner-cutover",
        "base_ref": "origin/main",
        "budgets": {"iteration_budget": 3},
        "actions": {"test": ["pytest", "-q"]},
        "plan_card": {"why": "Cut over runner", "what": "Port runner components"},
    }

    out = planner.pre_contract_to_work_queue(contract)
    assert out["run_id"] == "pkt-v2-migrate-0002-runner-cutover"
    assert out["base_ref"] == "origin/main"
    assert out["max_workers"] == 3
    assert [task["status"] for task in out["tasks"]] == ["QUEUED", "QUEUED", "QUEUED"]
    assert out["tasks"][0]["task_id"].endswith("-plan")
    assert out["tasks"][1]["dependencies"] == [out["tasks"][0]["task_id"]]
    assert out["tasks"][2]["task_id"].endswith("-verify")


def test_pre_contract_missing_packet_id_raises() -> None:
    with pytest.raises(ValueError):
        planner.pre_contract_to_work_queue({"base_ref": "main"})


def test_planner_cli_writes_output(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.json"
    out_path = tmp_path / "work.queue.json"
    contract_path.write_text(
        json.dumps(
            {
                "packet_id": "pkt-test-001",
                "base_ref": "main",
                "budgets": {"iteration_budget": 2},
                "actions": {"test": ["pytest", "-q"]},
                "plan_card": {"why": "test", "what": "implement"},
            }
        ),
        encoding="utf-8",
    )

    import sys

    old_argv = sys.argv
    try:
        sys.argv = [
            "planner.py",
            "--pre-contract",
            str(contract_path),
            "--out",
            str(out_path),
        ]
        rc = planner.main()
    finally:
        sys.argv = old_argv

    assert rc == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "pkt-test-001"
    assert payload["tasks"]


def test_planner_detects_dependency_cycle() -> None:
    with pytest.raises(ValueError, match="dependency cycle"):
        planner.validate_task_graph(
            [
                {"task_id": "a", "dependencies": ["b"]},
                {"task_id": "b", "dependencies": ["a"]},
            ]
        )
