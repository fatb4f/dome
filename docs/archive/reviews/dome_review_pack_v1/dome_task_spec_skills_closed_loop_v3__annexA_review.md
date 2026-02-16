---

## Annex A. Review Feedback (2026-02-16)
### Overall
- Architecturally coherent: deterministic pipeline, strong boundaries (planner/coordinator/worker), and explicit closed-loop semantics.
- Main improvement area: move from conceptual → implementable contracts (schemas/state machines/conformance tests).

### Blockers to “implementation-ready”
1. **Canonical schemas**: Provide machine-readable JSON Schema for:
   - Packet, TaskSpec, WaveSpec
   - ToolRequest/ToolResponse
   - ControlEvents (`task.completed`, `ack`, `timeout`, `retry`, `promotion`, etc.)
2. **Outcome artifacts**: Define *exact* shapes and enums for:
   - `WaveStatus`
   - `GateResult`
   - `PromotionResult`
3. **Ack/timeout state machine**: Pin down:
   - allowed transitions
   - retry rules
   - idempotency / duplicate handling across replays
4. **Capability discovery**: Add a minimal capability endpoint (or MCP-like handshake) that returns:
   - tool catalog (optionally progressive)
   - versions (`tool_request_version`, `tool_version`)
   - constraints / allowlists for the current execution container
5. **Conformance suite**: Add CI tests that prove:
   - replay determinism (same inputs → same outputs)
   - boundary enforcement (deny by default)
   - schema validation for every emitted event/artifact

### OSS-alignment suggestions (optional)
- Consider wrapping control-events in a CloudEvents envelope (while still exporting to OTel) to improve interoperability across transports and stores.
- Add “progressive tool discovery” modes (name-only → name+desc → full schema) for large catalogs.
