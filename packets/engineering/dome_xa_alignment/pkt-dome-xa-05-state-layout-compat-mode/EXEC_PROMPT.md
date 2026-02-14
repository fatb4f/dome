# EXEC_PROMPT: pkt-dome-xa-05-state-layout-compat-mode

## Scope
- Milestone: XA-05 - Substrate state layout compatibility mode
- Tracker issue: #18
- Depends on: XA-02

## Tasks
1. Reproduce current gap for XA-05 and capture baseline evidence.
2. Implement the required alignment deliverables in-repo.
3. Add or update tests to enforce behavior.
4. Run `just validate-ssot && just test`.
5. Write evidence artifacts under `ops/runtime/xa-05/`.

## Acceptance Checks
- `just validate-ssot` passes
- `just test` passes
- milestone checklist is fully checked in issue #18

## Evidence
- `ops/runtime/xa-05/checklist.md`
- `ops/runtime/xa-05/command_output.txt`
