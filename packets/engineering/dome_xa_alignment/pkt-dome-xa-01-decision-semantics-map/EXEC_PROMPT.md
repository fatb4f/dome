# EXEC_PROMPT: pkt-dome-xa-01-decision-semantics-map

## Scope
- Milestone: XA-01 - Decision semantics mapping
- Tracker issue: #14
- Depends on: None

## Tasks
1. Reproduce current gap for XA-01 and capture baseline evidence.
2. Implement the required alignment deliverables in-repo.
3. Add or update tests to enforce behavior.
4. Run `just validate-ssot && just test`.
5. Write evidence artifacts under `ops/runtime/xa-01/`.

## Acceptance Checks
- `just validate-ssot` passes
- `just test` passes
- milestone checklist is fully checked in issue #14

## Evidence
- `ops/runtime/xa-01/checklist.md`
- `ops/runtime/xa-01/command_output.txt`
