# M1 Contract Delta Register

Issue: `#57`  
Depends on: `#61` (Runtime Contract Freeze, decision-only)  
Last updated: 2026-02-25

## Purpose

Track contract deltas required for gateway adoption that are not covered by existing SSOT families.

## Delta register

| Delta ID | Contract delta | Why SSOT insufficient | Minimum v1 surface | Upstream candidate evaluated | Migration/merge plan | Risk | Compatibility rule | Downstream consumers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DLT-001 | `skill-execute` request envelope | No existing canonical single-entry execution envelope | `skill_id`, `task`, `constraints`, `idempotency_key` | `work.queue`, `spawn.spec` | keep gateway-owned; may fold into SSOT job family later | medium | New v1 schema; additive fields only after freeze | `#58`, `#59`, `#60` |
| DLT-002 | `skill-execute` response envelope | `task.result` lacks transport-level status and artifact handle semantics | `ok/status`, `run_id`, `artifacts`, `error`, `cursor` | `task.result`, `run.manifest` | extend mapping layer; preserve `task.result` compatibility | medium | Backward-compatible extension via mapping | `#58`, `#60` |
| DLT-003 | Capability discovery contract | No schema defines daemon capability/version negotiation fields | `server_version`, `api_versions`, `supported_job_types`, `schema_versions`, `feature_flags` | `profile.catalog.map`, `runtime.config` | gateway-owned with SSOT pin references | medium | New v1 schema; explicit version required | `#58`, `#59`, `#60` |
| DLT-004 | Gateway rpc error namespace | `reason.codes` is policy/gate-oriented, not transport/runtime | stable rpc code enum + transport mapping table | `reason.codes` | keep separate namespace; maintain cross-map doc | high | Stable namespace, additive-only changes | `#58`, `#59`, `#60` |
| DLT-005 | Canonical run provenance record freeze | `run.manifest` exists but fields from `#61` are not frozen as mandatory set | `{repo, commit_sha, dirty_flag, contract_hashes, tool_versions, input_hash, env_fingerprint}` | `run.manifest` | extend existing schema; do not fork new provenance family | high | Additive fields only; no removal of requireds | `#58`, `#59`, `#60` |
| DLT-006 | Stream cursor/resume contract | Event envelope exists, resume behavior not frozen | monotonic `seq`, cursor semantics, gap handling | `event.envelope`, `control.event` | extend event contract usage; no new event family | high | Cursor behavior frozen in v1; no breaking semantics | `#58`, `#59`, `#60` |
| DLT-007 | Thin-client-only invocation policy contract | Current policy is issue text only, no enforceable contract | allowlist of approved client surfaces + violation response | none | policy in CI/runtime guards; no schema fork | medium | Policy gate definition in CI + runtime checks | `#59`, `#60` |
| DLT-008 | Contract change classification policy | No formal classification for what counts as contract mutation | change-class matrix (`proto`, `schema`, `manifest`) + required gates | existing SSOT governance | adopt under M1 governance docs and CI policy | low | Any contract change requires compatibility gates | `#58`, `#60` |

## Decision notes

- `DLT-001` and `DLT-003` are canonical new families and should be created in the gateway spec freeze (`#58`).
- `DLT-004` must remain separate from policy reason catalog to prevent semantic coupling.
- `DLT-005` should reuse current `run.manifest` structure and only freeze/extend required provenance fields.

## Required checks (handoff to M2/M4)

- Schema/API drift check for all new and extended contracts.
- Backward-compatibility check for all `extend` deltas.
- Reuse-only check to fail if a duplicate family is created for an existing reusable contract.
- Delta records must include explicit SSOT candidate evaluation and risk classification.
