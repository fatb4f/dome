# EXEC_PROMPT: pkt-dome-xa-09-state-migration-bridge

## Scope
- Milestone: XA-09 - State migration bridge
- Tracker issue: #22
- Depends on: XA-05

## Tasks
1. Reproduce current gap for XA-09 and capture baseline evidence.
2. Implement the required alignment deliverables in-repo.
3. Add or update tests to enforce behavior.
4. Run `just validate-ssot && just test`.
5. Write evidence artifacts under `ops/runtime/xa-09/`.

## Acceptance Checks
- `just validate-ssot` passes
- `just test` passes
- milestone checklist is fully checked in issue #22

## Evidence
- `ops/runtime/xa-09/checklist.md`
- `ops/runtime/xa-09/command_output.txt`
