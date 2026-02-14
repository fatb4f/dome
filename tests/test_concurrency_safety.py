import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.io_utils import atomic_write_json  # noqa: E402
from tools.orchestrator.mcp_loop import Event, EventBus, load_event_envelopes  # noqa: E402


def test_parallel_publish_and_atomic_writes_are_consistent(tmp_path: Path) -> None:
    event_log = tmp_path / "events.jsonl"
    out_dir = tmp_path / "artifacts"
    bus = EventBus(event_log=event_log)

    def worker(i: int) -> None:
        bus.publish(
            Event(
                topic="task.result.raw",
                run_id="run-concurrency-001",
                payload={"task_id": f"task-{i:03d}", "status": "PASS", "attempt": 1},
                event_id=f"evt-{i:032x}",
            )
        )
        atomic_write_json(out_dir / f"artifact-{i:03d}.json", {"task_id": i, "ok": True})

    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(worker, range(200)))

    events = load_event_envelopes(event_log=event_log, run_id="run-concurrency-001")
    assert len(events) == 200
    assert len({item["event_id"] for item in events}) == 200

    artifacts = sorted(out_dir.glob("*.json"))
    assert len(artifacts) == 200
    for path in artifacts:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["ok"] is True
