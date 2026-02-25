# M5-D3 Adapter Resolution

## Goal

Resolve all `ADAPTER_REQUIRED` entries from the migration register by either:

- migrating to daemonized thin-client execution, or
- reclassifying with explicit rationale.

## Resolution outcome

Current register contains **zero** `ADAPTER_REQUIRED` rows.

### Reclassified entries

1. `tools/codex/browse_skill.py` legacy subprocess callsite
- D3 class: `DEPRECATE_REMOVE`
- D8 status: removed from codebase and register.

2. `tools/orchestrator/checkers.py:71`
3. `tools/orchestrator/run_demo.py:65`
4. `tools/orchestrator/run_live_fix_demo.py:51`
5. `tools/orchestrator/run_plan_implement_verify.py:51`
6. `tools/orchestrator/run_plan_implement_verify.py:68`
- New class: `KEEP_LOCAL`
- Rationale: orchestrator demo/ops harnesses are non-production utilities and intentionally rely on local subprocess behavior for deterministic fixture/control checks. They are not production runtime entrypoints.

## Migration principle maintained

- Production paths remain thin-client only (`dome-codex-skill run-skill` -> `DomedClient` -> `domed`).
- Non-production local harnesses are explicitly tracked and bounded in the register.
