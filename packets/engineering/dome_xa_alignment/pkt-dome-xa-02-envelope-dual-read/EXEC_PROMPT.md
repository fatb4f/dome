# EXEC_PROMPT: pkt-dome-xa-02-envelope-dual-read

## Scope
- Milestone: XA-02 - Dual-read substrate envelope fields
- Tracker issue: #15
- Depends on: XA-01

## Tasks
1. Reproduce current gap for XA-02 and capture baseline evidence.
2. Implement the required alignment deliverables in-repo.
3. Add or update tests to enforce behavior.
4. Run `just validate-ssot && just test`.
5. Write evidence artifacts under `ops/runtime/xa-02/`.

## Acceptance Checks
- `just validate-ssot` passes
- `just test` passes
- milestone checklist is fully checked in issue #15

## Evidence
- `ops/runtime/xa-02/checklist.md`
- `ops/runtime/xa-02/command_output.txt`
