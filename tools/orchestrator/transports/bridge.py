from __future__ import annotations

from dataclasses import dataclass

from tools.orchestrator.mcp_loop import (
    TOPIC_GATE_VERDICT,
    TOPIC_PLAN_CREATED,
    TOPIC_PROMOTION_DECISION,
    TOPIC_TASK_ASSIGNED,
    TOPIC_TASK_RESULT,
)
from tools.orchestrator.transports.a2a_transport import A2AMessage, A2ATransport
from tools.orchestrator.transports.mcp_transport import MCPTransport


@dataclass
class BridgeStats:
    relayed: int = 0
    dropped: int = 0


class A2AMCPBridge:
    """Normalize A2A envelopes into MCP topics owned by the orchestrator."""

    KIND_TO_TOPIC = {
        "planner.wave.created": TOPIC_PLAN_CREATED,
        "worker.task.assigned": TOPIC_TASK_ASSIGNED,
        "worker.task.result": TOPIC_TASK_RESULT,
        "gate.verdict": TOPIC_GATE_VERDICT,
        "promotion.decision": TOPIC_PROMOTION_DECISION,
    }

    def __init__(self, a2a: A2ATransport, mcp: MCPTransport) -> None:
        self.a2a = a2a
        self.mcp = mcp
        self.stats = BridgeStats()

    def relay_once(self, timeout: float | None = None) -> bool:
        message = self.a2a.recv(timeout=timeout)
        if message is None:
            return False
        topic = self.KIND_TO_TOPIC.get(message.kind)
        if topic is None:
            self.stats.dropped += 1
            return False
        self.mcp.publish(topic=topic, run_id=message.run_id, payload=message.payload)
        self.stats.relayed += 1
        return True

    def relay_until_empty(self) -> BridgeStats:
        while self.relay_once(timeout=0):
            pass
        return self.stats


def to_a2a(kind: str, run_id: str, payload: dict) -> A2AMessage:
    """Helper for quickly constructing A2A envelopes in callers/tests."""
    return A2AMessage(kind=kind, run_id=run_id, payload=payload)

