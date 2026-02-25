from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.domed.executor import ExecutionRequest
from tools.domed.executors.local_process import LocalProcessExecutor


def test_local_process_executor_success_and_logs() -> None:
    exe = LocalProcessExecutor()
    events = []
    req = ExecutionRequest(
        run_id="run-1",
        job_id="job-1",
        tool_id="domed.exec-probe",
        profile="work",
        task={"stdout": ["ok-a"], "stderr": ["warn-b"], "progress": [0.1, 0.9], "exit_code": 0},
        constraints={},
        entrypoint=["python3", "-m", "tools.domed.executor_probe"],
        cwd=ROOT,
    )
    result = exe.execute(req, lambda evt: events.append(evt))
    assert result.terminal_state == "succeeded"
    assert result.exit_code == 0
    payloads = [evt.payload for evt in events]
    assert any(p.get("line") == "ok-a" and p.get("stream") == "stdout" for p in payloads)
    assert any(p.get("line") == "warn-b" and p.get("stream") == "stderr" for p in payloads)
    assert any("value" in p for p in payloads)


def test_local_process_executor_failure_exit_code() -> None:
    exe = LocalProcessExecutor()
    req = ExecutionRequest(
        run_id="run-2",
        job_id="job-2",
        tool_id="domed.exec-probe",
        profile="work",
        task={"stdout": ["x"], "exit_code": 3},
        constraints={},
        entrypoint=["python3", "-m", "tools.domed.executor_probe"],
        cwd=ROOT,
    )
    result = exe.execute(req, lambda _evt: None)
    assert result.terminal_state == "failed"
    assert result.exit_code == 3
