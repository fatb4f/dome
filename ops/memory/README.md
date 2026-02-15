# ops/memory

This directory hosts generated long-horizon memory artifacts for telemetry materialization.

## Layout

- `memory.duckdb`: generated DuckDB database (ignored by git)
- `checkpoints/`: generated daemon checkpoint state (ignored by git)

## Primary Commands

1. One-shot materialization:
   - `python tools/telemetry/memoryd.py --once`
2. Continuous daemon loop:
   - `python tools/telemetry/memoryd.py --poll-seconds 10`
3. Health gate:
   - `python tools/telemetry/memory_alert_gate.py --checkpoint ops/memory/checkpoints/materialize.state.json --min-processed-runs 1`

## Operational Notes

- This directory is runtime-generated; only this README is intended for source control.
- Curated evidence for milestones belongs under `ops/runtime/m*/`.

