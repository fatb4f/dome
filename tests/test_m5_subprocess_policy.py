from __future__ import annotations

from pathlib import Path
import subprocess


def test_subprocess_policy_guard_passes() -> None:
    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        ["python", "tools/codex/check_subprocess_policy.py"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout

