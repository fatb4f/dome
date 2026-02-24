from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.run_plan_implement_verify import (  # noqa: E402
    _build_work_queue,
    _load_issue_body,
    run_plan_implement_verify,
)


def _args(tmp_path: Path, *, verify_cmd: str) -> argparse.Namespace:
    return argparse.Namespace(
        repo="example/repo",
        milestone_title="MVP PIV",
        milestone_description="",
        milestone_due_on="",
        issue_title="PIV live run",
        issue_body="Issue body",
        issue_body_file=None,
        issue_label=["automation"],
        implement_cmd=["echo implement-ok"],
        implement_cwd=tmp_path,
        verify_cmd=verify_cmd,
        verify_cwd=tmp_path,
        run_id="pkt-test-piv",
        run_root=tmp_path / "runs",
        state_space=ROOT / "ssot/examples/state.space.json",
        reason_codes=ROOT / "ssot/policy/reason.codes.json",
        event_log=tmp_path / "events.jsonl",
        risk_threshold=60,
        max_workers=3,
        max_retries=0,
        dry_run_plan=True,
    )


def test_build_work_queue_has_plan_implement_verify() -> None:
    out = _build_work_queue("pkt-abc", max_workers=2)
    assert out["run_id"] == "pkt-abc"
    assert [t["task_id"] for t in out["tasks"]] == [
        "pkt-abc-plan",
        "pkt-abc-implement",
        "pkt-abc-verify",
    ]
    assert out["tasks"][2]["dependencies"] == ["pkt-abc-implement"]


def test_issue_body_requires_single_source(tmp_path: Path) -> None:
    args = argparse.Namespace(issue_body="a", issue_body_file=tmp_path / "b.md")
    with pytest.raises(ValueError):
        _load_issue_body(args)


def test_run_plan_implement_verify_dry_run_pass(tmp_path: Path) -> None:
    args = _args(tmp_path, verify_cmd="python -c \"print('verify-ok')\"")
    result = run_plan_implement_verify(args)

    run_dir = args.run_root / args.run_id
    gate = json.loads((run_dir / "gate/gate.decision.json").read_text(encoding="utf-8"))
    promo = json.loads((run_dir / "promotion/promotion.decision.json").read_text(encoding="utf-8"))
    plan = json.loads((run_dir / "plan/plan.output.json").read_text(encoding="utf-8"))

    assert result["run_id"] == args.run_id
    assert gate["status"] == "APPROVE"
    assert promo["decision"] == "APPROVE"
    assert plan["issue"]["dry_run"] is True
    assert plan["milestone"]["dry_run"] is True


def test_run_plan_implement_verify_dry_run_verify_fail(tmp_path: Path) -> None:
    args = _args(tmp_path, verify_cmd="python -c \"import sys; sys.exit(2)\"")
    run_plan_implement_verify(args)

    run_dir = args.run_root / args.run_id
    gate = json.loads((run_dir / "gate/gate.decision.json").read_text(encoding="utf-8"))
    promo = json.loads((run_dir / "promotion/promotion.decision.json").read_text(encoding="utf-8"))

    assert gate["status"] == "REJECT"
    assert promo["decision"] == "REJECT"
