# EXEC_PROMPT: pkt-dome-graph-006-scheduler-tiebreak-contracts

## Scope
- Issue: DOME-GRAPH-006
- GitHub issue: #50
- Milestone: M2: Closed-Loop Ledger and Deterministic Execution
- Requirements: CL-REQ-0005
- Depends on: DOME-GRAPH-005

## Tasks
1. Reproduce the current gap for DOME-GRAPH-006 and capture baseline evidence.
2. Implement required changes for: Scheduler/selection/conflict deterministic tie-break contracts.
3. Add or update focused tests.
4. Run:
   
   `pytest -q tests/test_dispatcher.py tests/test_planner.py`
5. Write evidence artifacts under
   
   `ops/runtime/graph-006/`.

## Acceptance Checks
- Focused tests pass.
- Artifacts are schema-valid and deterministic where required.
- Progress is reflected in tracker + issue thread.

## Evidence
- `ops/runtime/graph-006/checklist.md`
- `ops/runtime/graph-006/command_output.txt`
