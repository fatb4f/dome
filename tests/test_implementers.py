from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.implementers import ImplementerHarness
from tools.orchestrator.mcp_loop import EventBus


def _queue() -> dict:
    return {
        "version": "0.2.0",
        "run_id": "wave-phase2-001",
        "base_ref": "main",
        "max_workers": 2,
        "tasks": [
            {"task_id": "t1", "goal": "a", "status": "QUEUED", "dependencies": []},
            {"task_id": "t2", "goal": "b", "status": "QUEUED", "dependencies": []},
            {"task_id": "t3", "goal": "c", "status": "QUEUED", "dependencies": []},
            {"task_id": "t4", "goal": "d", "status": "QUEUED", "dependencies": []},
            {"task_id": "t5", "goal": "e", "status": "QUEUED", "dependencies": []},
        ],
    }


def test_implementers_process_all_tasks_and_persist_artifacts(tmp_path: Path) -> None:
    bus = EventBus()
    harness = ImplementerHarness(bus=bus, run_root=tmp_path)
    summary = harness.run(_queue())

    assert summary["dispatched_count"] == 5
    run_dir = tmp_path / "wave-phase2-001"
    assert (run_dir / "work.queue.json").exists()
    assert (run_dir / "summary.json").exists()
    for task_id in ("t1", "t2", "t3", "t4", "t5"):
        assert (run_dir / "task_results" / f"{task_id}.result.json").exists()
        assert (run_dir / "evidence" / f"{task_id}.evidence.bundle.telemetry.json").exists()


def test_implementers_retry_transient_failure_then_pass(tmp_path: Path) -> None:
    attempts: dict[str, int] = {}

    def flaky_worker(task: dict) -> dict:
        task_id = task["task_id"]
        attempts[task_id] = attempts.get(task_id, 0) + 1
        if attempts[task_id] == 1:
            return {
                "task_id": task_id,
                "status": "FAIL",
                "transient": True,
                "reason_code": "TRANSIENT.NETWORK",
            }
        return {"task_id": task_id, "status": "PASS"}

    bus = EventBus()
    harness = ImplementerHarness(bus=bus, run_root=tmp_path, worker_fn=flaky_worker, max_retries=2)
    summary = harness.run(
        {
            "version": "0.2.0",
            "run_id": "wave-phase2-retry",
            "base_ref": "main",
            "max_workers": 1,
            "tasks": [{"task_id": "t1", "goal": "retry", "status": "QUEUED", "dependencies": []}],
        }
    )
    result = summary["results"][0]
    assert result["status"] == "PASS"
    assert result["attempts"] == 2
    assert len(result["attempt_history"]) == 2
    assert result["attempt_history"][0]["status"] == "FAIL"
    assert result["attempt_history"][1]["status"] == "PASS"
    attempt_path = tmp_path / "wave-phase2-retry" / "attempts" / "t1.attempts.json"
    assert attempt_path.exists()


def test_retry_backoff_is_monotonic_non_decreasing() -> None:
    sleeps: list[float] = []

    def always_transient(task: dict) -> dict:
        return {
            "task_id": task["task_id"],
            "status": "FAIL",
            "transient": True,
            "reason_code": "TRANSIENT.NETWORK",
        }

    from tools.orchestrator.implementers import RetryingWorker

    worker = RetryingWorker(
        worker_fn=always_transient,
        max_retries=3,
        base_backoff_ms=20,
        max_backoff_ms=200,
        sleep_fn=lambda s: sleeps.append(s),
    )
    out = worker({"task_id": "t-retry"})
    assert out["status"] == "FAIL"
    assert out["attempts"] == 4
    backoffs = out["retry_backoff_ms"]
    assert len(backoffs) == 3
    assert backoffs[0] <= backoffs[1] <= backoffs[2]
    assert len(sleeps) == 3


def test_transient_failure_exhaustion_writes_dlq(tmp_path: Path) -> None:
    def always_transient(task: dict) -> dict:
        return {
            "task_id": task["task_id"],
            "status": "FAIL",
            "transient": True,
            "reason_code": "TRANSIENT.TIMEOUT",
        }

    bus = EventBus()
    harness = ImplementerHarness(bus=bus, run_root=tmp_path, worker_fn=always_transient, max_retries=1)
    summary = harness.run(
        {
            "version": "0.2.0",
            "run_id": "wave-phase2-dlq",
            "base_ref": "main",
            "max_workers": 1,
            "tasks": [{"task_id": "t1", "goal": "retry", "status": "QUEUED", "dependencies": []}],
        }
    )
    result = summary["results"][0]
    assert result["status"] == "FAIL"
    assert result["dlq_path"]
    assert Path(result["dlq_path"]).exists()
