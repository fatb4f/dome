from __future__ import annotations

from typing import Any

from tools.orchestrator.mcp_loop import Event, EventBus


class MCPTransport:
    """Thin adapter for orchestrator-owned MCP-style event publishing."""

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    def publish(self, topic: str, run_id: str, payload: dict[str, Any]) -> None:
        self.bus.publish(Event(topic=topic, run_id=run_id, payload=payload))

