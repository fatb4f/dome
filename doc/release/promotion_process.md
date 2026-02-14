# Promotion Process

Required checks before promotion:
- `just validate-ssot`
- `just test`
- replay/state checks for deterministic output

Promotion policy source:
- `tools/orchestrator/promote.py`
- gate input: `ops/runtime/runs/<run_id>/gate/gate.decision.json`

Release candidate evidence:
- `run.manifest.json`
- `summary.json`
- `gate/gate.decision.json`
- `promotion/promotion.decision.json`
- `evidence/*.json`
