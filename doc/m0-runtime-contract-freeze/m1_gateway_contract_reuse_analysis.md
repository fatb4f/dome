# M1 Gateway Contract Reuse: Baseline, Gaps, Dependencies, Plan

Issue: `#57`  
Depends on: `#61` (Runtime Contract Freeze, decision-only)  
Date: 2026-02-25

## 1) Baseline: What Is Already Defined in `dome`

### 1.1 Existing SSOT contract families

| Contract family | Primary schema(s) | Current intent class |
| --- | --- | --- |
| Plan/queue | `ssot/schemas/work.queue.schema.json` | job/invocation |
| Task output | `ssot/schemas/task.result.schema.json` | status/result |
| Gate | `ssot/schemas/gate.decision.schema.json` | status/decision |
| Promotion | `ssot/schemas/promotion.decision.schema.json` | status/decision |
| Run provenance (current) | `ssot/schemas/run.manifest.schema.json` | event/log + provenance |
| Event envelope | `ssot/schemas/event.envelope.schema.json`, `control.event.schema.json` | event/log |
| Spawn envelope | `ssot/schemas/spawn.spec.schema.json` | invocation/runtime binding |
| Runtime config | `ssot/schemas/runtime.config.schema.json` | resource spec |
| Secure defaults | `ssot/schemas/orchestrator.secure_defaults.schema.json` | policy |
| Reason catalog | `ssot/schemas/reason.codes.schema.json` | error/reason catalog |
| Evidence | `ssot/schemas/evidence.capsule.schema.json`, `evidence.bundle.telemetry.schema.json` | event/log evidence |
| Strategy/profile catalog | `ssot/schemas/control.strategies.schema.json`, `profile.catalog.map.schema.json` | resource/policy |

### 1.2 Existing runtime/tooling surfaces

| Surface | Files | Notes |
| --- | --- | --- |
| Orchestrator pipeline | `tools/orchestrator/*` | Script-driven PIV/MCP flows already emit schema-backed artifacts. |
| Contract validation | `tests/test_schema_examples_validate.py`, `tests/test_ssot_policy_validate.py` | Schema/example gates exist. |
| Skill wrapper bridge | `tools/codex/dome_cli.py`, `tools/codex/browse_skill.py` | Contract-validated wrapper for `codex-browse`; no `domed` runtime yet. |
| Contract pinning | `ssot/pins/xtrlv2/*`, `tests/test_xtrlv2_contract_pin.py` | Upstream pin model exists and is reusable. |

### 1.3 Existing intent mapping (resource/job/event/error)

| Intent class | Already covered | Missing for gateway target model |
| --- | --- | --- |
| resource spec | runtime config, secure defaults, profile map | tool manifest contract for API-first gateway |
| job/invocation | work queue, spawn spec | canonical `skill-execute` request/response contract |
| status | task result, gate decision, promotion decision | transport-level rpc status/error envelope |
| event/log | event envelope, evidence capsule, run manifest | stream cursor/resume contract for gateway streams |
| error | reason codes (policy/gate-oriented) | gateway rpc error namespace + grpc status mapping |

## 2) Gap Analysis Against Target Model (`#61` -> `#57`)

### 2.1 Required by target model but missing/partial

| Required target contract | Current state | Gap |
| --- | --- | --- |
| `skill-execute` entrypoint contract | Not defined in SSOT | Missing schema family |
| Capability discovery contract (`domed`) | Mentioned in docs/comments only | Missing schema + wire contract |
| API-first gateway contract (proto/openapi) | None in `dome` | Missing canonical wire spec |
| Thin-client-only invocation policy | Policy intent stated in issues | Missing enforceable contract + CI rule definition |
| Canonical run provenance record | `run.manifest` exists but not frozen to target fields from `#61` | Partial; needs explicit field freeze |
| Idempotency contract for gateway submissions | Idempotency behavior exists in telemetry/orchestrator paths | Missing gateway-level request semantics |
| Stability tiers/ownership per schema | Implicit only | Missing declared ownership/stability metadata |
| Reuse-only guard | No explicit "no duplicate schema family" gate | Missing policy/check definition |

### 2.3 Missing-contract resolution checklist

- [ ] `skill-execute` entrypoint resolved by reuse/extend/new decision.
- [ ] Capability discovery contract resolved by reuse/extend/new decision.
- [ ] API-first gateway wire contract path frozen (proto/openapi).
- [ ] Thin-client-only invocation policy encoded as enforceable checks.
- [ ] Canonical run provenance record fields frozen and mapped to `run.manifest`.
- [ ] Idempotency submission semantics frozen.
- [ ] Ownership/stability metadata attached for each reused family.
- [ ] Reuse-only duplication guard defined for CI/runtime.

