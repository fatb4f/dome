# M-04 Checklist

- [x] Added event envelope contract:
  - `ssot/schemas/event.envelope.schema.json`
  - `ssot/examples/event.envelope.json`
- [x] Added event envelope fields in runtime JSONL persistence (`event_id`, `sequence`, `schema_version`)
- [x] Added idempotent publish behavior by event ID in `EventBus`
- [x] Added replay helpers for task-result streams in `tools/orchestrator/mcp_loop.py`
- [x] Split task result events into raw and persisted topics (`task.result.raw`, `task.result`)
- [x] Updated live-fix iteration loop reconstruction from replayed events
- [x] Added tests:
  - `tests/test_mcp_events.py`
  - `tests/test_run_live_fix_demo.py`
- [x] Captured verification output in `ops/runtime/m04/command_output.txt`

## Verification

- `pytest -q tests/test_mcp_events.py tests/test_run_live_fix_demo.py`
- `just test`
