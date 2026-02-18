# EXEC_PROMPT: pkt-dome-graph-002-toolcontract-method-boundary

## Scope
- Issue: DOME-GRAPH-002
- GitHub issue: #46
- Milestone: M1: Authority and Contracts Baseline
- Requirements: CL-REQ-0002
- Depends on: DOME-GRAPH-001

## Tasks
1. Reproduce the current gap for DOME-GRAPH-002 and capture baseline evidence.
2. Implement required changes for: ToolContract allowlist + boundary enforcement.
3. Add or update focused tests.
4. Run:
   
   `pytest -q tests/test_security.py tests/test_dispatcher.py`
5. Write evidence artifacts under
   
   `ops/runtime/graph-002/`.

## Acceptance Checks
- Focused tests pass.
- Artifacts are schema-valid and deterministic where required.
- Progress is reflected in tracker + issue thread.

## Evidence
- `ops/runtime/graph-002/checklist.md`
- `ops/runtime/graph-002/command_output.txt`
