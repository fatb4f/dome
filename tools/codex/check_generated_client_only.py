#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    codex_root = root / "tools" / "codex"
    target = codex_root / "dome_cli.py"
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

    # Enforce thin-client-only gRPC usage for codex consumers.
    allowed = {
        codex_root / "domed_client.py",
        codex_root / "check_generated_client_only.py",
    }
    bad_refs: list[str] = []
    for path in sorted(codex_root.glob("*.py")):
        if path in allowed:
            continue
        text = path.read_text(encoding="utf-8")
        if "grpc.insecure_channel(" in text:
            bad_refs.append(f"{path.relative_to(root)} uses grpc.insecure_channel directly")
        if "DomedServiceStub(" in text:
            bad_refs.append(f"{path.relative_to(root)} uses DomedServiceStub directly")
    if bad_refs:
        raise SystemExit("generated-client-only policy violation:\n- " + "\n- ".join(bad_refs))

    print("generated-client-only check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
