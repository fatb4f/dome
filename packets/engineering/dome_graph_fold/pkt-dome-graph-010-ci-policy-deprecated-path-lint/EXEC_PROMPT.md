# EXEC_PROMPT: pkt-dome-graph-010-ci-policy-deprecated-path-lint

## Scope
- Issue: DOME-GRAPH-010
- GitHub issue: #54
- Milestone: M4: Traceability and CI Hard Gates
- Requirements: CL-REQ-0001, CL-REQ-0002, CL-REQ-0003, CL-REQ-0004, CL-REQ-0005
- Depends on: DOME-GRAPH-009

## Tasks
1. Reproduce the current gap for DOME-GRAPH-010 and capture baseline evidence.
2. Implement required changes for: CI policy gates + deprecated path lint enforcement.
3. Add or update focused tests.
4. Run:
   
   `pytest -q tests/test_ops_tools.py tests/test_schema_examples_validate.py`
5. Write evidence artifacts under
   
   `ops/runtime/graph-010/`.

## Acceptance Checks
- Focused tests pass.
- Artifacts are schema-valid and deterministic where required.
- Progress is reflected in tracker + issue thread.

## Evidence
- `ops/runtime/graph-010/checklist.md`
- `ops/runtime/graph-010/command_output.txt`
