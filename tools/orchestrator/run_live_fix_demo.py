#!/usr/bin/env python
"""Run a live red->green demo with iterative implementation retries."""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.checkers import (  # noqa: E402
    create_gate_decision,
    persist_gate_decision,
    validate_gate_decision_schema,
)
from tools.orchestrator.implementers import ImplementerHarness  # noqa: E402
from tools.orchestrator.mcp_loop import EventBus  # noqa: E402
from tools.orchestrator.promote import (  # noqa: E402
    create_promotion_decision,
    persist_promotion_decision,
    validate_promotion_schema,
)
from tools.orchestrator.state_writer import update_state_space  # noqa: E402


def _sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_buggy_project(workbench: Path) -> None:
    src_dir = workbench / "src"
    tests_dir = workbench / "tests"
    src_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "calculator.py").write_text(
        "def add(a: int, b: int) -> int:\n"
        "    # Deliberate bug for red->green demo.\n"
        "    return a - b\n",
        encoding="utf-8",
    )
    (tests_dir / "test_calculator.py").write_text(
        "import sys\n"
        "from pathlib import Path\n\n"
        "ROOT = Path(__file__).resolve().parents[1]\n"
        "if str(ROOT / 'src') not in sys.path:\n"
        "    sys.path.insert(0, str(ROOT / 'src'))\n\n"
        "from calculator import add\n\n"
        "def test_add_basic() -> None:\n"
        "    assert add(2, 3) == 5\n",
        encoding="utf-8",
    )


def _apply_fix(workbench: Path) -> None:
    (workbench / "src" / "calculator.py").write_text(
        "def add(a: int, b: int) -> int:\n"
        "    return a + b\n",
        encoding="utf-8",
    )


def _run_tests(workbench: Path) -> tuple[int, str]:
    cmd = [sys.executable, "-m", "pytest", "-q", str(workbench / "tests")]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    output = "\n".join(filter(None, [proc.stdout.strip(), proc.stderr.strip()]))
    return int(proc.returncode), output[:4000]


