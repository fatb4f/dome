# EXEC_PROMPT: pkt-dome-graph-001-taskspec-intent-authority

## Scope
- Issue: DOME-GRAPH-001
- GitHub issue: #45
- Milestone: M1: Authority and Contracts Baseline
- Requirements: CL-REQ-0001
- Depends on: none

## Tasks
1. Reproduce the current gap for DOME-GRAPH-001 and capture baseline evidence.
2. Implement required changes for: TaskSpec authority guard implementation.
3. Add or update focused tests.
4. Run:
   
   `pytest -q tests/test_planner.py tests/test_security.py`
5. Write evidence artifacts under
   
   `ops/runtime/graph-001/`.

## Acceptance Checks
- Focused tests pass.
- Artifacts are schema-valid and deterministic where required.
- Progress is reflected in tracker + issue thread.

## Evidence
- `ops/runtime/graph-001/checklist.md`
- `ops/runtime/graph-001/command_output.txt`
