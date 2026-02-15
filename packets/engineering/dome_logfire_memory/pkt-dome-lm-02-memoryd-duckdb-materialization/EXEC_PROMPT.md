# EXEC_PROMPT: pkt-dome-lm-02-memoryd-duckdb-materialization

## Scope
- Milestone: LM-02 - memoryd + DuckDB materialization
- Tracker issue: #26
- Depends on: LM-01

## Tasks
1. Add DuckDB schema DDL for long-horizon memory tables.
2. Add `memoryd` daemon skeleton with checkpointed ingestion loop.
3. Add tests for deterministic/idempotent checkpoint behavior.
4. Run `just test`.
5. Write evidence artifacts under `ops/runtime/lm-02/`.

## Acceptance Checks
- `just test` passes.
- `memoryd` supports one-shot mode and checkpoint persistence.
- DuckDB schema file defines run/task/event/feature tables.

## Evidence
- `ops/runtime/lm-02/checklist.md`
- `ops/runtime/lm-02/command_output.txt`
