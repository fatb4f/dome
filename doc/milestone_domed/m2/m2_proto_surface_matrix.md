# M2 Proto Surface Matrix

Issue: `#58`  
Depends on: `#61`, `#57`  
Last updated: 2026-02-25

## Purpose

Define the proto-first RPC and message freeze target for `domed`, with explicit mapping to M1 inputs.

## Service surface (v1 freeze target)

| RPC | Request contract source | Response contract source | Notes |
| --- | --- | --- | --- |
| `ListCapabilities` | `DLT-003` + `runtime.config` / `profile.catalog.map` | capability discovery envelope | Must include server/api/schema versions and feature flags. |
| `SkillExecute` | `DLT-001` | `DLT-002` | Canonical single-entry runtime invocation. |
| `GetJobStatus` | `task.result` extend decision | status envelope + artifact refs | Must preserve stable status semantics for thin clients. |
| `CancelJob` | `DLT-001` lifecycle semantics | status envelope | Idempotent cancel behavior required. |
| `StreamJobEvents` | `event.envelope` extend + `DLT-006` | stream event envelope | Cursor/resume semantics are part of v1 freeze. |
| `GetGateDecision` | `gate.decision` reuse | gate decision artifact ref/envelope | Policy-plane decision surface, runtime references only. |
| `GetPromotionDecision` | `promotion.decision` reuse | promotion decision artifact ref/envelope | Policy-plane decision surface, runtime references only. |

## Shared message families

| Message family | Mapping source | Freeze rule |
| --- | --- | --- |
| Identity fields (`run_id`, `task_id`, `event_id`, correlation ids) | `m1_dependency_matrix.md` D3 | required fields in all relevant request/response/event envelopes |
| Error envelope | `DLT-004` | must remain distinct from policy reason-code schema |
| Provenance attachment | `DLT-005` | canonical provenance fields must be representable without schema fork |

## Representation mapping notes

- Timestamp fields: use one canonical wire representation and map consistently from JSON schema representations.
- Optional vs required behavior: explicit in proto message docs and compatibility policy.
- Cursor fields: define monotonic ordering and replay behavior as contract text, not implementation-only behavior.

