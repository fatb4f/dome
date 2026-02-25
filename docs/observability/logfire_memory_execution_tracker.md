# OTLP Memory Execution Tracker

Date: 2026-02-15

## Milestones

| Order | Milestone | Scope | Priority | Depends On | Status |
|---:|---|---|---|---|---|
| 1 | LM-01 OTel + OTLP backend baseline | Add stage instrumentation and run-level correlation attributes | P0 | - | Done (#27) |
| 2 | LM-02 `memoryd` + DuckDB materialization | Add daemon skeleton, schema DDL, checkpointed ingest loop | P0 | LM-01 | Done (#28) |
| 3 | LM-03 MCP/A2A memory interface | Add bounded memory query/upsert/health API over DuckDB | P1 | LM-02 | Done (#29) |
| 4 | LM-04 Policy hardening + ops | Add retention/redaction/audit/runbook integration and alert hooks | P1 | LM-02, LM-03 | Done (#30) |
| 5 | LM-05 Reason semantics + facts spine | Canonical failure/policy reason semantics and task/event fact materialization | P0 | LM-04 | Done (#31) |
| 6 | LM-06 Deterministic timestamps + replay stability | Deterministic timestamp handling and replay-stable ordering in memory writes | P0 | LM-05 | Done (#32) |
| 7 | LM-07 Cross-repo contract tests | Pin and validate xtrlv2 SSOT compatibility artifacts in dome CI tests | P0 | LM-05 | Done (#33) |
| 8 | LM-08 Query primitive hardening | Add stable query primitives for deterministic/bounded retrieval patterns | P0 | LM-05 | Done (#34) |
| 9 | LM-09 Tracker truthfulness + OTLP backend naming | Reconcile tracker/status fidelity and backend naming (`OTLP backend` with backend options) | P1 | LM-08 | Done (#35) |
| 10 | LM-10 Semantics migration completion | Complete failure/policy reason semantic naming migration and compatibility boundaries | P0 | LM-09 | Done (#36) |
| 11 | LM-11 Binder v1 deterministic integration | Implement binder idempotency/upsert keys/fingerprint determinism and replay-safe derivations | P0 | LM-10 | Done (#37) |

## Dependency Matrix

`1` means row item depends on column item.

| Row \\ Col | LM-01 | LM-02 | LM-03 | LM-04 |
|---|---:|---:|---:|---:|
| LM-01 | 0 | 0 | 0 | 0 |
| LM-02 | 1 | 0 | 0 | 0 |
| LM-03 | 0 | 1 | 0 | 0 |
| LM-04 | 0 | 1 | 1 | 0 |

## Forward Dependency Matrix (LM-05..LM-11)

`1` means row item depends on column item.

| Row \\ Col | LM-05 | LM-06 | LM-07 | LM-08 | LM-09 | LM-10 | LM-11 |
|---|---:|---:|---:|---:|---:|---:|---:|
| LM-05 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| LM-06 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| LM-07 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| LM-08 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| LM-09 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| LM-10 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| LM-11 | 0 | 0 | 0 | 0 | 1 | 1 | 0 |

## Packet IDs

1. `pkt-dome-lm-01-otel-logfire-baseline`
2. `pkt-dome-lm-02-memoryd-duckdb-materialization`
3. `pkt-dome-lm-03-memory-mcp-a2a-interface`
4. `pkt-dome-lm-04-policy-hardening-ops`
5. `pkt-dome-lm-05-reason-semantics-facts-spine`
6. `pkt-dome-lm-06-deterministic-timestamps-replay`
7. `pkt-dome-lm-07-cross-repo-contract-tests`
8. `pkt-dome-lm-08-query-primitives-hardening`
9. `pkt-dome-lm-09-tracker-otlp-reconciliation`
10. `pkt-dome-lm-10-semantics-migration-completion`
11. `pkt-dome-lm-11-binder-v1-deterministic-integration`

## Completion

LM-01..LM-11 completed on 2026-02-15.

Evidence roots:

- `ops/runtime/lm-01/`
- `ops/runtime/lm-02/`
- `ops/runtime/lm-03/`
- `ops/runtime/lm-04/`
- `ops/runtime/lm-05/`
- `ops/runtime/lm-06/`
- `ops/runtime/lm-07/`
- `ops/runtime/lm-08/`
- `ops/runtime/lm-09/`
- `ops/runtime/lm-10/`
- `ops/runtime/lm-11/`

## Status Semantics

- `Done`: milestone acceptance checks passed with committed evidence roots.
- `Partial`: milestone started and artifacts exist, but one or more exit criteria remain open.
- `Planned`: milestone is defined but has no accepted implementation evidence yet.

## Cross-Repo Requirements

- `dome` remains integration owner for planner/daemon/materialization and Memory API behavior.
- `xtrlv2` remains SSOT owner for guardrails/state-transition/reason-code schema contracts.

## Cross-Repo Dependency Matrix (core path)

`1` means row item depends on column item.

| Row \\ Col | CR-01 dome | CR-02 xtrlv2 SSOT |
|---|---:|---:|
| CR-01 dome | 0 | 1 |
| CR-02 xtrlv2 SSOT | 0 | 0 |

## Post-LM11 Planned Rollout

Associated tracker issue: `#42`

| Order | Item | Issue | Scope | Status |
|---:|---|---:|---|---|
| 1 | PL-01 Binder shadow-mode daemon rollout | #38 | Optional `memoryd --run-binder` rollout without planner behavior changes | Planned |
| 2 | PL-02 Binder-aware ops alerts + runbook wiring | #39 | Binder-aware health thresholds and runbook commands | Planned |
| 3 | PL-03 Planner retrieval loop with memory priors | #41 | Query/rank priors before execution with deterministic bounded selection | Planned |
| 4 | PL-04 Guardrails facts ingestion + policy reason-code path | #40 | Persist guard facts while keeping policy/failure semantics split | Planned |
| 5 | PL-05 End-to-end deterministic pipeline validation | #43 | Integration coverage for materialize -> binder -> retrieve determinism | Planned |

Detailed dependency matrix and milestone tracker:
- `doc/observability/post_lm11_memory_execution_tracker.md`
