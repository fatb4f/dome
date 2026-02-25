# M2 Contract Delta Register

Issue: `#58`  
Depends on: `#61`, `#57`  
Last updated: 2026-02-25

## Purpose

Track M2-specific API-freeze deltas that must be resolved before daemon/runtime implementation.

## Delta register

| Delta ID | Delta | Why needed | Input from M1 | Compatibility policy | Consumer |
| --- | --- | --- | --- | --- | --- |
| M2-DLT-001 | Proto package and service namespace definition | No wire contract currently exists | `m1_to_m2_handoff.md` | v1 freeze, additive fields only post-freeze | `#59`, `#60` |
| M2-DLT-002 | `SkillExecute` message schema set | Required single-entry runtime invocation | `DLT-001`, `DLT-002` | no breaking changes in v1 | `#59`, `#60` |
| M2-DLT-003 | Capability discovery message schema set | Required runtime discovery/negotiation | `DLT-003` | required version fields and stable semantics | `#59`, `#60` |
| M2-DLT-004 | RPC error namespace + transport mapping | Separate runtime errors from policy reasons | `DLT-004` | stable enum namespace; additive-only extension | `#59`, `#60` |
| M2-DLT-005 | Stream cursor/resume contract freeze text | Deterministic reconnect behavior required | `DLT-006` | behavior-stable in v1 | `#59`, `#60` |
| M2-DLT-006 | Provenance contract wire mapping notes | Runtime must emit canonical provenance | `DLT-005` | preserve run.manifest alignment | `#59`, `#60` |
| M2-DLT-007 | Codegen policy and pin artifacts | Reproducible clients required | `m1_ci_enforcement_mapping.md` | deterministic generation + drift checks | `#60` |

## Notes

- M2 does not implement runtime behavior; it freezes contract shape and compatibility policy.
- Any additional message family beyond this register requires explicit update to M2 docs and issue acceptance criteria.

