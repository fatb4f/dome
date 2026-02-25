# M5 Tool Migration Plan

## Objective

Migrate remaining tool invocation paths to a strict API-first runtime model:

- `dome` control/spec plane orchestrates by contract.
- `domed` runtime/data plane executes jobs via gRPC.
- Production paths use generated thin clients only.

## Scope

In scope:

- Remove production bypasses to direct script execution.
- Route remaining tool execution through `domed` job types and envelopes.
- Add migration guardrails and compatibility adapters where needed.
- Define deprecation and removal schedule for legacy paths.

Out of scope:

- Re-architecting unrelated memory/planner milestones (`#38-#43`).
- Replacing SSOT model files not tied to runtime invocation.

## Current baseline

Implemented:

- `domed.v1` proto + codegen checks.
- `domed` runtime daemon with sqlite store + TTL GC.
- Generated thin client wrapper + production `run-skill` path via `DomedClient`.
- Explicit legacy path (`run-skill-legacy`) still present.

Remaining migration targets:

1. Tool wrappers still invoking local subprocess runners for operational paths.
2. Legacy command surfaces that can bypass daemon policy.
3. Inconsistent transport usage across tool families (some contract-validated, some local process).

## Migration phases

### Phase 1: Inventory and classification

- Build canonical migration register of all execution entrypoints:
  - production
  - debug-only
  - test-only
- Assign each entrypoint a migration class:
  - `MIGRATE_NOW`
  - `ADAPTER_REQUIRED`
  - `DEPRECATE_REMOVE`

Artifacts:

- `doc/milestone_domed/m5/m5_tool_migration_register.csv`
- `doc/milestone_domed/m5/m5_tool_migration_dependency_matrix.md`
- `doc/milestone_domed/m5/m5_tool_callsite_inventory.csv` (generated)

Inventory generation command:

- `python tools/codex/migration_inventory.py --repo-root . --out doc/milestone_domed/m5/m5_tool_callsite_inventory.csv`

### Phase 2: Adapter and contract alignment

- For each `ADAPTER_REQUIRED` path:
  - define a `domed` job type envelope
  - preserve idempotency and status semantics
  - add compatibility tests

Acceptance:

- No production path executes tools outside `domed` transport.
- Explicit legacy adapters are marked non-production and time-bounded.

### Phase 3: Cutover and enforcement

- Switch production callers to generated clients.
- Add CI guard checks for forbidden call patterns.
- Keep temporary feature flags only where rollback is needed.

Acceptance:

- Guard checks fail on new bypasses.
- All production runbooks reference `domed` endpoint flow only.

### Phase 4: Legacy removal

- Remove deprecated direct-run paths after cutover bake period.
- Update docs and issue trackers.

Acceptance:

- `run-skill-legacy` and equivalent bypasses removed (or isolated to test fixtures only).

## Required controls and tests

Required controls:

- static scan for forbidden production bypass calls
- generated-client-only guard script
- proto/codegen drift and compatibility gates

Required test suites:

- stub matrix per migrated tool family
- integration tests against running `domed`
- failure-mode tests (daemon unavailable, idempotency conflict, timeout)

## Risks and mitigations

Risk: migration breaks existing workflows using local script runners.
Mitigation: keep explicit adapter command path during transition; mark as non-production and instrument usage.

Risk: mixed transport behavior causes semantic drift.
Mitigation: enforce envelope mapping tests and typed status/error checks.

Risk: daemon dependency introduces new availability coupling.
Mitigation: daemon health checks + retry policy + explicit operator runbooks.

## Exit criteria for M5

- Migration register completed and all production paths classified.
- All production execution paths use generated clients to `domed`.
- Legacy bypasses deprecated or removed with explicit date and commit references.
- CI gates prevent regression to direct execution paths.
