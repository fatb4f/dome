from __future__ import annotations

import argparse
import ast
import csv
from pathlib import Path


def collect_callsites(repo_root: Path) -> list[dict[str, str]]:
    tools_root = repo_root / "tools"
    rows: list[dict[str, str]] = []
    for path in sorted(tools_root.rglob("*.py")):
        rel = path.relative_to(repo_root).as_posix()
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        lines = source.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            if not (
                isinstance(fn, ast.Attribute)
                and fn.attr == "run"
                and isinstance(fn.value, ast.Name)
                and fn.value.id == "subprocess"
            ):
                continue
            lineno = int(getattr(node, "lineno", 0))
            line = lines[lineno - 1].strip() if lineno > 0 and lineno <= len(lines) else "subprocess.run(...)"
            rows.append(
                {
                    "callsite_id": f"{rel}:{lineno}",
                    "path": rel,
                    "line": str(lineno),
                    "snippet": line,
                }
            )
    return sorted(rows, key=lambda r: (r["path"], int(r["line"])))


def write_inventory(rows: list[dict[str, str]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["callsite_id", "path", "line", "snippet"])
        writer.writeheader()
        writer.writerows(rows)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate subprocess callsite inventory for tool migration")
    p.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument(
        "--out",
        type=Path,
        default=Path("doc/milestone_domed/m5/m5_tool_callsite_inventory.csv"),
    )
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = args.repo_root.resolve()
    out = args.out if args.out.is_absolute() else repo_root / args.out
    rows = collect_callsites(repo_root)
    write_inventory(rows, out)
    print(f"wrote {len(rows)} callsites -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
