# EXEC_PROMPT: pkt-dome-xa-04-evidence-capsule-adapter

## Scope
- Milestone: XA-04 - Evidence capsule adapter
- Tracker issue: #17
- Depends on: XA-02

## Tasks
1. Reproduce current gap for XA-04 and capture baseline evidence.
2. Implement the required alignment deliverables in-repo.
3. Add or update tests to enforce behavior.
4. Run `just validate-ssot && just test`.
5. Write evidence artifacts under `ops/runtime/xa-04/`.

## Acceptance Checks
- `just validate-ssot` passes
- `just test` passes
- milestone checklist is fully checked in issue #17

## Evidence
- `ops/runtime/xa-04/checklist.md`
- `ops/runtime/xa-04/command_output.txt`
