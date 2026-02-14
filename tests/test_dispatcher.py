from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.dispatcher import DispatcherSupervisor
from tools.orchestrator.mcp_loop import (
    EventBus,
    TOPIC_PROMOTION_DECISION,
    TOPIC_TASK_ASSIGNED,
    TOPIC_TASK_RESULT,
)


def _queue() -> dict:
    return {
        "version": "0.2.0",
        "run_id": "wave-001",
        "base_ref": "main",
        "max_workers": 2,
        "tasks": [
            {"task_id": "t1", "goal": "a", "status": "QUEUED", "dependencies": []},
            {"task_id": "t2", "goal": "b", "status": "QUEUED", "dependencies": ["t1"]},
            {"task_id": "t3", "goal": "c", "status": "QUEUED", "dependencies": ["t1"]},
            {"task_id": "t4", "goal": "d", "status": "QUEUED", "dependencies": ["t2", "t3"]},
        ],
    }


def test_dispatcher_processes_all_tasks() -> None:
    bus = EventBus()
    sup = DispatcherSupervisor(bus=bus, worker_models=["gpt-5.3", "gpt-5.2"])
    summary = sup.dispatch(_queue())

    assert summary["dispatched_count"] == 4
    assert [r["task_id"] for r in summary["results"]] == ["t1", "t2", "t3", "t4"]

    assigned_q = bus.subscribe(TOPIC_TASK_ASSIGNED)
    result_q = bus.subscribe(TOPIC_TASK_RESULT)
    assert assigned_q.qsize() == 4
    assert result_q.qsize() == 4


def test_dispatcher_raises_on_dependency_cycle() -> None:
    bus = EventBus()
    sup = DispatcherSupervisor(bus=bus)
    work = _queue()
    work["tasks"][0]["dependencies"] = ["t4"]

    with pytest.raises(ValueError, match="dependency cycle"):
        sup.dispatch(work)


def test_dispatcher_never_emits_promotion_event() -> None:
    bus = EventBus()
    sup = DispatcherSupervisor(bus=bus)
    sup.dispatch(_queue())

    promotion_q = bus.subscribe(TOPIC_PROMOTION_DECISION)
    assert promotion_q.qsize() == 0

