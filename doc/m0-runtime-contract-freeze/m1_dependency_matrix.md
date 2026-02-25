# M1 Dependency Matrix

Issue: `#57`  
Last updated: 2026-02-25

## M1 internal dependencies

| ID | Work package | Depends on | Produces |
| --- | --- | --- | --- |
| D1 | Baseline SSOT inventory by intent class | none | Reuse inventory base |
| D2 | Ownership and stability tier assignment | D1 | Governance metadata |
| D3 | Identifier mapping (`run_id`, `task_id`, `event_id`, correlation ids) | D1 | Identity mapping baseline |
| D4 | Reuse policy and duplicate-family guard definition | D2 | Reuse gate policy |
| D5 | Representation mapping (JSON schema <-> wire fields/types) | D2, D3 | API freeze inputs |
| D6 | Canonical provenance mapping to `run.manifest` | D3 | Provenance freeze inputs |
| D7 | CI gate definition (reuse-only + compatibility checks) | D4 | M2/M4 gate requirements |
| D8 | Handoff package publication | D1-D7 | Downstream implementation package |

## Cross-milestone dependencies

| Consumer issue | Requires from M1 | Blocked until |
| --- | --- | --- |
| `#58` M2 API spec freeze | D5, D6, D7, D8 | M1 artifacts finalized and linked |
| `#59` M3 daemon MVP | D3, D6, D8 | Identifier/provenance mapping frozen |
| `#60` M4 clients/sdk/CI | D4, D7, D8 | Reuse policy + CI gates frozen |

## Artifact mapping

| Artifact | Covers |
| --- | --- |
| `m1_gateway_contract_reuse_analysis.md` | Baseline + gaps + phased plan |
| `m1_contract_reuse_matrix.md` | Reuse/extend/new decisions by contract family |
| `m1_contract_delta_register.md` | Delta scope, compatibility rules, consumers |
| `m1_dependency_matrix.md` | Internal and cross-milestone dependency structure |
