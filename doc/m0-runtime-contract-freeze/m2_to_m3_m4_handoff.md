# M2 -> M3/M4 Handoff Package

Issue handoff: `#58` -> `#59`, `#60`  
Depends on: `#61`, `#57`  
Last updated: 2026-02-25

## Objective

Provide implementation-ready contract outputs from M2 for runtime and client milestones.

## Handoff payload

| Handoff item | Required by | Purpose |
| --- | --- | --- |
| Frozen proto service definition | `#59`, `#60` | Single source of truth for runtime and client implementation |
| Message contract mapping to M1 rows | `#59`, `#60` | Prevent semantic drift from M1 decisions |
| Frozen RPC error namespace | `#59`, `#60` | Stable retry and failure handling behavior |
| Cursor/resume stream contract | `#59`, `#60` | Deterministic event/log streaming behavior |
| Codegen reproducibility policy and pins | `#60` | Deterministic thin-client generation |
| Drift/breaking gate definitions | `#59`, `#60` | Enforce frozen API boundary in implementation |

## Mandatory M3 adoption points

- Runtime handlers must implement only frozen M2 RPC surfaces.
- Runtime must not alter message semantics in handler code.
- Runtime must emit provenance and stream fields compatible with frozen contracts.

## Mandatory M4 adoption points

- Clients/SDK must be generated from frozen M2 contract.
- Wrapper behavior (retries, stream reconnect, negotiation) must use frozen error and stream semantics.
- CI must fail if generated outputs drift from frozen contract artifacts.

## Exit condition linkage

- `#59` and `#60` must reference this handoff file in closure evidence.

