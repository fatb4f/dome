# EXEC_PROMPT: pkt-dome-graph-004-controlevent-append-only-log

## Scope
- Issue: DOME-GRAPH-004
- GitHub issue: #48
- Milestone: M2: Closed-Loop Ledger and Deterministic Execution
- Requirements: CL-REQ-0004
- Depends on: DOME-GRAPH-002, DOME-GRAPH-003

## Tasks
1. Reproduce the current gap for DOME-GRAPH-004 and capture baseline evidence.
2. Implement required changes for: Authoritative append-only ControlEvent log.
3. Add or update focused tests.
4. Run:
   
   `pytest -q tests/test_mcp_events.py tests/test_event_envelope_runtime.py`
5. Write evidence artifacts under
   
   `ops/runtime/graph-004/`.

## Acceptance Checks
- Focused tests pass.
- Artifacts are schema-valid and deterministic where required.
- Progress is reflected in tracker + issue thread.

## Evidence
- `ops/runtime/graph-004/checklist.md`
- `ops/runtime/graph-004/command_output.txt`
