from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator import mcp_loop as MODULE


def test_wave_processes_all_tasks_not_just_max_workers() -> None:
    bus = MODULE.EventBus()
    orch = MODULE.RalphOrchestrator(
        bus=bus,
        max_workers=2,
        control_model="gpt-5.3-codex-high",
        worker_models=["gpt-5.3", "gpt-5.2"],
    )
    tasks = [
        MODULE.Task(task_id="task-001", goal="a"),
        MODULE.Task(task_id="task-002", goal="b"),
        MODULE.Task(task_id="task-003", goal="c"),
        MODULE.Task(task_id="task-004", goal="d"),
        MODULE.Task(task_id="task-005", goal="e"),
    ]
    summary = orch.run_wave(goal="test full queue", tasks=tasks)

    assert len(summary["results"]) == 5
    assert sorted(result["task_id"] for result in summary["results"]) == [
        "task-001",
        "task-002",
        "task-003",
        "task-004",
        "task-005",
    ]


def test_gate_rejects_when_any_worker_fails() -> None:
    bus = MODULE.EventBus()
    orch = MODULE.RalphOrchestrator(
        bus=bus,
        max_workers=2,
        control_model="gpt-5.3-codex-high",
        worker_models=["gpt-5.3", "gpt-5.2"],
    )
    tasks = [
        MODULE.Task(task_id="task-001", goal="a"),
        MODULE.Task(task_id="task-002", goal="b", fail=True),
    ]
    summary = orch.run_wave(goal="test rejection", tasks=tasks)

    assert summary["gate"]["verdict"] == "REJECT"
    assert summary["promotion"] == "REJECT"
