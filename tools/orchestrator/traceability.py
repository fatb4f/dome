#!/usr/bin/env python
"""Requirement traceability report generator for graph fold CI gates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIREMENT_TO_CHECKS: dict[str, list[str]] = {
    "CL-REQ-0001": ["tests/test_planner.py::test_task_spec_authority_guard_rejects_direct_method_keys"],
    "CL-REQ-0002": ["tests/test_dispatcher.py::test_dispatcher_rejects_out_of_contract_method"],
    "CL-REQ-0003": ["tests/test_dispatcher.py::test_dispatcher_rejects_spawn_spec_unknown_fields"],
    "CL-REQ-0004": ["tests/test_mcp_events.py::test_control_events_materialize_deterministic_ledger"],
    "CL-REQ-0005": ["tests/test_dispatcher.py::test_dispatcher_tiebreak_is_deterministic_across_input_order"],
}


def build_traceability_report(repo_root: Path) -> dict[str, object]:
    missing: list[str] = []
    mappings: dict[str, dict[str, object]] = {}
    for req_id in sorted(REQUIREMENT_TO_CHECKS.keys()):
        checks = REQUIREMENT_TO_CHECKS[req_id]
        existing = []
        missing_checks = []
        for check in checks:
            file_path = check.split("::", 1)[0]
            path = repo_root / file_path
            if path.exists():
                existing.append(check)
            else:
                missing_checks.append(check)
        if missing_checks:
            missing.append(req_id)
        mappings[req_id] = {
            "checks": checks,
            "existing_checks": existing,
            "missing_checks": missing_checks,
            "status": "PASS" if not missing_checks else "FAIL",
        }
    return {
        "version": "0.1.0",
        "requirements": mappings,
        "missing_requirement_ids": missing,
        "status": "PASS" if not missing else "FAIL",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build CL-REQ traceability report")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_traceability_report(args.repo_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if report["status"] != "PASS":
        raise SystemExit(2)
    print(str(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
