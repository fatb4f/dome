# EXEC_PROMPT: pkt-dome-xa-06-outer-loop-tick-controller

## Scope
- Milestone: XA-06 - Outer-loop tick controller
- Tracker issue: #19
- Depends on: XA-02, XA-03

## Tasks
1. Reproduce current gap for XA-06 and capture baseline evidence.
2. Implement the required alignment deliverables in-repo.
3. Add or update tests to enforce behavior.
4. Run `just validate-ssot && just test`.
5. Write evidence artifacts under `ops/runtime/xa-06/`.

## Acceptance Checks
- `just validate-ssot` passes
- `just test` passes
- milestone checklist is fully checked in issue #19

## Evidence
- `ops/runtime/xa-06/checklist.md`
- `ops/runtime/xa-06/command_output.txt`
