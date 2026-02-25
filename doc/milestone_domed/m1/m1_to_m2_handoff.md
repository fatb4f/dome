# M1 -> M2 Handoff Package

Issue handoff: `#57` -> `#58`  
Depends on: `#61` (Runtime Contract Freeze, decision-only)  
Last updated: 2026-02-25

## Objective

Provide M2 with an explicit API-freeze target list that traces directly to M1 reuse and delta decisions.

## Required M2 service items

| M2 service item | Source in M1 | Notes |
| --- | --- | --- |
| `ListCapabilities` | `m1_contract_reuse_matrix.md` + `DLT-003` | Must include server/api/schema versions and feature flags. |
| `SkillExecute` entrypoint | `DLT-001`, `DLT-002` | Canonical single-entry invocation path for runtime execution. |
| `GetJobStatus` | `task.result` extend decision + `DLT-002` | Must preserve stable status mapping. |
| `CancelJob` | `DLT-001` lifecycle semantics | Must be idempotent and deterministic under retries. |
| `StreamJobEvents` | `event.envelope` extend + `DLT-006` | Cursor/resume semantics must be frozen in v1. |
| `GetGateDecision` reference surface | `gate.decision` reuse | Artifact reference and status semantics remain policy-plane output. |
| `GetPromotionDecision` reference surface | `promotion.decision` reuse | Artifact reference and risk/confidence semantics remain policy-plane output. |

## Required M2 data model constraints

| Constraint | Source |
| --- | --- |
| Distinct RPC error namespace from policy reason codes | `DLT-004` |
| Canonical run provenance fields linked to `run.manifest` | `DLT-005` |
| Identifier conventions (`run_id`, `task_id`, `event_id`, correlation ids) | `m1_dependency_matrix.md` D3 |
| Reuse-only contract policy and no duplicate families | `m1_contract_reuse_matrix.md` guardrails |

## M2 acceptance linkage requirements

- M2 proto/service definitions must reference this handoff file in issue body and PR notes.
- Every new proto message must map to:
  - one reused SSOT family, or
  - one M1 delta-register row with rationale.
- M2 must not introduce untracked contract families.

