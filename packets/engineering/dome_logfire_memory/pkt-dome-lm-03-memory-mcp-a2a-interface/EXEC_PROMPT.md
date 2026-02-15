# EXEC_PROMPT: pkt-dome-lm-03-memory-mcp-a2a-interface

## Scope
- Milestone: LM-03 - MCP/A2A memory interface
- Tracker issue: #26
- Depends on: LM-02

## Tasks
1. Add bounded deterministic memory query/upsert/summary/health APIs.
2. Validate evidence capsule payloads before memory upsert.
3. Add tests for deterministic sorting and contract behavior.
4. Run `just test`.
5. Write evidence artifacts under `ops/runtime/lm-03/`.

## Acceptance Checks
- `just test` passes.
- `memory.query_priors`, `memory.upsert_capsule`, `memory.get_run_summary`, and `memory.health` handlers exist.
- Query ordering is stable for identical snapshots.

## Evidence
- `ops/runtime/lm-03/checklist.md`
- `ops/runtime/lm-03/command_output.txt`
