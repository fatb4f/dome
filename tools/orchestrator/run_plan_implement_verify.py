#!/usr/bin/env python
"""Run a non-demo PLAN -> IMPLEMENT -> VERIFY loop with GitHub-tracked PLAN outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
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
from tools.orchestrator.mcp_loop import EventBus, load_control_events, materialize_control_ledger  # noqa: E402
from tools.orchestrator.promote import (  # noqa: E402
    create_promotion_decision,
    persist_promotion_decision,
    validate_promotion_schema,
)
from tools.orchestrator.security import assert_runtime_path  # noqa: E402
from tools.orchestrator.state_writer import update_state_space  # noqa: E402


def _utc_ts() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _run_cmd(command: str, cwd: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        ["bash", "-lc", command],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )
    out = "\n".join(x for x in [proc.stdout.strip(), proc.stderr.strip()] if x)
    return int(proc.returncode), out


def _gh_api(method: str, endpoint: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    cmd = ["gh", "api", "-X", method.upper(), endpoint]
    stdin = None
    if payload is not None:
        cmd.extend(["--input", "-"])
        stdin = json.dumps(payload)
    proc = subprocess.run(cmd, input=stdin, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"gh api failed ({endpoint}): {proc.stderr.strip() or proc.stdout.strip()}")
    data = proc.stdout.strip()
    return json.loads(data) if data else {}


def ensure_milestone(
    *,
    repo: str,
    title: str,
    description: str | None,
    due_on: str | None,
    dry_run: bool,
) -> dict[str, Any]:
    if dry_run:
        return {
            "number": 0,
            "title": title,
            "html_url": f"https://github.com/{repo}/milestone/dry-run",
            "state": "open",
            "created": False,
            "dry_run": True,
        }

    items = _gh_api("GET", f"repos/{repo}/milestones?state=all&per_page=100")
    if not isinstance(items, list):
        raise RuntimeError("unexpected milestone list response")
    for item in items:
        if str(item.get("title", "")) == title:
            return {
                "number": int(item["number"]),
                "title": str(item.get("title", title)),
                "html_url": str(item.get("html_url", "")),
                "state": str(item.get("state", "open")),
                "created": False,
            }

    payload: dict[str, Any] = {"title": title}
    if description:
        payload["description"] = description
    if due_on:
        payload["due_on"] = due_on
    item = _gh_api("POST", f"repos/{repo}/milestones", payload)
    return {
        "number": int(item["number"]),
        "title": str(item.get("title", title)),
        "html_url": str(item.get("html_url", "")),
        "state": str(item.get("state", "open")),
        "created": True,
    }


def create_issue(
    *,
    repo: str,
    title: str,
    body: str,
    milestone_number: int,
    labels: list[str],
    dry_run: bool,
) -> dict[str, Any]:
    if dry_run:
        return {
            "number": 0,
            "title": title,
            "html_url": f"https://github.com/{repo}/issues/dry-run",
            "state": "open",
            "dry_run": True,
        }

    payload: dict[str, Any] = {
        "title": title,
        "body": body,
        "milestone": int(milestone_number),
    }
    if labels:
        payload["labels"] = labels
    item = _gh_api("POST", f"repos/{repo}/issues", payload)
    return {
        "number": int(item["number"]),
        "title": str(item.get("title", title)),
        "html_url": str(item.get("html_url", "")),
        "state": str(item.get("state", "open")),
    }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_issue_body(args: argparse.Namespace) -> str:
    if args.issue_body and args.issue_body_file:
        raise ValueError("use only one of --issue-body or --issue-body-file")
    if args.issue_body_file:
        return args.issue_body_file.read_text(encoding="utf-8")
    if args.issue_body:
        return args.issue_body
    raise ValueError("issue body required (--issue-body or --issue-body-file)")


def _build_work_queue(run_id: str, max_workers: int) -> dict[str, Any]:
    return {
        "artifact_kind": "dome.work.queue/v0.2",
        "version": "0.2.0",
        "run_id": run_id,
        "base_ref": "main",
        "policy_ref": "ssot/policy/reason.codes.json",
        "pattern_ref": "ssot/examples/profile.catalog.map.json#plan-implement-verify",
        "max_workers": max(1, int(max_workers)),
        "tasks": [
            {
                "task_id": f"{run_id}-plan",
                "goal": "Create/resolve GitHub milestone and issue",
                "status": "QUEUED",
                "dependencies": [],
            },
            {
                "task_id": f"{run_id}-implement",
                "goal": "Execute real implement commands",
                "status": "QUEUED",
                "dependencies": [f"{run_id}-plan"],
            },
            {
                "task_id": f"{run_id}-verify",
                "goal": "Run verification command",
                "status": "QUEUED",
                "dependencies": [f"{run_id}-implement"],
            },
        ],
    }


def run_plan_implement_verify(args: argparse.Namespace) -> dict[str, Any]:
    run_id = args.run_id or f"pkt-plan-implement-verify-{_utc_ts()}"
    run_root = args.run_root
    run_dir = run_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    issue_body = _load_issue_body(args)
    work_queue = _build_work_queue(run_id=run_id, max_workers=args.max_workers)
    atomic_write_json(run_dir / "work.queue.json", work_queue)

    plan_dir = run_dir / "plan"
    impl_dir = run_dir / "implement"
    verify_dir = run_dir / "verify"
    plan_dir.mkdir(parents=True, exist_ok=True)
    impl_dir.mkdir(parents=True, exist_ok=True)
    verify_dir.mkdir(parents=True, exist_ok=True)

    def worker(task: dict[str, Any]) -> dict[str, Any]:
        task_id = str(task["task_id"])
        if task_id.endswith("-plan"):
            try:
                milestone = ensure_milestone(
                    repo=args.repo,
                    title=args.milestone_title,
                    description=args.milestone_description,
                    due_on=args.milestone_due_on,
                    dry_run=args.dry_run_plan,
                )
                issue = create_issue(
                    repo=args.repo,
                    title=args.issue_title,
                    body=issue_body,
                    milestone_number=int(milestone["number"]),
                    labels=args.issue_label,
                    dry_run=args.dry_run_plan,
                )
                plan_out = {
                    "repo": args.repo,
                    "milestone": milestone,
                    "issue": issue,
                    "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                }
                plan_path = plan_dir / "plan.output.json"
                atomic_write_json(plan_path, plan_out)
                return {
                    "task_id": task_id,
                    "status": "PASS",
                    "notes": f"plan recorded issue={issue['html_url']} milestone={milestone['html_url']}",
                    "worker_model": "planner.live",
                    "plan_output_path": str(plan_path),
                }
            except Exception as exc:  # noqa: BLE001
                return {
                    "task_id": task_id,
                    "status": "FAIL",
                    "reason_code": "EXEC.NONZERO_EXIT",
                    "notes": str(exc),
                    "worker_model": "planner.live",
                }

        if task_id.endswith("-implement"):
            cmds = args.implement_cmd or []
            if not cmds:
                return {
                    "task_id": task_id,
                    "status": "PASS",
                    "notes": "no implement commands provided (no-op)",
                    "worker_model": "implementer.live",
                }
            all_logs: list[dict[str, Any]] = []
            for i, cmd in enumerate(cmds, start=1):
                rc, out = _run_cmd(cmd, cwd=args.implement_cwd)
                log_path = impl_dir / f"command_{i:02d}.log"
                log_path.write_text(f"$ {cmd}\n\n{out}\n", encoding="utf-8")
                all_logs.append({"index": i, "command": cmd, "rc": rc, "log_path": str(log_path)})
                if rc != 0:
                    atomic_write_json(impl_dir / "implement.output.json", {"commands": all_logs})
                    return {
                        "task_id": task_id,
                        "status": "FAIL",
                        "reason_code": "EXEC.NONZERO_EXIT",
                        "notes": f"implement command failed at #{i}",
                        "worker_model": "implementer.live",
                    }
            atomic_write_json(impl_dir / "implement.output.json", {"commands": all_logs})
            return {
                "task_id": task_id,
                "status": "PASS",
                "notes": f"implement commands passed ({len(cmds)})",
                "worker_model": "implementer.live",
            }

        if task_id.endswith("-verify"):
            rc, out = _run_cmd(args.verify_cmd, cwd=args.verify_cwd or args.implement_cwd)
            log_path = verify_dir / "verify.log"
            log_path.write_text(f"$ {args.verify_cmd}\n\n{out}\n", encoding="utf-8")
            if rc != 0:
                return {
                    "task_id": task_id,
                    "status": "FAIL",
                    "reason_code": "VERIFY.TEST_FAILURE",
                    "notes": f"verify command failed rc={rc}",
                    "worker_model": "verifier.live",
                }
            return {
                "task_id": task_id,
                "status": "PASS",
                "notes": "verify command passed",
                "worker_model": "verifier.live",
            }

        return {
            "task_id": task_id,
            "status": "FAIL",
            "reason_code": "EXEC.NONZERO_EXIT",
            "notes": "unknown task id",
            "worker_model": "unknown",
        }

    bus = EventBus(event_log=args.event_log)
    harness = ImplementerHarness(
        bus=bus,
        run_root=run_root,
        worker_fn=worker,
        max_retries=args.max_retries,
        worker_models=["planner.live", "implementer.live", "verifier.live"],
    )
    run_summary = harness.run(work_queue)

    reason_codes_payload = _load_json(args.reason_codes)
    reason_codes_catalog = {item["code"] for item in reason_codes_payload.get("codes", [])}
    gate_decision, trace_source = create_gate_decision(
        run_summary=run_summary,
        reason_codes_catalog=reason_codes_catalog,
        verify_command=args.verify_cmd,
        risk_threshold=args.risk_threshold,
        otel_export=False,
    )
    validate_gate_decision_schema(gate_decision, ROOT / "ssot/schemas/gate.decision.schema.json")
    gate_path = persist_gate_decision(run_root, run_id, gate_decision)

    promotion = create_promotion_decision(gate_decision=gate_decision, max_risk=args.risk_threshold)
    validate_promotion_schema(promotion, ROOT / "ssot/schemas/promotion.decision.schema.json")
    promotion_path = persist_promotion_decision(run_root, run_id, promotion)

    control_events = load_control_events(event_log=args.event_log, run_id=run_id)
    control_ledger = materialize_control_ledger(control_events)
    control_ledger_path = run_dir / "control.ledger.json"
    atomic_write_json(control_ledger_path, control_ledger)

    state_space = _load_json(args.state_space)
    updated_state = update_state_space(
        state_space=state_space,
        work_queue=work_queue,
        run_summary=run_summary,
        gate_decision=gate_decision,
        promotion_decision=promotion,
    )
    state_out_path = run_dir / "state.space.json"
    atomic_write_json(state_out_path, updated_state)

    plan_output_path = run_dir / "plan" / "plan.output.json"
    plan_output = _load_json(plan_output_path) if plan_output_path.exists() else {}

    manifest = {
        "version": "0.2.0",
        "run_id": run_id,
        "inputs": {
            "repo": args.repo,
            "issue_title": args.issue_title,
            "milestone_title": args.milestone_title,
            "work_queue_sha256": _sha256_path(run_dir / "work.queue.json"),
        },
        "commands": {
            "implement": args.implement_cmd or [],
            "verify": args.verify_cmd,
        },
        "plan": plan_output,
        "artifacts": {
            "work_queue_path": str(run_dir / "work.queue.json"),
            "summary_path": str(run_dir / "summary.json"),
            "gate_decision_path": str(gate_path),
            "promotion_decision_path": str(promotion_path),
            "control_ledger_path": str(control_ledger_path),
            "state_space_path": str(state_out_path),
        },
        "runtime": {
            "repo_commit_sha": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False).stdout.strip() or "unknown",
            "platform": platform.platform(),
            "python": sys.version.split(" ")[0],
            "cwd": os.getcwd(),
            "trace_source": trace_source,
        },
    }
    manifest_path = run_dir / "run.manifest.json"
    atomic_write_json(manifest_path, manifest)

    return {
        "run_id": run_id,
        "work_queue_path": str(run_dir / "work.queue.json"),
        "summary_path": str(run_dir / "summary.json"),
        "gate_decision_path": str(gate_path),
        "promotion_decision_path": str(promotion_path),
        "state_space_path": str(state_out_path),
        "run_manifest_path": str(manifest_path),
        "plan_output_path": str(plan_output_path) if plan_output_path.exists() else None,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run non-demo PLAN->IMPLEMENT->VERIFY loop")
    p.add_argument("--repo", required=True, help="GitHub repo slug, e.g. fatb4f/codex-browse")
    p.add_argument("--milestone-title", required=True)
    p.add_argument("--milestone-description", default="")
    p.add_argument("--milestone-due-on", default="", help="ISO-8601 due date, e.g. 2026-03-06T00:00:00Z")
    p.add_argument("--issue-title", required=True)
    p.add_argument("--issue-body", default="")
    p.add_argument("--issue-body-file", type=Path)
    p.add_argument("--issue-label", action="append", default=[])
    p.add_argument("--implement-cmd", action="append", default=[])
    p.add_argument("--implement-cwd", type=Path, default=ROOT)
    p.add_argument("--verify-cmd", required=True)
    p.add_argument("--verify-cwd", type=Path)
    p.add_argument("--run-id", default="")
    p.add_argument("--run-root", type=Path, default=Path("ops/runtime/runs"))
    p.add_argument("--state-space", type=Path, default=Path("ssot/examples/state.space.json"))
    p.add_argument("--reason-codes", type=Path, default=Path("ssot/policy/reason.codes.json"))
    p.add_argument("--event-log", type=Path, default=Path("ops/runtime/mcp_events.jsonl"))
    p.add_argument("--risk-threshold", type=int, default=60)
    p.add_argument("--max-workers", type=int, default=3)
    p.add_argument("--max-retries", type=int, default=0)
    p.add_argument("--dry-run-plan", action="store_true", help="Do not mutate GitHub; emit synthetic milestone/issue refs")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    assert_runtime_path(args.run_root, ROOT, "--run-root")
    assert_runtime_path(args.event_log, ROOT, "--event-log")
    if args.issue_body_file is not None and not args.issue_body_file.exists():
        raise SystemExit(f"issue body file not found: {args.issue_body_file}")

    result = run_plan_implement_verify(args)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