def run_live_fix_demo(
    run_root: Path,
    state_space_path: Path,
    reason_codes_path: Path,
    event_log: Path,
    run_id: str = "pkt-dome-livefix-0001",
    max_retries: int = 2,
    risk_threshold: int = 60,
    otel_export: bool = False,
) -> dict[str, Any]:
    run_dir = run_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    workbench = run_dir / "workbench"
    _write_buggy_project(workbench)

    work_queue = {
        "version": "0.2.0",
        "run_id": run_id,
        "base_ref": "main",
        "max_workers": 2,
        "tasks": [
            {
                "task_id": f"{run_id}-plan",
                "goal": "Reproduce failure in workbench tests",
                "status": "QUEUED",
                "dependencies": [],
            },
            {
                "task_id": f"{run_id}-implement",
                "goal": "Implement fix iteratively until tests pass",
                "status": "QUEUED",
                "dependencies": [f"{run_id}-plan"],
            },
            {
                "task_id": f"{run_id}-verify",
                "goal": "Verify tests remain green",
                "status": "QUEUED",
                "dependencies": [f"{run_id}-implement"],
            },
        ],
    }
    (run_dir / "work.queue.json").write_text(json.dumps(work_queue, indent=2), encoding="utf-8")

    attempts: dict[str, int] = {}

    def worker(task: dict[str, Any]) -> dict[str, Any]:
        task_id = str(task["task_id"])
        attempts[task_id] = attempts.get(task_id, 0) + 1
        if task_id.endswith("-plan"):
            rc, out = _run_tests(workbench)
            if rc == 0:
                return {
                    "task_id": task_id,
                    "status": "FAIL",
                    "reason_code": "EXEC.NONZERO_EXIT",
                    "notes": "expected initial failing test but tests already passed",
                    "worker_model": "gpt-5.3",
                }
            return {
                "task_id": task_id,
                "status": "PASS",
                "notes": f"reproduced failing test: {out}",
                "worker_model": "gpt-5.3",
            }
        if task_id.endswith("-implement"):
            # First attempt reports transient failure after observing red state.
            if attempts[task_id] == 1:
                rc, out = _run_tests(workbench)
                return {
                    "task_id": task_id,
                    "status": "FAIL" if rc != 0 else "PASS",
                    "transient": True,
                    "reason_code": "TRANSIENT.FIRST_ATTEMPT",
                    "notes": f"first implement attempt left failing state: {out}",
                    "worker_model": "gpt-5.2",
                }
            _apply_fix(workbench)
            rc, out = _run_tests(workbench)
            return {
                "task_id": task_id,
                "status": "PASS" if rc == 0 else "FAIL",
                "reason_code": None if rc == 0 else "EXEC.NONZERO_EXIT",
                "notes": "applied fix and reran tests: " + out,
                "worker_model": "gpt-5.2",
            }
        if task_id.endswith("-verify"):
            rc, out = _run_tests(workbench)
            return {
                "task_id": task_id,
                "status": "PASS" if rc == 0 else "FAIL",
                "reason_code": None if rc == 0 else "VERIFY.TEST_FAILURE",
                "notes": out,
                "worker_model": "gpt-5.3",
            }
        return {"task_id": task_id, "status": "FAIL", "reason_code": "EXEC.NONZERO_EXIT"}

    bus = EventBus(event_log=event_log)
    harness = ImplementerHarness(
        bus=bus,
        run_root=run_root,
        worker_fn=worker,
        max_retries=max_retries,
    )
    run_summary = harness.run(work_queue)
    implement_result = next(item for item in run_summary["results"] if item["task_id"].endswith("-implement"))
    verify_result = next(item for item in run_summary["results"] if item["task_id"].endswith("-verify"))
    plan_result = next(item for item in run_summary["results"] if item["task_id"].endswith("-plan"))

    iterations = [
        {
            "iteration": 1,
            "label": "im_helping",
            "task_id": plan_result["task_id"],
            "status": plan_result["status"],
            "attempt": 1,
            "reason_code": plan_result.get("reason_code"),
            "notes": plan_result.get("notes"),
        }
    ]
    for attempt in implement_result.get("attempt_history", []):
        iterations.append(
            {
                "iteration": len(iterations) + 1,
                "label": "choo_choo" if attempt.get("attempt") == 1 else "wookiee_repair",
                "task_id": implement_result["task_id"],
                "status": attempt.get("status"),
                "attempt": attempt.get("attempt"),
                "reason_code": attempt.get("reason_code"),
                "notes": attempt.get("notes"),
            }
        )
    iterations.append(
        {
            "iteration": len(iterations) + 1,
            "label": "verify_green",
            "task_id": verify_result["task_id"],
            "status": verify_result["status"],
            "attempt": 1,
            "reason_code": verify_result.get("reason_code"),
            "notes": verify_result.get("notes"),
        }
    )
    loop_path = run_dir / "iteration.loop.json"
    loop_path.write_text(json.dumps({"run_id": run_id, "iterations": iterations}, indent=2), encoding="utf-8")

    reason_codes_payload = json.loads(reason_codes_path.read_text(encoding="utf-8"))
    reason_codes_catalog = {item["code"] for item in reason_codes_payload.get("codes", [])}
    verify_cmd = f"{shlex.quote(sys.executable)} -m pytest -q {shlex.quote(str(workbench / 'tests'))}"
    gate_decision, trace_source = create_gate_decision(
        run_summary=run_summary,
        reason_codes_catalog=reason_codes_catalog,
        verify_command=verify_cmd,
        risk_threshold=risk_threshold,
        otel_export=otel_export,
    )
    validate_gate_decision_schema(gate_decision, ROOT / "ssot/schemas/gate.decision.schema.json")
    gate_path = persist_gate_decision(run_root, run_id, gate_decision)

    promotion = create_promotion_decision(gate_decision=gate_decision, max_risk=risk_threshold)
    validate_promotion_schema(promotion, ROOT / "ssot/schemas/promotion.decision.schema.json")
    promotion_path = persist_promotion_decision(run_root, run_id, promotion)

    state_space = json.loads(state_space_path.read_text(encoding="utf-8"))
    updated_state = update_state_space(
        state_space=state_space,
        work_queue=work_queue,
        run_summary=run_summary,
        gate_decision=gate_decision,
        promotion_decision=promotion,
    )
    state_out_path = run_dir / "state.space.json"
    state_out_path.write_text(json.dumps(updated_state, indent=2), encoding="utf-8")

    manifest = {
        "version": "0.2.0",
        "run_id": run_id,
        "inputs": {
            "workbench_path": str(workbench),
            "work_queue_sha256": _sha256_path(run_dir / "work.queue.json"),
        },
        "commands": ["implementers", "checkers", "promote", "state_writer"],
        "artifacts": {
            "work_queue_path": str(run_dir / "work.queue.json"),
            "summary_path": str(run_dir / "summary.json"),
            "gate_decision_path": str(gate_path),
            "promotion_decision_path": str(promotion_path),
            "state_space_path": str(state_out_path),
            "workbench_path": str(workbench),
            "iteration_loop_path": str(loop_path),
        },
        "runtime": {
            "python_version": sys.version.split(" ")[0],
            "trace_source": trace_source,
        },
    }
    manifest_path = run_dir / "run.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {
        "run_id": run_id,
        "trace_source": trace_source,
        "work_queue_path": str(run_dir / "work.queue.json"),
        "summary_path": str(run_dir / "summary.json"),
        "gate_decision_path": str(gate_path),
        "promotion_decision_path": str(promotion_path),
        "state_space_path": str(state_out_path),
        "run_manifest_path": str(manifest_path),
        "workbench_path": str(workbench),
        "iteration_loop_path": str(loop_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run live iterative fix demo")
    parser.add_argument("--run-root", type=Path, default=Path("ops/runtime/runs"))
    parser.add_argument("--state-space", type=Path, default=Path("ssot/examples/state.space.json"))
    parser.add_argument("--reason-codes", type=Path, default=Path("ssot/policy/reason.codes.json"))
    parser.add_argument("--event-log", type=Path, default=Path("ops/runtime/mcp_events.jsonl"))
    parser.add_argument("--run-id", default="pkt-dome-livefix-0001")
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--risk-threshold", type=int, default=60)
    parser.add_argument("--otel-export", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_live_fix_demo(
        run_root=args.run_root,
        state_space_path=args.state_space,
        reason_codes_path=args.reason_codes,
        event_log=args.event_log,
        run_id=args.run_id,
        max_retries=args.max_retries,
        risk_threshold=args.risk_threshold,
        otel_export=args.otel_export,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
