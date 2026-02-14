# Run ID Contract

## Format

Recommended run ID pattern:
- `^[a-z0-9][a-z0-9._-]{2,127}$`

Examples:
- `pkt-dome-demo-0001`
- `wave-20260214-001`

## Requirements

- Must be unique per execution intent within retention horizon.
- Must appear in all event envelopes and run artifacts.
- Must be stable across replay of the same execution when deterministic provenance is required.

## Provenance Linkage

Each run ID must be traceable to:
- `run.manifest.json`
- `work.queue.json`
- `summary.json`
- gate/promotion decisions
- evidence bundle set
