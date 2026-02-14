# Demo MVP Design and Work Plan

## Goal
Build a runnable demo loop in `dome`:

`prompt -> planner -> orchestrator -> implementers -> checkers -> promotion`

The loop must be deterministic-first, telemetry-backed, and auditable from files/events.

## Status (2026-02-14)
- Current phase: Phase 1 (Prompt and planner integration)
- Completed in this phase:
  - `tools/orchestrator/planner.py` translates `xtrlv2` pre-contract -> `dome` `work.queue`
  - tests for translator mapping and CLI write path (`tests/test_planner.py`)
- Remaining in this phase:
  - add planner request/response runtime artifacts under `ops/runtime/` during demo runs
  - add dependency-cycle validation for planner task graphs

## Scope (MVP)
- Single repo, single orchestrator process.
- Parallel implementers via worker pool.
- Checker stage combines deterministic checks + gate decision artifact.
- Promotion decision is explicit and recorded.
- MCP is the internal control-plane backbone.
- A2A is optional ingress/egress and is normalized into MCP topics.

## Non-goals (for MVP)
- Multi-host distributed scheduling.
- Autonomous git merge/push to remote.
- Full production auth/rate-limit hardening.
- Long-term memory optimization.

## Roles and default models
- Planner: `gpt-5.3-codex-high`
- Orchestrator policy/gate synthesis: `gpt-5.3-codex-high`
- Implementers: `gpt-5.3` and `gpt-5.2` pool
- Checkers: deterministic tools first, then model checker (`gpt-5.3` by default)

## End-to-end flow
1. Prompt intake
2. Planner emits wave plan (`work.queue`)
3. Orchestrator dispatches implementer tasks (parallel)
4. Implementers return task results + evidence pointers
5. Checker stage runs deterministic verification + emits `gate.decision`
6. Promotion stage emits APPROVE/REJECT/NEEDS_HUMAN decision
7. State snapshot updates `state.space` with telemetry provenance

## Event spine (MCP topics)
- `plan.wave.created`
- `task.assigned`
- `task.result`
- `gate.requested`
- `gate.verdict`
- `promotion.decision`

A2A envelopes map to this spine through `tools/orchestrator/transports/bridge.py`.

## Core artifacts (already present)
- `ssot/schemas/work.queue.schema.json`
- `ssot/schemas/gate.decision.schema.json`
- `ssot/schemas/reason.codes.schema.json`
- `ssot/schemas/state.space.schema.json`
- `ssot/schemas/evidence.bundle.telemetry.schema.json`

## Prompt contracts (MVP templates)

### 1) Prompt -> Planner input
Required fields:
- `goal`
- `constraints`
- `acceptance_criteria`
- `max_workers`
- `budget` (`max_iterations`, `max_attempts`)

### 2) Planner -> Orchestrator output
Schema target: `work.queue`
- `run_id`
- `base_ref`
- `max_workers`
- `tasks[]` with `task_id`, `goal`, `status=QUEUED`, optional `dependencies`, optional `worker_model`

### 3) Checker -> Promotion output
Schema target: `gate.decision`
- `status`: `APPROVE | REJECT | NEEDS_HUMAN`
- `reason_codes[]`
- `confidence`, `risk_score`
- `telemetry_ref` (`trace_id_hex`, `span_id_hex`)

## Deterministic-first promotion policy
- Hard fail if deterministic checks fail.
- Approve only when:
  - deterministic checks pass
  - checker status is `APPROVE`
  - no critical reason code in result
- Route to `NEEDS_HUMAN` when risk is high or confidence is low.

## Work plan

### Phase 0: Foundation (done/partial)
- [x] Add SSOT schemas: `work.queue`, `gate.decision`, `reason.codes`
- [x] Add schema examples
- [x] Add MCP loop scaffold
- [x] Add A2A/MCP transport bridge
- [x] Add baseline tests for loop + bridge

### Phase 1: Prompt and planner integration
- [ ] Add planner request/response JSON files under `ops/runtime/`
- [x] Implement `tools/orchestrator/planner.py`:
  - reads prompt contract
  - writes schema-valid `work.queue`
- [x] Add tests:
  - invalid planner output rejected
- [ ] Add tests:
  - dependency cycles rejected

DoD:
- Planner always emits schema-valid `work.queue`.

### Phase 2: Implementer execution harness
- [ ] Implement `tools/orchestrator/implementers.py`:
  - consume `work.queue`
  - dispatch tasks with model routing
  - emit `task.result` events and evidence bundle refs
- [ ] Persist run artifacts to `ops/runtime/runs/<run_id>/`
- [ ] Add tests for:
  - all tasks processed (not capped to `max_workers`)
  - retry behavior for transient failures

DoD:
- A run with 5 tasks and `max_workers=2` completes all 5 tasks.

### Phase 3: Checker and gate
- [ ] Implement `tools/orchestrator/checkers.py`:
  - run deterministic verify commands
  - produce schema-valid `gate.decision`
- [ ] Wire reason code policy from `reason.codes` catalog
- [ ] Add tests:
  - deterministic fail -> `REJECT`
  - pass + low risk -> `APPROVE`
  - pass + high risk -> `NEEDS_HUMAN`

DoD:
- Gate decisions are deterministic and schema-valid.

### Phase 4: Promotion and state updates
- [ ] Implement `tools/orchestrator/promote.py`:
  - apply decision policy
  - emit `promotion.decision`
- [ ] Implement state writer `tools/orchestrator/state_writer.py`:
  - update `state.space` only from telemetry-backed evidence
- [ ] Add end-to-end test for full loop.

DoD:
- Full prompt-to-promotion run is reproducible and auditable.

## Demo scenario (first target)
- Input prompt: "Fix failing test and ensure formatter passes."
- Planner emits 3 tasks:
  1. reproduce failure
  2. implement fix
  3. verify tests/format
- Implementers run in parallel where possible.
- Checker emits gate decision.
- Promotion emits final outcome and writes state snapshot.

## Acceptance criteria for demo MVP
- One command runs end-to-end locally.
- Artifacts produced:
  - `work.queue.json`
  - task result bundles
  - `gate.decision.json`
  - `promotion.decision.json`
  - updated `state.space.json`
  - MCP event log (`jsonl`)
- Tests pass and schemas validate.

## Next command targets
- `python tools/orchestrator/planner.py --pre-contract /home/src404/src/xtrlv2/packets/engineering/migration_xtrlv2_cutover/pkt-v2-migrate-0002-runner-cutover.pre_contract.json --out ops/runtime/work.queue.json`
- `python tools/orchestrator/mcp_loop.py` (existing scaffold)
- `pytest -q`
- (after Phase 1+) `python tools/orchestrator/run_demo.py --prompt-file ops/runtime/prompt.json`
