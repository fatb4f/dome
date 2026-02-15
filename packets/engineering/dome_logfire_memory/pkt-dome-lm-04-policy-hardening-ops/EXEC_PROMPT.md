# EXEC_PROMPT: pkt-dome-lm-04-policy-hardening-ops

## Scope
- Milestone: LM-04 - Policy hardening + ops
- Tracker issue: #26
- Depends on: LM-02, LM-03

## Tasks
1. Add retention/redaction policy docs for long-horizon memory storage.
2. Add memory ops runbook and DB hygiene conventions.
3. Add a memory health alert gate and tests.
4. Run `just test`.
5. Write evidence artifacts under `ops/runtime/lm-04/`.

## Acceptance Checks
- `just test` passes.
- `.gitignore` excludes generated memory DB outputs.
- Memory health gate script is available and tested.

## Evidence
- `ops/runtime/lm-04/checklist.md`
- `ops/runtime/lm-04/command_output.txt`
