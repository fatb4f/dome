# EXEC_PROMPT: pkt-dome-xa-08-schema-pin-lint-gates

## Scope
- Milestone: XA-08 - Schema pin + lint gates
- Tracker issue: #21
- Depends on: XA-03

## Tasks
1. Reproduce current gap for XA-08 and capture baseline evidence.
2. Implement the required alignment deliverables in-repo.
3. Add or update tests to enforce behavior.
4. Run `just validate-ssot && just test`.
5. Write evidence artifacts under `ops/runtime/xa-08/`.

## Acceptance Checks
- `just validate-ssot` passes
- `just test` passes
- milestone checklist is fully checked in issue #21

## Evidence
- `ops/runtime/xa-08/checklist.md`
- `ops/runtime/xa-08/command_output.txt`
