from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

from tools.domed.executor import ExecutionEvent, ExecutionRequest, ExecutionResult


class LocalProcessExecutor:
    def execute(self, request: ExecutionRequest, sink) -> ExecutionResult:  # type: ignore[no-untyped-def]
        if not request.entrypoint:
            return ExecutionResult(terminal_state="failed", exit_code=127, message="empty entrypoint")

        env = os.environ.copy()
        if request.env_allowlist:
            env = {k: v for k, v in env.items() if k in set(request.env_allowlist)}
        env["DOMED_RUN_ID"] = request.run_id
        env["DOMED_JOB_ID"] = request.job_id
        env["DOMED_TOOL_ID"] = request.tool_id
        env["DOMED_PROFILE"] = request.profile
        env["DOMED_TASK_JSON"] = json.dumps(request.task, sort_keys=True)
        env["DOMED_CONSTRAINTS_JSON"] = json.dumps(request.constraints, sort_keys=True)

        try:
            proc = subprocess.Popen(
                request.entrypoint,
                cwd=str(request.cwd),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = proc.communicate(timeout=request.timeout_seconds)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            if stdout:
                for line in stdout.splitlines():
                    sink(ExecutionEvent(kind="log", payload={"stream": "stdout", "line": line}))
            if stderr:
                for line in stderr.splitlines():
                    sink(ExecutionEvent(kind="log", payload={"stream": "stderr", "line": line}))
            sink(ExecutionEvent(kind="error", payload={"reason": "executor timeout"}))
            return ExecutionResult(terminal_state="failed", exit_code=124, message="executor timeout")

        if stdout:
            for line in stdout.splitlines():
                sink(ExecutionEvent(kind="log", payload={"stream": "stdout", "line": line}))
                if line.startswith("PROGRESS:"):
                    raw = line.removeprefix("PROGRESS:").strip()
                    try:
                        value = float(raw)
                    except ValueError:
                        continue
                    sink(ExecutionEvent(kind="progress", payload={"value": value}))
        if stderr:
            for line in stderr.splitlines():
                sink(ExecutionEvent(kind="log", payload={"stream": "stderr", "line": line}))

        if proc.returncode == 0:
            return ExecutionResult(terminal_state="succeeded", exit_code=0, message="ok")
        return ExecutionResult(
            terminal_state="failed",
            exit_code=int(proc.returncode or 1),
            message="non-zero exit",
        )


def repo_root_from_file(path: Path) -> Path:
    return path.resolve().parents[3]

