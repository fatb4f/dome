# M2 Gateway API Spec Freeze: Baseline, Gaps, Dependencies, Plan

Issue: `#58`  
Depends on: `#61` (Runtime Contract Freeze, decision-only), `#57` (M1 handoff)  
Date: 2026-02-25

## 1) Baseline: What Is Already Defined in `dome`

### 1.1 Upstream inputs available from M1

- `m1_contract_reuse_matrix.md`
- `m1_contract_delta_register.md`
- `m1_dependency_matrix.md`
- `m1_ci_enforcement_mapping.md`
- `m1_to_m2_handoff.md`

These define what must be reused, extended, or introduced in the M2 API.

### 1.2 Existing contract assets in repo

| Area | Current state |
| --- | --- |
| SSOT schemas | Present under `ssot/schemas/*` |
| Runtime artifact schemas | Present (`work.queue`, `task.result`, `gate.decision`, `promotion.decision`, `run.manifest`, `event.envelope`) |
| Issue-level API intent | Defined in `#58` and `#61` |
| Gateway wire spec | Not present (no `proto/` or OpenAPI for `domed`) |
| Gateway codegen pipeline | Not present |
| Proto breaking/drift checks | Not present |

### 1.3 M2 target from M1 handoff

Required service surfaces (from `m1_to_m2_handoff.md`):

- `ListCapabilities`
- `SkillExecute`
- `GetJobStatus`
- `CancelJob`
- `StreamJobEvents`
- `GetGateDecision` (reference surface)
- `GetPromotionDecision` (reference surface)

## 2) Gap Analysis

### 2.1 Missing artifacts required for M2 closure

| Required M2 artifact | Current state | Gap |
| --- | --- | --- |
| Canonical API wire contract (proto-first) | none | missing |
| Service-level message model with versioning | none | missing |
| Typed RPC error namespace + mapping | policy reason codes only | missing |
| Compatibility policy for v1 freeze | implicit in issue text | missing formal artifact |
| Codegen reproducibility workflow | none | missing |
| Proto drift/breaking CI checks | none | missing |
| API/spec docs aligned with proto | none | missing |

### 2.2 Risks if gaps are not closed

| Risk | Impact | Mitigation in M2 |
| --- | --- | --- |
| Wire contract ambiguity | M3/M4 implementation drift | Freeze proto and message ownership early |
| Error taxonomy conflation | unstable retries and client behavior | Separate RPC error namespace from policy reason codes |
| Unpinned codegen | non-reproducible clients | lock toolchain + deterministic generation path |
| Unchecked proto evolution | breaking changes leak into runtime | add explicit breaking-change and drift gates |

## 3) Dependency Matrix

### 3.1 M2 internal work packages

| ID | Work package | Depends on | Enables |
| --- | --- | --- | --- |
| M2-D1 | Define package layout and service boundaries | M1 handoff | M2-D2, M2-D3 |
| M2-D2 | Define message contracts for all required RPCs | M2-D1 | M2-D4, M2-D5 |
| M2-D3 | Define typed RPC error namespace + status mapping | M2-D1 | M2-D5, M2-D6 |
| M2-D4 | Write API freeze spec doc aligned to proto | M2-D2, M2-D3 | M2-D7 |
| M2-D5 | Define codegen reproducibility and version pins | M2-D2, M2-D3 | M2-D7 |
| M2-D6 | Define compatibility policy and change classes | M2-D3 | M2-D7 |
| M2-D7 | Implement CI drift/breaking checks and smoke validation | M2-D4, M2-D5, M2-D6 | M2 closeout + M3/M4 start |

### 3.2 Cross-issue handoff

| Consumer issue | Requires from M2 | Why |
| --- | --- | --- |
| `#59` M3 domed Runtime MVP | frozen RPC/message contracts + error model | runtime implementation anchor |
| `#60` M4 clients/SDK/CI | codegen contract + drift/breaking policy | stable generated thin clients |

## 4) Plan for Issue `#58`

### Phase P1: Freeze surface and boundaries

- Create proto namespace and service boundary doc.
- Lock required RPC list from M1 handoff.

Outputs:
- `m2_proto_surface_matrix.md`

### Phase P2: Contract deltas and error model

- Define message-level deltas vs existing SSOT families.
- Define RPC error namespace and transport mapping.

Outputs:
- `m2_contract_delta_register.md`

### Phase P3: Compatibility + CI gate mapping

- Define codegen/toolchain pins.
- Define breaking/drift checks and ownership.

Outputs:
- `m2_ci_codegen_enforcement_mapping.md`

### Phase P4: Handoff to M3/M4

- Build explicit implementation handoff packet with required artifacts and sequencing.

Outputs:
- `m2_to_m3_m4_handoff.md`

## 5) Verification Criteria for Closing `#58`

- Proto-first contract exists and covers all M1-required service items.
- Error namespace is frozen and distinct from policy reason codes.
- Reproducible codegen path is defined and pinned.
- CI drift and breaking checks are defined and wired into issue acceptance.
