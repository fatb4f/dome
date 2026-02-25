# M2 CI and Codegen Enforcement Mapping

Issue: `#58`  
Depends on: `#61`, `#57`  
Last updated: 2026-02-25

## Purpose

Define the enforcement gates required to keep the proto-first API freeze deterministic and non-breaking.

## Gate map

| Gate ID | Enforcement target | Rule | Target milestone owner |
| --- | --- | --- | --- |
| M2-CI-001 | Proto drift check | Regenerated artifacts must match committed outputs. | `#58` |
| M2-CI-002 | Proto breaking-change check | Contract changes must pass breaking-compat policy. | `#58` |
| M2-CI-003 | Schema/API alignment check | RPC message fields must map to M1 reuse/delta decisions. | `#58` |
| M2-CI-004 | Error model conformance | RPC error namespace must remain separate from policy reason codes. | `#58` |
| M2-CI-005 | Codegen reproducibility | Toolchain versions and generation command are pinned. | `#58` |
| M2-CI-006 | Consumer smoke contract | Generated client can call required RPC surfaces in smoke harness. | `#60` |
| M2-CI-007 | Handoff integrity | M3/M4 implementation references frozen M2 artifacts. | `#59`, `#60` |

## Required artifacts for enforcement

- Canonical proto files and package layout.
- Codegen manifest (tool versions + commands).
- Compatibility policy document for change classes.
- Mapping table from proto messages to M1 contract rows.

## Ownership notes

- `#58` defines and locks the gate definitions.
- `#59` and `#60` consume these gates; they must not redefine M2 freeze semantics.

