# EXEC_PROMPT: pkt-dome-xa-10-pattern-catalog-ingest

## Scope
- Milestone: XA-10 - Pattern catalog ingestion pipeline
- Tracker issue: #23
- Depends on: XA-01

## Tasks
1. Reproduce current gap for XA-10 and capture baseline evidence.
2. Implement the required alignment deliverables in-repo.
3. Add or update tests to enforce behavior.
4. Run `just validate-ssot && just test`.
5. Write evidence artifacts under `ops/runtime/xa-10/`.

## Acceptance Checks
- `just validate-ssot` passes
- `just test` passes
- milestone checklist is fully checked in issue #23

## Evidence
- `ops/runtime/xa-10/checklist.md`
- `ops/runtime/xa-10/command_output.txt`
