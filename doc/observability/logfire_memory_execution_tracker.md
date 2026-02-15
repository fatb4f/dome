# Logfire Memory Execution Tracker

Date: 2026-02-15

## Milestones

| Order | Milestone | Scope | Priority | Depends On | Status |
|---:|---|---|---|---|---|
| 1 | LM-01 OTel + Logfire baseline | Add stage instrumentation and run-level correlation attributes | P0 | - | Done (#27) |
| 2 | LM-02 `memoryd` + DuckDB materialization | Add daemon skeleton, schema DDL, checkpointed ingest loop | P0 | LM-01 | Done (#28) |
| 3 | LM-03 MCP/A2A memory interface | Add bounded memory query/upsert/health API over DuckDB | P1 | LM-02 | Done (#29) |
| 4 | LM-04 Policy hardening + ops | Add retention/redaction/audit/runbook integration and alert hooks | P1 | LM-02, LM-03 | Done (#30) |
| 5 | LM-05 Reason semantics + facts spine | Canonical failure/policy reason semantics and task/event fact materialization | P0 | LM-04 | Done (#31) |

## Dependency Matrix

`1` means row item depends on column item.

| Row \\ Col | LM-01 | LM-02 | LM-03 | LM-04 |
|---|---:|---:|---:|---:|
| LM-01 | 0 | 0 | 0 | 0 |
| LM-02 | 1 | 0 | 0 | 0 |
| LM-03 | 0 | 1 | 0 | 0 |
| LM-04 | 0 | 1 | 1 | 0 |

## Packet IDs

1. `pkt-dome-lm-01-otel-logfire-baseline`
2. `pkt-dome-lm-02-memoryd-duckdb-materialization`
3. `pkt-dome-lm-03-memory-mcp-a2a-interface`
4. `pkt-dome-lm-04-policy-hardening-ops`
5. `pkt-dome-lm-05-reason-semantics-facts-spine`

## Completion

Sequential milestone execution completed on 2026-02-15.

Evidence roots:

- `ops/runtime/lm-01/`
- `ops/runtime/lm-02/`
- `ops/runtime/lm-03/`
- `ops/runtime/lm-04/`
- `ops/runtime/lm-05/`

## Cross-Repo Requirements

- `dome` remains integration owner for planner/daemon/materialization and Memory API behavior.
- `xtrlv2` remains SSOT owner for guardrails/state-transition/reason-code schema contracts.

## Cross-Repo Dependency Matrix (core path)

`1` means row item depends on column item.

| Row \\ Col | CR-01 dome | CR-02 xtrlv2 SSOT |
|---|---:|---:|
| CR-01 dome | 0 | 1 |
| CR-02 xtrlv2 SSOT | 0 | 0 |
