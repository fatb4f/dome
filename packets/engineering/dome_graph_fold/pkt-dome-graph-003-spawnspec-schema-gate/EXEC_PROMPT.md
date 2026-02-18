# EXEC_PROMPT: pkt-dome-graph-003-spawnspec-schema-gate

## Scope
- Issue: DOME-GRAPH-003
- GitHub issue: #47
- Milestone: M1: Authority and Contracts Baseline
- Requirements: CL-REQ-0003
- Depends on: DOME-GRAPH-001, DOME-GRAPH-002

## Tasks
1. Reproduce the current gap for DOME-GRAPH-003 and capture baseline evidence.
2. Implement required changes for: SpawnSpec schema + fail-closed dispatch gate.
3. Add or update focused tests.
4. Run:
   
   `pytest -q tests/test_planner.py tests/test_dispatcher.py tests/test_schema_examples_validate.py`
5. Write evidence artifacts under
   
   `ops/runtime/graph-003/`.

## Acceptance Checks
- Focused tests pass.
- Artifacts are schema-valid and deterministic where required.
- Progress is reflected in tracker + issue thread.

## Evidence
- `ops/runtime/graph-003/checklist.md`
- `ops/runtime/graph-003/command_output.txt`
