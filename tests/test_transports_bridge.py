from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.mcp_loop import EventBus, TOPIC_TASK_RESULT
from tools.orchestrator.transports.a2a_transport import A2ATransport
from tools.orchestrator.transports.bridge import A2AMCPBridge, to_a2a
from tools.orchestrator.transports.mcp_transport import MCPTransport


def test_bridge_relays_known_kind_to_mcp_topic() -> None:
    bus = EventBus()
    a2a = A2ATransport()
    mcp = MCPTransport(bus=bus)
    bridge = A2AMCPBridge(a2a=a2a, mcp=mcp)

    a2a.enqueue_incoming(
        to_a2a(
            kind="worker.task.result",
            run_id="wave-1",
            payload={"task_id": "task-001", "status": "PASS"},
        )
    )
    stats = bridge.relay_until_empty()

    assert stats.relayed == 1
    assert stats.dropped == 0

    topic_queue = bus.subscribe(TOPIC_TASK_RESULT)
    event = topic_queue.get_nowait()
    assert event.run_id == "wave-1"
    assert event.payload["task_id"] == "task-001"
    assert event.payload["status"] == "PASS"


def test_bridge_drops_unknown_kind() -> None:
    bus = EventBus()
    a2a = A2ATransport()
    mcp = MCPTransport(bus=bus)
    bridge = A2AMCPBridge(a2a=a2a, mcp=mcp)

    a2a.enqueue_incoming(to_a2a(kind="unknown.kind", run_id="wave-2", payload={}))
    stats = bridge.relay_until_empty()

    assert stats.relayed == 0
    assert stats.dropped == 1

