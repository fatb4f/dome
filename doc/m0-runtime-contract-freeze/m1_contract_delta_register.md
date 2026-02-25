# M1 Contract Delta Register

Issue: `#57`  
Last updated: 2026-02-25

## Purpose

Track contract deltas required for gateway adoption that are not covered by existing SSOT families.

## Delta register

| Delta ID | Contract delta | Why needed | Upstream base | Compatibility rule | Downstream consumers |
| --- | --- | --- | --- | --- | --- |
| DLT-001 | `skill-execute` request envelope | Single execution entrypoint mandated by `#61` | none | New v1 schema; additive fields only after freeze | `#58`, `#59`, `#60` |
| DLT-002 | `skill-execute` response envelope | Standardized status/artifacts/errors for thin clients | `task.result` (extended) | Backward-compatible extension to `task.result` mapping | `#58`, `#60` |
| DLT-003 | Capability discovery contract | Required daemon discovery and version negotiation | `profile.catalog.map`, `runtime.config` | New v1 schema; explicit version field required | `#58`, `#59`, `#60` |
| DLT-004 | Gateway rpc error namespace | Separate transport/runtime errors from policy reason codes | `reason.codes` (reference only) | Stable enum namespace with mapping table to transport status | `#58`, `#59`, `#60` |
| DLT-005 | Canonical run provenance record freeze | Enforce git-authoritative and reproducible run metadata | `run.manifest` (extended) | Additive fields only; no removal of existing required fields | `#58`, `#59`, `#60` |
| DLT-006 | Stream cursor/resume contract | Deterministic reconnection and event replay | `event.envelope` (extended) | Cursor semantics fixed in v1, no behavior-breaking changes | `#58`, `#59`, `#60` |
| DLT-007 | Thin-client-only invocation policy contract | Enforce "if not thin client, do not use it" | none | Policy gate definition in CI + runtime checks | `#59`, `#60` |
| DLT-008 | Contract change classification policy | Enforce "if not in git, it does not exist" | existing SSOT governance | Any contract change requires schema/API compatibility gate | `#58`, `#60` |

## Decision notes

- `DLT-001` and `DLT-003` are canonical new families and should be created in the gateway spec freeze (`#58`).
- `DLT-004` must remain separate from policy reason catalog to prevent semantic coupling.
- `DLT-005` should reuse current `run.manifest` structure and only freeze/extend required provenance fields.

## Required checks (handoff to M2/M4)

- Schema/API drift check for all new and extended contracts.
- Backward-compatibility check for all `extend` deltas.
- Reuse-only check to fail if a duplicate family is created for an existing reusable contract.
