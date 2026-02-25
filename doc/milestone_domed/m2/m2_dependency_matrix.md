# M2 Dependency Matrix

Issue: `#58`  
Depends on: `#61`, `#57`  
Last updated: 2026-02-25

## M2 internal dependencies

| ID | Work package | Depends on | Produces |
| --- | --- | --- | --- |
| M2-D1 | Proto package/service boundary definition | M1 handoff | proto surface base |
| M2-D2 | RPC message contract freeze (`SkillExecute`, status, cancel, stream) | M2-D1 | v1 message set |
| M2-D3 | Capability discovery contract freeze | M2-D1 | discovery message set |
| M2-D4 | RPC error namespace + mapping definition | M2-D1 | stable runtime error model |
| M2-D5 | Compatibility policy + change classes | M2-D2, M2-D3, M2-D4 | API evolution policy |
| M2-D6 | Codegen pinning and reproducibility contract | M2-D2, M2-D3, M2-D4 | deterministic codegen path |
| M2-D7 | CI gate plan for drift/breaking/smoke | M2-D5, M2-D6 | enforceable M2 gates |
| M2-D8 | M3/M4 handoff package | M2-D1..M2-D7 | downstream implementation packet |

## Cross-milestone dependencies

| Consumer issue | Requires from M2 | Blocked until |
| --- | --- | --- |
| `#59` M3 domed Runtime MVP | frozen proto/message contracts + error model + stream semantics | M2-D8 |
| `#60` M4 clients/SDK/CI | frozen proto + codegen policy + drift checks | M2-D8 |

## Artifact mapping

| Artifact | Covers |
| --- | --- |
| `m2_gateway_api_spec_freeze_analysis.md` | baseline, gaps, phased plan |
| `m2_proto_surface_matrix.md` | RPC/message freeze target |
| `m2_contract_delta_register.md` | M2-specific contract deltas |
| `m2_dependency_matrix.md` | internal + cross-milestone dependencies |
| `m2_ci_codegen_enforcement_mapping.md` | CI and codegen enforcement map |
| `m2_to_m3_m4_handoff.md` | downstream implementation handoff |

