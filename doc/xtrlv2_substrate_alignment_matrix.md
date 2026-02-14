# xtrlv2 Substrate Alignment Matrix

Date: 2026-02-14

Scope: Align `dome` execution/runtime contracts with `xtrlv2` as execution substrate baseline.

Intent note: `dome` is an **agentic patterns consolidation repository**. Upstream pattern source is `https://github.com/nibzard/awesome-agentic-patterns/tree/main`. Alignment target is compatibility and interoperability with `xtrlv2` substrate contracts, not full contract identity or replacement of `dome` pattern-focused abstractions.

## Consolidation Source

| Source | Role in dome | Integration Requirement |
|---|---|---|
| `nibzard/awesome-agentic-patterns` | Upstream pattern corpus for curation/consolidation | Import metadata + taxonomy into a schema-bound local catalog with provenance refs |
| `xtrlv2` (`control/ssot/*`) | Execution substrate contracts and governance baseline | Map consolidated patterns to substrate-compatible runtime/policy artifacts |

## Alignment Matrix

| Area | xtrlv2 Baseline | dome Current | Status | Gap |
|---|---|---|---|---|
| Pre-contract | `control/ssot/schemas/packet_pre_contract.schema.json` (strict, includes constraints/evidence/inputs) | `ssot/schemas/demo.pre_contract.schema.json` (looser MVP) | Partial | Missing strict fields and negative constraints parity |
| Work queue contract | `control/ssot/schemas/work_queue.schema.json` (`artifact_kind`, policy linkage, pattern, budgets, meta guards) | `ssot/schemas/work.queue.schema.json` (task list + deps + status) | Gap | No policy/meta/guard linkage, different object model |
| Gate decision contract | `control/ssot/schemas/gate_decision.schema.json` (`PROMOTE/DENY/STOP`, iteration id, pointers/meta) | `ssot/schemas/gate.decision.schema.json` (`APPROVE/REJECT/NEEDS_HUMAN`) | Gap | Decision semantics + metadata model diverge |
| Run manifest contract | `control/ssot/schemas/run_manifest.schema.json` (policy, budgets, desired state, refs) | `ssot/schemas/run.manifest.schema.json` (minimal runtime summary) | Gap | Missing substrate-level policy/provenance structure |
| Reason codes | `control/ssot/reason_codes.json` + schema | `ssot/policy/reason.codes.json` + schema | Partial | Need canonical mapping/versioning against xtrlv2 registry |
| Runtime profile/patterns | pattern/rank/control strategy artifacts in `control/ssot` | `tools/orchestrator/runtime_config.py` + `ssot/schemas/runtime.config.schema.json` | Partial | Needs mapping to `pattern_catalog`/`rank_policy` contracts |
| Event schema | `helper_event.schema.json` + structured examples | JSONL event log via `EventBus` only | Gap | No schema-bound event envelope in dome |
| Evidence capsule | `evidence_capsule.schema.json` | `evidence.bundle.telemetry.schema.json` | Partial | Different schema; no canonical capsule mapping |
| State substrate | `queue/out/locks/promote/worktrees/ledger` + doctor/migrate tooling | `ops/runtime/runs/*` ad hoc layout | Gap | No substrate directories/doctor/migrate parity |
| Outer loop controller | `loop_tick.py` and migration loop state artifacts | Single-pass runner (`run_demo.py`/`run_live_fix_demo.py`) | Gap | No multi-iteration PLAN→EXEC→CHECK→GATE loop controller |
| Governance gates | schema + python quality + branch protection documented in `xtrlv2` migration docs | `mvp-loop-gate.yml` (pytest + smoke) | Partial | Missing lint/static/schema pin gates and branch policy evidence |

## Pattern-Repo Guardrails

| Principle | Why it matters for dome | Constraint on alignment work |
|---|---|---|
| Pattern-first experimentation | `dome` should incubate loop/prompt/control patterns quickly | Preserve fast iteration interfaces even when adding substrate-compatible adapters |
| Substrate interoperability | Outputs should be consumable by `xtrlv2` runtime/governance | Add translators/adapters before replacing existing pattern contracts |
| Controlled divergence | Some `dome` semantics may intentionally differ | Require explicit mapping docs and tests for each intentional divergence |
| Reproducible pattern evidence | Pattern experiments must still be auditable | Keep run manifests/event logs/schema checks for every demo mode |

