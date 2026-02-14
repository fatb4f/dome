#!/usr/bin/env python
"""Run a live red->green demo with iterative implementation retries."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
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
from tools.orchestrator.io_utils import atomic_write_json  # noqa: E402
from tools.orchestrator.mcp_loop import EventBus, TOPIC_TASK_RESULT_RAW, replay_task_result_events  # noqa: E402
from tools.orchestrator.promote import (  # noqa: E402
    create_promotion_decision,
    persist_promotion_decision,
    validate_promotion_schema,
)
from tools.orchestrator.runtime_config import load_runtime_profile  # noqa: E402
from tools.orchestrator.security import assert_runtime_path  # noqa: E402
from tools.orchestrator.substrate_layout import ensure_substrate_layout  # noqa: E402
from tools.orchestrator.state_writer import update_state_space  # noqa: E402


def _sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_commit_sha() -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return proc.stdout.strip()
    except Exception:
        return "unknown"


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


def _label_for_event(task_id: str, attempt: int) -> str:
    if task_id.endswith("-plan"):
        return "im_helping"
    if task_id.endswith("-implement"):
        return "choo_choo" if attempt <= 1 else "wookiee_repair"
    if task_id.endswith("-verify"):
        return "verify_green"
    return "task_result"


def _build_iteration_loop_from_events(event_log: Path, run_id: str) -> list[dict[str, Any]]:
    iterations: list[dict[str, Any]] = []
    for event in replay_task_result_events(event_log=event_log, run_id=run_id):
        if event.get("topic") != TOPIC_TASK_RESULT_RAW:
            continue
        payload = event.get("payload", {})
        task_id = str(payload.get("task_id", "task-unknown"))
        attempt = int(payload.get("attempt", 1))
        iterations.append(
            {
                "iteration": len(iterations) + 1,
                "label": _label_for_event(task_id=task_id, attempt=attempt),
                "task_id": task_id,
                "status": payload.get("status"),
                "attempt": attempt,
                "reason_code": payload.get("reason_code"),
                "notes": payload.get("notes"),
                "event_id": event.get("event_id"),
            }
        )
    return iterations


def run_live_fix_demo(
    run_root: Path,
    state_space_path: Path,
    reason_codes_path: Path,
    event_log: Path,
    run_id: str = "pkt-dome-livefix-0001",
    max_retries: int = 2,
    risk_threshold: int = 60,
    worker_models: list[str] | None = None,
    otel_export: bool = False,
    runtime_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    run_dir = run_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    ensure_substrate_layout(run_root, run_id)
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
    atomic_write_json(run_dir / "work.queue.json", work_queue)

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
        worker_models=worker_models,
    )
    run_summary = harness.run(work_queue)
    implement_result = next(item for item in run_summary["results"] if item["task_id"].endswith("-implement"))
    verify_result = next(item for item in run_summary["results"] if item["task_id"].endswith("-verify"))
    plan_result = next(item for item in run_summary["results"] if item["task_id"].endswith("-plan"))

    iterations = _build_iteration_loop_from_events(event_log=event_log, run_id=run_id)
    if not iterations:
        iterations = [
            {
                "iteration": 1,
                "label": "im_helping",
                "task_id": plan_result["task_id"],
                "status": plan_result["status"],
                "attempt": 1,
                "reason_code": plan_result.get("reason_code"),
                "notes": plan_result.get("notes"),
                "event_id": None,
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
                    "event_id": None,
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
                "event_id": None,
            }
        )
    loop_path = run_dir / "iteration.loop.json"
    atomic_write_json(loop_path, {"run_id": run_id, "iterations": iterations})

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
    atomic_write_json(state_out_path, updated_state)

    input_hashes = {
        "work_queue_sha256": _sha256_path(run_dir / "work.queue.json"),
        "state_space_sha256": _sha256_path(state_space_path),
        "reason_codes_sha256": _sha256_path(reason_codes_path),
    }

    manifest = {
        "version": "0.2.0",
        "run_id": run_id,
        "inputs": {
            "workbench_path": str(workbench),
            "work_queue_sha256": input_hashes["work_queue_sha256"],
            "input_hashes": input_hashes,
        },
        "commands": ["implementers", "checkers", "promote", "state_writer"],
        "refs": {
            "policy_ref": "ssot/policy/reason.codes.json",
            "pattern_ref": (runtime_profile or {}).get("pattern_catalog_ref"),
            "packet_contract_ref": "live-fix-demo",
        },
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
            "repo_commit_sha": _git_commit_sha(),
            "tool_versions": {"python": sys.version.split(" ")[0]},
            "environment_fingerprint": {
                "platform": platform.platform(),
                "python_implementation": platform.python_implementation(),
                "cwd": os.getcwd(),
            },
            "trace_source": trace_source,
            "runtime_profile": (runtime_profile or {}).get("name"),
            "runtime_pattern": (runtime_profile or {}).get("pattern"),
            "max_retries": max_retries,
            "risk_threshold": risk_threshold,
            "worker_models": worker_models or ["gpt-5.3", "gpt-5.2"],
        },
    }
    manifest_path = run_dir / "run.manifest.json"
    atomic_write_json(manifest_path, manifest)

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
    parser.add_argument("--runtime-config", type=Path)
    parser.add_argument("--profile")
    parser.add_argument("--worker-models")
    parser.add_argument("--run-id", default="pkt-dome-livefix-0001")
    parser.add_argument("--max-retries", type=int)
    parser.add_argument("--risk-threshold", type=int)
    parser.add_argument("--otel-export", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    assert_runtime_path(args.run_root, ROOT, "--run-root")
    assert_runtime_path(args.event_log, ROOT, "--event-log")
    runtime_profile = load_runtime_profile(
        runtime_config_path=args.runtime_config,
        profile=args.profile,
        schema_path=ROOT / "ssot/schemas/runtime.config.schema.json",
    )
    models_cfg = runtime_profile.get("models", {}).get("implementers", [])
    worker_models = (
        [item.strip() for item in args.worker_models.split(",") if item.strip()]
        if isinstance(args.worker_models, str) and args.worker_models.strip()
        else list(models_cfg)
    )
    if not worker_models:
        worker_models = ["gpt-5.3", "gpt-5.2"]
    budget_cfg = runtime_profile.get("budgets", {})
    risk_threshold = int(args.risk_threshold) if args.risk_threshold is not None else int(budget_cfg.get("risk_threshold", 60))
    max_retries = int(args.max_retries) if args.max_retries is not None else int(budget_cfg.get("max_retries", 2))

    summary = run_live_fix_demo(
        run_root=args.run_root,
        state_space_path=args.state_space,
        reason_codes_path=args.reason_codes,
        event_log=args.event_log,
        run_id=args.run_id,
        max_retries=max_retries,
        risk_threshold=risk_threshold,
        worker_models=worker_models,
        otel_export=args.otel_export,
        runtime_profile=runtime_profile,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
