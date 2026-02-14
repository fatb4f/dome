# EXEC_PROMPT: pkt-dome-xa-11-profile-catalog-mapping

## Scope
- Milestone: XA-11 - Profile-to-catalog mapping
- Tracker issue: #24
- Depends on: XA-07, XA-10

## Tasks
1. Reproduce current gap for XA-11 and capture baseline evidence.
2. Implement the required alignment deliverables in-repo.
3. Add or update tests to enforce behavior.
4. Run `just validate-ssot && just test`.
5. Write evidence artifacts under `ops/runtime/xa-11/`.

## Acceptance Checks
- `just validate-ssot` passes
- `just test` passes
- milestone checklist is fully checked in issue #24

## Evidence
- `ops/runtime/xa-11/checklist.md`
- `ops/runtime/xa-11/command_output.txt`
