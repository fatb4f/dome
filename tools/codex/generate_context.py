#!/usr/bin/env python3
"""Generate Codex context frontmatter and prompt snippet from local git/session state."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class CommitEntry:
    hash: str
    short: str
    committed_at_utc: str
    subject: str
    files_touched: list[str]


def run(cmd: list[str]) -> str:
    out = subprocess.check_output(cmd, text=True)
    return out.rstrip("\n")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_project_arg(raw: str) -> tuple[str, Path]:
    if "=" not in raw:
        raise ValueError(f"invalid --project entry '{raw}', expected name=/abs/path")
    name, raw_path = raw.split("=", 1)
    name = name.strip()
    if not name:
        raise ValueError(f"invalid --project entry '{raw}', project name is empty")
    path = Path(raw_path).expanduser().resolve()
    return name, path


def load_latest_sessions_by_cwd(sessions_root: Path) -> dict[str, dict[str, str]]:
    by_cwd: dict[str, dict[str, str]] = {}
    if not sessions_root.exists():
        return by_cwd

    for path in sessions_root.rglob("*.jsonl"):
        try:
            first = path.read_text(encoding="utf-8").splitlines()[0]
            payload = json.loads(first).get("payload", {})
            cwd = payload.get("cwd")
            sid = payload.get("id")
            ts = payload.get("timestamp")
            if not cwd or not sid or not ts:
                continue
            prev = by_cwd.get(cwd)
            if prev is None or ts > prev["timestamp_utc"]:
                by_cwd[cwd] = {"id": sid, "timestamp_utc": ts}
        except (OSError, json.JSONDecodeError, IndexError):
            continue
    return by_cwd


def load_recent_commits(repo_path: Path, limit: int) -> list[CommitEntry]:
    marker = "__COMMIT__"
    raw = run(
        [
            "git",
            "-C",
            str(repo_path),
            "log",
            f"-n{limit}",
            "--date=iso-strict",
            "--name-only",
            f"--pretty=format:{marker}%H|%h|%cI|%s",
        ]
    )

    commits: list[CommitEntry] = []
    current: CommitEntry | None = None
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(marker):
            if current is not None:
                commits.append(current)
            _, rest = line.split(marker, 1)
            full, short, ts, subject = rest.split("|", 3)
            current = CommitEntry(
                hash=full,
                short=short,
                committed_at_utc=ts,
                subject=subject,
                files_touched=[],
            )
            continue
        if current is not None and line not in current.files_touched:
            current.files_touched.append(line)

    if current is not None:
        commits.append(current)
    return commits


def collect_last_files(commits: list[CommitEntry], max_files: int) -> list[str]:
    files: list[str] = []
    seen: set[str] = set()
    for commit in commits:
        for rel in commit.files_touched:
            if rel in seen:
                continue
            seen.add(rel)
            files.append(rel)
            if len(files) >= max_files:
                return files
    return files


def quote_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def dump_yaml_like(obj: Any, indent: int = 0) -> str:
    pad = " " * indent
    if isinstance(obj, dict):
        lines: list[str] = []
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.append(dump_yaml_like(value, indent + 2))
            else:
                lines.append(f"{pad}{key}: {quote_scalar(value)}")
        return "\n".join(lines)
    if isinstance(obj, list):
        lines = []
        for item in obj:
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                lines.append(dump_yaml_like(item, indent + 2))
            else:
                lines.append(f"{pad}- {quote_scalar(item)}")
        return "\n".join(lines) if lines else f"{pad}[]"
    return f"{pad}{quote_scalar(obj)}"


def build_prompt_snippet(context: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("Meta context (local, generated):")
    lines.append(f"- src_root: {context['src_root']}")
    lines.append(f"- src_meta: {context['src_meta']}")
    for project in context["projects"]:
        lines.append(f"- project: {project['name']} ({project['path']})")
        sess = project.get("codex_session")
        if sess:
            lines.append(f"  - latest_session_id: {sess['id']}")
            lines.append(f"  - latest_session_timestamp_utc: {sess['timestamp_utc']}")
        else:
            lines.append("  - latest_session_id: null")
        lines.append("  - recent_commits:")
        for c in project["recent_commits"]:
            lines.append(f"    - {c['short']} {c['subject']}")
        lines.append("  - last_files_touched:")
        for rel in project["last_files_touched"]:
            lines.append(f"    - {rel}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project",
        action="append",
        required=True,
        help="Project in name=/abs/path form. Repeat for multiple projects.",
    )
    parser.add_argument(
        "--sessions-root",
        default=str(Path.home() / ".config" / "codex" / "sessions"),
        help="Codex sessions root (default: ~/.config/codex/sessions)",
    )
    parser.add_argument("--src-root", default=str(Path.home() / "src"))
    parser.add_argument("--src-meta", default=str(Path.home() / "src" / "meta"))
    parser.add_argument("--commit-limit", type=int, default=5)
    parser.add_argument("--max-last-files", type=int, default=20)
    parser.add_argument(
        "--out-frontmatter",
        default=os.path.join(
            os.environ.get("CODEX_STATE", str(Path.home() / ".local" / "state" / "codex")),
            "meta",
            "context.frontmatter.md",
        ),
    )
    parser.add_argument(
        "--out-prompt-snippet",
        default=os.path.join(
            os.environ.get("CODEX_STATE", str(Path.home() / ".local" / "state" / "codex")),
            "meta",
            "generated_prompt_context.txt",
        ),
    )
    args = parser.parse_args()

    projects = [parse_project_arg(p) for p in args.project]
    latest_sessions = load_latest_sessions_by_cwd(Path(args.sessions_root).expanduser().resolve())

    project_entries: list[dict[str, Any]] = []
    for name, repo_path in projects:
        commits = load_recent_commits(repo_path, args.commit_limit)
        commit_entries = [
            {
                "hash": c.hash,
                "short": c.short,
                "committed_at_utc": c.committed_at_utc,
                "subject": c.subject,
                "files_touched": c.files_touched,
            }
            for c in commits
        ]
        entry: dict[str, Any] = {
            "name": name,
            "path": str(repo_path),
            "codex_session": latest_sessions.get(str(repo_path)),
            "recent_commits": commit_entries,
            "last_files_touched": collect_last_files(commits, args.max_last_files),
        }
        project_entries.append(entry)

    context = {
        "generated_at_utc": utc_now_iso(),
        "src_root": str(Path(args.src_root).expanduser().resolve()),
        "src_meta": str(Path(args.src_meta).expanduser().resolve()),
        "projects": project_entries,
    }

    out_frontmatter = Path(args.out_frontmatter).expanduser().resolve()
    out_prompt = Path(args.out_prompt_snippet).expanduser().resolve()
    out_frontmatter.parent.mkdir(parents=True, exist_ok=True)
    out_prompt.parent.mkdir(parents=True, exist_ok=True)

    frontmatter_text = "---\n" + dump_yaml_like(context) + "\n---\n"
    frontmatter_text += (
        "\nThis file is generated. It captures lightweight project context pointers for Codex.\n"
    )
    out_frontmatter.write_text(frontmatter_text, encoding="utf-8")
    out_prompt.write_text(build_prompt_snippet(context), encoding="utf-8")

    print(f"wrote {out_frontmatter}")
    print(f"wrote {out_prompt}")


if __name__ == "__main__":
    main()
