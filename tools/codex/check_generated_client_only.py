#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    target = root / "tools/codex/dome_cli.py"
    tree = ast.parse(target.read_text(encoding="utf-8"))

    run_skill_uses_domed = False
    run_skill_uses_legacy = False

    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            if (
                isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Attribute)
                and test.left.attr == "cmd"
                and len(test.ops) == 1
                and isinstance(test.ops[0], ast.Eq)
                and len(test.comparators) == 1
                and isinstance(test.comparators[0], ast.Constant)
            ):
                cmd = test.comparators[0].value
                if cmd == "run-skill":
                    for n in ast.walk(node):
                        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                            if n.func.id == "run_task_via_domed":
                                run_skill_uses_domed = True
                            if n.func.id == "run_task":
                                run_skill_uses_legacy = True

    if not run_skill_uses_domed:
        raise SystemExit("run-skill must call run_task_via_domed")
    if run_skill_uses_legacy:
        raise SystemExit("run-skill must not call legacy run_task")
    print("generated-client-only check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

