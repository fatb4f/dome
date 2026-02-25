# Replay A Run

Inputs:
- `run.manifest.json`
- `work.queue.json`
- `mcp_events.jsonl`

Steps:
1. Re-run deterministic pipeline with same inputs.
2. Validate produced artifacts with schema checks.
3. Compare hash chain (`work.queue`, `summary`, `gate`, `manifest`).
