# EXEC_PROMPT: pkt-dome-graph-005-deterministic-ledger-materializer

## Scope
- Issue: DOME-GRAPH-005
- GitHub issue: #49
- Milestone: M2: Closed-Loop Ledger and Deterministic Execution
- Requirements: CL-REQ-0004, CL-REQ-0005
- Depends on: DOME-GRAPH-004

## Tasks
1. Reproduce the current gap for DOME-GRAPH-005 and capture baseline evidence.
2. Implement required changes for: Deterministic ledger materializer + replay equivalence.
3. Add or update focused tests.
4. Run:
   
   `pytest -q tests/test_state_replay.py tests/test_state_machine.py`
5. Write evidence artifacts under
   
   `ops/runtime/graph-005/`.

## Acceptance Checks
- Focused tests pass.
- Artifacts are schema-valid and deterministic where required.
- Progress is reflected in tracker + issue thread.

## Evidence
- `ops/runtime/graph-005/checklist.md`
- `ops/runtime/graph-005/command_output.txt`
