# EXEC_PROMPT: pkt-dome-graph-009-requirement-traceability-runner

## Scope
- Issue: DOME-GRAPH-009
- GitHub issue: #53
- Milestone: M4: Traceability and CI Hard Gates
- Requirements: CL-REQ-0001, CL-REQ-0002, CL-REQ-0003, CL-REQ-0004, CL-REQ-0005
- Depends on: DOME-GRAPH-008

## Tasks
1. Reproduce the current gap for DOME-GRAPH-009 and capture baseline evidence.
2. Implement required changes for: Requirement-to-check traceability coverage runner.
3. Add or update focused tests.
4. Run:
   
   `pytest -q tests/test_ssot_policy_validate.py tests/test_schema_examples_validate.py`
5. Write evidence artifacts under
   
   `ops/runtime/graph-009/`.

## Acceptance Checks
- Focused tests pass.
- Artifacts are schema-valid and deterministic where required.
- Progress is reflected in tracker + issue thread.

## Evidence
- `ops/runtime/graph-009/checklist.md`
- `ops/runtime/graph-009/command_output.txt`
