# EXEC_PROMPT: pkt-dome-xa-07-pattern-catalog-rank-policy

## Scope
- Milestone: XA-07 - Runtime config to pattern catalog/rank policy
- Tracker issue: #20
- Depends on: XA-02

## Tasks
1. Reproduce current gap for XA-07 and capture baseline evidence.
2. Implement the required alignment deliverables in-repo.
3. Add or update tests to enforce behavior.
4. Run `just validate-ssot && just test`.
5. Write evidence artifacts under `ops/runtime/xa-07/`.

## Acceptance Checks
- `just validate-ssot` passes
- `just test` passes
- milestone checklist is fully checked in issue #20

## Evidence
- `ops/runtime/xa-07/checklist.md`
- `ops/runtime/xa-07/command_output.txt`