### 2.2 Areas with overlap risk

| Overlap risk | Why risky | Mitigation in M1 |
| --- | --- | --- |
| New gateway schema duplicates existing SSOT concept | Creates drift and dual authority | Create reuse matrix first, add "reused vs new" decision with rationale |
| Reason codes reused as RPC errors without mapping | Semantics differ (policy reason vs transport error) | Freeze separate rpc error namespace + mapping table |
| Run manifest and provenance record diverge | Reproducibility/reporting inconsistency | Define one canonical provenance section and update schema once |
| Dispatcher/tool contract checks diverge from gateway capability model | Runtime policy mismatch | Map existing tool contract checks to capability discovery semantics |

## 3) Dependency Matrix

### 3.1 Work packages for M1 (`#57`)

| ID | Work package | Depends on | Enables |
| --- | --- | --- | --- |
| D1 | Build SSOT reuse inventory by intent class | none | D2, D3 |
| D2 | Define ownership + stability tier for each reused contract | D1 | D4, D5 |
| D3 | Define identifier mapping (`run_id`, `task_id`, `event_id`, correlation ids) | D1 | D5, D6 |
| D4 | Define reuse rules and "no duplicate schema family" policy | D2 | D7 |
| D5 | Define representation mapping (JSON schema <-> proto fields/types) | D2, D3 | M2 API freeze (`#58`) |
| D6 | Define canonical provenance record and mapping to `run.manifest` | D3 | M2 (`#58`), M3 (`#59`) |
| D7 | Define CI gate specification (reuse-only check + schema compatibility checks) | D4 | M2 (`#58`), M4 (`#60`) |
| D8 | Publish M1 contract reuse matrix + delta register | D1-D7 | M2-M4 execution |

### 3.2 Cross-issue dependency handoff

| Downstream issue | M1 artifact consumed | Why |
| --- | --- | --- |
| `#58` API Spec Freeze | D5, D6, D8 | API fields and versions must align to reused contracts and provenance rules |
| `#59` Daemon MVP | D3, D6, D8 | Runtime identifiers and provenance emission depend on frozen mapping |
| `#60` Clients/SDK/CI | D4, D7, D8 | Thin-client policy and CI enforcement depend on reuse and compatibility rules |

## 4) Plan for Issue `#57`

### Phase P1: Baseline and classification

- Produce contract reuse matrix with columns:
  - `contract_family`
  - `intent_class` (`resource_spec|status|job_invocation|event_log|error`)
  - `owner`
  - `stability_tier` (`stable/v1|experimental|internal`)
  - `current_usage`
  - `candidate_gateway_usage`
  - `decision` (`reuse|extend|new`)
  - `rationale`

Outputs:
- `doc/m0-runtime-contract-freeze/m1_contract_reuse_matrix.md` (new)

### Phase P2: Gap decisions and delta register

- Create delta register for contracts not reusable as-is:
  - `skill-execute` envelope
  - capability discovery envelope
  - rpc error namespace + mapping
  - provenance record freeze
- For each delta, declare:
  - authority owner
  - compatibility rule
  - downstream consumer(s)

Outputs:
- `doc/m0-runtime-contract-freeze/m1_contract_delta_register.md` (new)

### Phase P3: Dependency and CI policy definition

- Define dependency matrix and gate policy:
  - no duplicate schema family
  - schema evolution requirements per tier
  - required checks before merging M2+ changes
- Define CI enforcement mapping:
  - schema/example validation gate
  - proto compatibility gate (breaking-change detection)
  - reuse-only duplication guard
  - provenance contract presence/shape gate
  - thin-client-only invocation policy gate

Outputs:
- `doc/m0-runtime-contract-freeze/m1_dependency_matrix.md` (new) or fold into this doc
- `doc/m0-runtime-contract-freeze/m1_ci_enforcement_mapping.md` (new)
- issue `#57` body update with closure checklist linked to concrete files

### Phase P4: Handoff package to M2-M4

- Create handoff section that is directly consumed by `#58-#60`:
  - field-level mapping baseline for proto freeze
  - provenance constraints
  - id/correlation conventions
  - CI gate contract
  - M2 proto/service item list: capabilities, skill-execute, submit/status/cancel, stream events/logs

Outputs:
- Issue comment on `#57` referencing final M1 artifacts and ready-for-M2 gate
- `doc/m0-runtime-contract-freeze/m1_to_m2_handoff.md` (new)

## 5) Verification Criteria for Closing `#57`

- Reuse matrix exists and is complete for all current SSOT schemas.
- Every "new" contract has explicit non-reuse rationale.
- Dependency matrix ties each M1 output to M2/M3/M4 consumers.
- `#57` checklist is updated with file-backed evidence paths.
