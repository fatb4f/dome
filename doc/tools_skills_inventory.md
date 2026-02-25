# Tools and Skills Inventory

Last updated: 2026-02-25

## Scope

This inventory captures tool and skill surfaces currently present in `dome` to support issue decomposition from #56 into #57-#60.

## Tools

### Codex bridge tools (`tools/codex`)

| Tool | Entrypoint | Role | Current status |
| --- | --- | --- | --- |
| `dome_cli` | `tools/codex/dome_cli.py` | Wrapper CLI for codex-browse skill execution and contract validation. | Active |
| `browse_skill` | `tools/codex/browse_skill.py` | Contract checks + runner invocation adapter. | Active |
| `generate_context` | `tools/codex/generate_context.py` | Context generation utility for codex workflows. | Active |

### Orchestrator tools (`tools/orchestrator`)

| Tool | Entrypoint | Role | Current status |
| --- | --- | --- | --- |
| `run_plan_implement_verify` | `tools/orchestrator/run_plan_implement_verify.py` | PIV runner with issue/milestone plan stage support. | Active |
| `mcp_loop` | `tools/orchestrator/mcp_loop.py` | Event bus + concurrent wave orchestration scaffold. | Active |
| `planner` | `tools/orchestrator/planner.py` | Translates pre-contract to `work.queue`. | Active |
| `dispatcher` | `tools/orchestrator/dispatcher.py` | Dependency-aware task dispatch supervisor. | Active |
| `implementers` | `tools/orchestrator/implementers.py` | Implement-phase harness for command execution and result capture. | Active |
| `checkers` | `tools/orchestrator/checkers.py` | Gate decision generation + schema validation. | Active |
| `promote` | `tools/orchestrator/promote.py` | Promotion decision generation + schema validation. | Active |
| `state_writer` | `tools/orchestrator/state_writer.py` | Writes/updates `state.space` from run outputs. | Active |
| `run_demo` | `tools/orchestrator/run_demo.py` | End-to-end demo orchestration flow. | Active (demo) |
| `run_live_fix_demo` | `tools/orchestrator/run_live_fix_demo.py` | Live-fix iterative demo flow. | Active (demo) |
| `loop_tick` | `tools/orchestrator/loop_tick.py` | Bounded outer-loop tick runner. | Active |
| `audit_drill` | `tools/orchestrator/audit_drill.py` | Build audit evidence bundle from run artifacts. | Active |
| `evidence_capsule` | `tools/orchestrator/evidence_capsule.py` | Translate evidence bundle to canonical capsule format. | Active |
| `traceability` | `tools/orchestrator/traceability.py` | CL-REQ traceability report generation. | Active |
| `ingest_pattern_catalog` | `tools/orchestrator/ingest_pattern_catalog.py` | Import pattern data into local catalog format. | Active |
| `migrate_substrate` | `tools/orchestrator/migrate_substrate.py` | Substrate migration report helper. | Active |
| `state_doctor` | `tools/orchestrator/state_doctor.py` | Validate substrate layout invariants. | Active |
| `alert_gate` | `tools/orchestrator/alert_gate.py` | Alert threshold evaluation over run summaries. | Active |
| `dlq_reprocess` | `tools/orchestrator/dlq_reprocess.py` | Reprocess DLQ entries. | Active |
| `deprecated_path_lint` | `tools/orchestrator/deprecated_path_lint.py` | Lint docs/artifacts for deprecated paths. | Active |
| `otel_stage` | `tools/orchestrator/otel_stage.py` | OTel stage helper module. | Module |
| `security` | `tools/orchestrator/security.py` | Runtime path/security checks. | Module |
| `runtime_config` | `tools/orchestrator/runtime_config.py` | Runtime config loading and defaults. | Module |
| `io_utils` | `tools/orchestrator/io_utils.py` | Common IO helpers (atomic writes, etc.). | Module |
| `state_machine` | `tools/orchestrator/state_machine.py` | State transition helpers. | Module |
| `substrate_layout` | `tools/orchestrator/substrate_layout.py` | Filesystem layout helpers. | Module |
| `xa_mapping` | `tools/orchestrator/xa_mapping.py` | XA mapping utilities. | Module |
| `transports/*` | `tools/orchestrator/transports/*.py` | MCP/A2A transport abstractions and bridge. | Module |

### Telemetry tools (`tools/telemetry`)

| Tool | Entrypoint | Role | Current status |
| --- | --- | --- | --- |
| `memoryd` | `tools/telemetry/memoryd.py` | Materialize long-horizon run memory into DuckDB. | Active |
| `memory_binder` | `tools/telemetry/memory_binder.py` | Deterministic binder derivations over task facts. | Active |
| `memory_alert_gate` | `tools/telemetry/memory_alert_gate.py` | Check memory daemon checkpoint health. | Active |
| `memory_api` | `tools/telemetry/memory_api.py` | API/query helper module for telemetry memory. | Module |
| `memory_schema.sql` | `tools/telemetry/memory_schema.sql` | SQL schema for memory substrate storage. | Active schema asset |

## Skills

### Repo-local skills

| Skill | Path | Entrypoint | Contract dependency | Current status |
| --- | --- | --- | --- | --- |
| `codex_web_browse` | `docs/skills/codex_web_browse/SKILL.md` | `tools/codex/dome_cli.py` | `codex-browse` schemas + `identity-graph` contract pins | Active |

### Notes

- No additional repo-local `SKILL.md` files are present besides `codex_web_browse`.
- Current implementation is wrapper-driven around `codex-browse`; no standalone `codex-gateway` daemon exists yet.

## Gaps relative to #57-#60

- Missing gateway API contract artifacts (`proto` and/or OpenAPI) in `dome`.
- Missing generated gateway clients.
- Missing runtime `codex-gateway` daemon implementation.
- Existing orchestration is script/module-driven, not API-daemon-driven.