## Priority Tracker

| ID | Task | Depends On | Priority | Current Status | Evidence / Note | Exit Criteria |
|---|---|---|---|---|---|---|
| XA-01 | Add substrate mapping doc for decision semantics (`PROMOTE/DENY/STOP` <-> `APPROVE/REJECT/NEEDS_HUMAN`) and intentional divergences | - | P0 | Partial | Mapping present in `doc/slo_and_release_gates.md`, but not full contract/test parity | Mapping approved and referenced by contracts/tests |
| XA-02 | Introduce optional substrate-compatible envelope fields (`artifact_kind`, policy linkage refs) into dome artifacts (backward-compatible v0.3) | XA-01 | P0 | Not Started | No dual-read substrate envelope fields in core contracts | Schemas/examples/tests pass with dual-read compatibility |
| XA-03 | Add schema-bound event envelope in dome (`helper_event` parity) | XA-02 | P0 | Mostly Done | `ssot/schemas/event.envelope.schema.json`, `ssot/examples/event.envelope.json`, `tests/test_mcp_events.py` | Event log validates against schema in CI |
| XA-04 | Add canonical evidence capsule translation (`evidence.bundle.telemetry` -> `evidence_capsule`) as adapter output | XA-02 | P1 | Not Started | No adapter/emitter for canonical evidence capsule yet | Capsule artifact emitted and schema-valid |
| XA-05 | Add substrate state layout compatibility mode (`queue/out/locks/promote/worktrees/ledger`) | XA-02 | P1 | Not Started | Runtime layout remains dome-native | `state_doctor`-style validation passes in dome runtime |
| XA-06 | Add outer-loop tick controller (`next_iter_plan` aligned) | XA-02, XA-03 | P1 | Partial | Iterative demo exists (`run_live_fix_demo.py`), no substrate-aligned loop tick controller | Iterative controller runs bounded cycles with stop rules |
| XA-07 | Align runtime config to `pattern_catalog` + `rank_policy` references while keeping pattern profiles first-class | XA-02 | P1 | Not Started | Runtime profiles exist but do not reference catalog/rank contracts | Runtime profile resolves to canonical artifact refs and preserves pattern presets |
| XA-08 | Add schema pin + lint quality gates (ruff + schema conformance) | XA-03 | P1 | Partial | Schema conformance wired; lint quality gate not yet required | CI required checks include lint + schema conformance |
| XA-09 | Build state migration bridge (`dome` runtime -> substrate layout) | XA-05 | P2 | Not Started | No migration dry-run/apply bridge artifacts yet | Deterministic dry-run/apply migration report artifacts |
| XA-10 | Add pattern-catalog ingestion pipeline from awesome-agentic-patterns (metadata + provenance) | XA-01 | P0 | Not Started | No ingestion pipeline or local versioned catalog artifact yet | Versioned local catalog artifact generated with source links/commit pin |
| XA-11 | Add mapping from consolidated patterns to runtime profiles (`tdd`, `refactor`, etc.) | XA-07, XA-10 | P1 | Not Started | No profile->catalog mapping references with rationale yet | Each runtime profile references catalog entries + rationale |

## Status Snapshot (As Of 2026-02-14)

- Done-ish:
  - XA-03 (event envelope contracts + replay/idempotency mechanics)
- Partial:
  - XA-01, XA-06, XA-08
- Not Started:
  - XA-02, XA-04, XA-05, XA-07, XA-09, XA-10, XA-11

## Dependency Matrix

`1` means row item depends on column item.

| Row \\ Col | XA-01 | XA-02 | XA-03 | XA-04 | XA-05 | XA-06 | XA-07 | XA-08 | XA-09 | XA-10 | XA-11 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| XA-01 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| XA-02 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| XA-03 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| XA-04 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| XA-05 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| XA-06 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| XA-07 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| XA-08 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| XA-09 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| XA-10 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| XA-11 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 |

## Recommended Execution Order

1. XA-01
2. XA-02
3. XA-03
4. XA-04 and XA-07 (parallel)
5. XA-05
6. XA-08
7. XA-10
8. XA-07 and XA-11 (parallel)
9. XA-06
10. XA-09
