# EXEC_PROMPT: pkt-dome-xa-03-helper-event-envelope

## Scope
- Milestone: XA-03 - Schema-bound event envelope parity
- Tracker issue: #16
- Depends on: XA-02

## Tasks
1. Reproduce current gap for XA-03 and capture baseline evidence.
2. Implement the required alignment deliverables in-repo.
3. Add or update tests to enforce behavior.
4. Run `just validate-ssot && just test`.
5. Write evidence artifacts under `ops/runtime/xa-03/`.

## Acceptance Checks
- `just validate-ssot` passes
- `just test` passes
- milestone checklist is fully checked in issue #16

## Evidence
- `ops/runtime/xa-03/checklist.md`
- `ops/runtime/xa-03/command_output.txt`
