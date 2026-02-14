# MVP v0.2 — Spec Kit scaffold (memory + task preferences)

This repository is a **minimal Spec Kit** scaffold for an agentic system whose only durable identity is:

- **Memory:** proven observations with provenance
- **Task preferences:** deterministic ranking/routing preferences under constraints

The SSOT is `.specify/memory/constitution.md`.

## Workflow (Plan → Execute → Gate)

- **Plan:** produce a bounded work DAG (`{reqs,deps,provs,assert}`) and evidence obligations.
- **Execute:** run tools with rich signals and emit all decision-relevant signals into telemetry.
- **Gate:** update state **only** from telemetry-derived evidence (trace data). DONE requires satisfied obligations and a recorded trace pointer.

## Telemetry wiring (Option A + Langfuse)

- `ops/observability/` contains an OpenTelemetry Collector config that forwards OTLP/HTTP traces to Langfuse.
- `apps/python-demo/` contains a minimal runnable demo.

## Concurrent loop contracts (MVP)

- `ssot/schemas/work.queue.schema.json` — planner/orchestrator task wave contract
- `ssot/schemas/gate.decision.schema.json` — deterministic-first gate verdict contract
- `ssot/schemas/reason.codes.schema.json` — typed reason-code catalog
- `tools/orchestrator/mcp_loop.py` — MCP-first concurrent orchestrator scaffold
- `tools/orchestrator/dispatcher.py` — Codex supervisor layer for dependency-aware task dispatch
- `tools/orchestrator/transports/` — MCP + A2A adapters and bridge (`A2A -> MCP` normalization)
- `tools/orchestrator/planner.py` — translate `xtrlv2` pre-contract into `dome` `work.queue`
- `tools/orchestrator/implementers.py` — Phase 2 harness with transient retry + run artifact persistence
- `tools/orchestrator/checkers.py` — Phase 3 deterministic gate checker with optional OTel span export

Matching examples live in `ssot/examples/`.

## Spec Kit layout

- `.specify/memory/constitution.md` — SSOT principles (project constitution)
- `.specify/templates/*.md` — templates for spec / plan / tasks
- `.specify/specs/001-mvpv0_2-memory-task-preferences/` — initial feature artifacts
- `.claude/commands/` and `.github/prompts/` — minimal slash-command prompts

## Using with Spec Kit

If you already use Spec Kit in your environment, you can initialize/upgrade templates as needed using `specify init --here --force` and your preferred agent.

See GitHub Spec Kit docs for setup and supported agents. (https://github.com/github/spec-kit)

## Validation

```bash
python -m pip install pytest jsonschema
pytest -q
```

Pre-contract translation example:

```bash
python tools/orchestrator/planner.py \
  --pre-contract /home/src404/src/xtrlv2/packets/engineering/migration_xtrlv2_cutover/pkt-v2-migrate-0002-runner-cutover.pre_contract.json \
  --out ops/runtime/work.queue.json
```

Implementer harness example:

```bash
python tools/orchestrator/implementers.py \
  --work-queue ops/runtime/work.queue.json \
  --run-root ops/runtime/runs \
  --max-retries 2
```

Checker example:

```bash
python tools/orchestrator/checkers.py \
  --run-root ops/runtime/runs \
  --run-id pkt-v2-migrate-0002-runner-cutover \
  --reason-codes ssot/examples/reason.codes.json \
  --risk-threshold 60 \
  --otel-export
```
