# M1 Contract Reuse Matrix

Issue: `#57`  
Last updated: 2026-02-25

## Purpose

Identify which existing `dome` contract families are reused as-is for gateway work, which are extended, and which require new schema families.

## Matrix

| Contract family | Intent class | Owner | Stability tier | Current usage | Candidate gateway usage | Decision | Rationale |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `work.queue` | job/invocation | `dome` | stable/v1 | Planner output for orchestrator waves | Internal planning artifact for gateway jobs | extend | Reuse core queue semantics, add gateway-specific linkage fields only if required. |
| `task.result` | status | `dome` | stable/v1 | Implementer/checker result emission | Base execution result envelope | extend | Keep status shape; gateway needs richer rpc status mapping. |
| `gate.decision` | status/decision | `dome` | stable/v1 | Deterministic gate verdicts | Post-run policy decision artifact | reuse | Semantics already match gate outcome and reason linkage. |
| `promotion.decision` | status/decision | `dome` | stable/v1 | Promotion policy output | Promotion artifact after gateway execution | reuse | Already captures decision/risk/confidence linkage. |
| `run.manifest` | provenance/event-log | `dome` | stable/v1 | Run-level command/artifact provenance | Canonical run provenance record | extend | Freeze required provenance fields from `#61` while preserving existing structure. |
| `event.envelope` / `control.event` | event/log | `dome` | stable/v1 | Event bus and replay materialization | Stream event/log frame | extend | Reuse sequence/run/event identity fields; add explicit cursor/resume semantics in gateway API. |
| `spawn.spec` | job/invocation | `dome` | stable/v1 | Worker spawn contract | Internal execution binding for gateway jobs | reuse | Core determinism/task binding is already applicable. |
| `runtime.config` | resource spec | `dome` | stable/v1 | Runtime profile defaults/config | Gateway runtime config and defaults | reuse | Directly maps to daemon configuration needs. |
| `orchestrator.secure_defaults` | policy | `dome` | stable/v1 | Path and redaction safety defaults | Gateway secure runtime defaults | reuse | Same operational safety concerns. |
| `reason.codes` | error/reason catalog | `dome` | stable/v1 | Gate/promo reason classifications | Policy-layer reason catalog for gateway decisions | extend | Keep policy reasons; define distinct RPC error namespace for transport/runtime failures. |
| `evidence.capsule` / `evidence.bundle.telemetry` | event/log evidence | `dome` | experimental | Evidence consolidation for runs | Optional gateway evidence export | reuse | Can remain downstream artifact without changing core gateway rpc contracts. |
| `control.strategies` / `profile.catalog.map` | resource/policy | `dome` | internal | Strategy ranking/profile mapping | Capability/routing policy input | extend | Reusable policy source; requires explicit mapping to gateway capability discovery. |
| `skill-execute` envelope | job/invocation | `dome` | new | Not present | Canonical task execution entrypoint | new | Required by `#61` target model. |
| Capability discovery envelope | resource spec | `dome` | new | Not present | `gw-daemon` discovery/version negotiation | new | Required by `#61` target model. |
| Gateway wire API (proto/OpenAPI) | transport | `dome` | new | Not present | Canonical daemon interface | new | Required by `#58`; no existing wire contract family. |
| RPC error namespace + mapping | error | `dome` | new | Not present | Typed rpc failure semantics | new | Must not overload policy reason codes. |

## Reuse policy

- `reuse`: schema can be consumed without shape changes.
- `extend`: keep family identity; only additive, backward-compatible changes.
- `new`: create only when no existing family can express required semantics.

## Guardrails

- No duplicate schema family may be introduced when a `reuse` or `extend` path exists.
- All `new` rows require explicit non-reuse rationale and downstream consumer mapping.
