from __future__ import annotations

import json
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any


def _git_output(args: list[str], cwd: Path) -> str:
    out = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    value = out.stdout.strip()
    return value


def collect_runtime_provenance(repo_root: Path, *, executor_backend: str, manifest_hash: str) -> dict[str, Any]:
    commit_sha = _git_output(["rev-parse", "HEAD"], repo_root) or "unknown"
    dirty_flag = bool(_git_output(["status", "--porcelain"], repo_root))
    env = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "implementation": platform.python_implementation(),
    }
    tools = {
        "domed": "phase-d",
        "executor": executor_backend,
        "python": env["python"],
    }
    return {
        "repo": "dome",
        "commit_sha": commit_sha,
        "dirty_flag": dirty_flag,
        "contract_hashes_json": json.dumps({"tool_manifest_sha256": manifest_hash}, sort_keys=True),
        "tool_versions_json": json.dumps(tools, sort_keys=True),
        "env_fingerprint": json.dumps(env, sort_keys=True),
    }

