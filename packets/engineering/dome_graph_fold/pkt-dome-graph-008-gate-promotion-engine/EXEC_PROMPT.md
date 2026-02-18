# EXEC_PROMPT: pkt-dome-graph-008-gate-promotion-engine

## Scope
- Issue: DOME-GRAPH-008
- GitHub issue: #52
- Milestone: M3: Wave Orchestration and Promotion Gates
- Requirements: CL-REQ-0004, CL-REQ-0005
- Depends on: DOME-GRAPH-005, DOME-GRAPH-006, DOME-GRAPH-007

## Tasks
1. Reproduce the current gap for DOME-GRAPH-008 and capture baseline evidence.
2. Implement required changes for: Deterministic gate and promotion engine with evidence linkage.
3. Add or update focused tests.
4. Run:
   
   `pytest -q tests/test_checkers.py tests/test_promote.py`
5. Write evidence artifacts under
   
   `ops/runtime/graph-008/`.

## Acceptance Checks
- Focused tests pass.
- Artifacts are schema-valid and deterministic where required.
- Progress is reflected in tracker + issue thread.

## Evidence
- `ops/runtime/graph-008/checklist.md`
- `ops/runtime/graph-008/command_output.txt`
