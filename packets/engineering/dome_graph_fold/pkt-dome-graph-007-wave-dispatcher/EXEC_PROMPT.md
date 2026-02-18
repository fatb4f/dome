# EXEC_PROMPT: pkt-dome-graph-007-wave-dispatcher

## Scope
- Issue: DOME-GRAPH-007
- GitHub issue: #51
- Milestone: M3: Wave Orchestration and Promotion Gates
- Requirements: CL-REQ-0003, CL-REQ-0005
- Depends on: DOME-GRAPH-003

## Tasks
1. Reproduce the current gap for DOME-GRAPH-007 and capture baseline evidence.
2. Implement required changes for: Wave dispatcher with bounded SpawnSpec flow.
3. Add or update focused tests.
4. Run:
   
   `pytest -q tests/test_dispatcher.py tests/test_mcp_loop.py`
5. Write evidence artifacts under
   
   `ops/runtime/graph-007/`.

## Acceptance Checks
- Focused tests pass.
- Artifacts are schema-valid and deterministic where required.
- Progress is reflected in tracker + issue thread.

## Evidence
- `ops/runtime/graph-007/checklist.md`
- `ops/runtime/graph-007/command_output.txt`
