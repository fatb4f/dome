# M1 Contract Reuse Matrix

Issue: `#57`  
Depends on: `#61` (Runtime Contract Freeze, decision-only)  
Last updated: 2026-02-25

## Purpose

Identify which existing `dome` contract families are reused as-is for gateway work, which are extended, and which require new schema families.

## Matrix

| Contract family | Intent class | Canonical owner | Stability tier | Candidate gateway usage | Decision | Wire mapping pointer | Representation deltas | Version policy | Rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `work.queue` | job/invocation | SSOT (`dome`) | stable/v1 | Internal planning artifact for gateway jobs | extend | `Gateway.SubmitJob` internal mapping input | `budgets`/task graph to rpc options | additive only | Reuse core queue semantics, add linkage only if needed. |
| `task.result` | status | SSOT (`dome`) | stable/v1 | Base execution result envelope | extend | `Gateway.GetJobStatus` result payload | map status/reasons to rpc status + details | additive only | Keep status shape; gateway needs transport-oriented wrappers. |
| `gate.decision` | status/decision | SSOT (`dome`) | stable/v1 | Post-run policy decision artifact | reuse | `Gateway.GetGateDecision` artifact ref | none | non-breaking only | Already aligned with decision semantics. |
| `promotion.decision` | status/decision | SSOT (`dome`) | stable/v1 | Promotion artifact after execution | reuse | `Gateway.GetPromotionDecision` artifact ref | none | non-breaking only | Already captures decision/risk/confidence linkage. |
| `run.manifest` | event/log + provenance | SSOT (`dome`) | stable/v1 | Canonical run provenance record | extend | shared in all terminal job responses | provenance subrecord freeze from `#61` | additive only | Preserve existing structure while freezing required fields. |
| `event.envelope` / `control.event` | event/log | SSOT (`dome`) | stable/v1 | Stream event/log frame | extend | `Gateway.StreamJobEvents` | explicit cursor/sequence semantics | additive + behavior-stable | Reuse identity fields and formalize resume contract. |
| `spawn.spec` | job/invocation | SSOT (`dome`) | stable/v1 | Internal execution binding for jobs | reuse | internal daemon runtime only | none | non-breaking only | Determinism/task binding already applies. |
| `runtime.config` | resource spec | SSOT (`dome`) | stable/v1 | Gateway runtime defaults/config | reuse | daemon config load endpoint/internal | none | non-breaking only | Directly maps to runtime configuration needs. |
| `orchestrator.secure_defaults` | policy | SSOT (`dome`) | stable/v1 | Gateway secure runtime defaults | reuse | daemon startup policy validation | none | non-breaking only | Same safety boundary requirements. |
| `reason.codes` | error/reason catalog | SSOT (`dome`) | stable/v1 | Policy reason catalog for decisions | extend | referenced by gate/promotion responses | separate from rpc transport errors | additive only | Keep policy reasons distinct from rpc error namespace. |
| `evidence.capsule` / `evidence.bundle.telemetry` | event/log evidence | SSOT (`dome`) | experimental | Optional evidence export | reuse | `Gateway.GetEvidenceCapsule` or artifact refs | none | controlled by tier | Remains downstream evidence layer; no core rpc coupling required. |
| `control.strategies` / `profile.catalog.map` | resource/policy | SSOT (`dome`) | internal | Capability/routing policy input | extend | `Gateway.ListCapabilities` policy derivation | profile-to-capability mapping | additive only | Reusable policy source with explicit mapping layer. |
| `skill-execute` envelope | job/invocation | Gateway (`dome`) | stable/v1 (new) | Canonical task execution entrypoint | new | `Gateway.SkillExecute` | define canonical request/response + errors | freeze in v1 | Required by `#61` target model. |
| Capability discovery envelope | resource spec | Gateway (`dome`) | stable/v1 (new) | `gw-daemon` discovery/version negotiation | new | `Gateway.ListCapabilities` | include versions/schema/features fields | freeze in v1 | Required by `#61` target model. |
| Gateway wire API (proto/OpenAPI) | transport | Gateway (`dome`) | stable/v1 (new) | Canonical daemon interface | new | proto service + optional REST bridge | proto/json mapping table required | freeze + compatibility gates | Required by `#58`; no existing wire family. |
| RPC error namespace + mapping | error | Gateway (`dome`) | stable/v1 (new) | Typed rpc failure semantics | new | shared rpc status/error detail envelope | strict map to transport status + codes | freeze + additive only | Must not overload policy reason codes. |

## Reuse policy

- `reuse`: schema can be consumed without shape changes.
- `extend`: keep family identity; only additive, backward-compatible changes.
- `new`: create only when no existing family can express required semantics.

## Guardrails

- No duplicate schema family may be introduced when a `reuse` or `extend` path exists.
- All `new` rows require explicit non-reuse rationale and downstream consumer mapping.
- Every row must have an explicit version policy entry and wire mapping pointer before M2 freeze.
