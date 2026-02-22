# xtrlv2 Folding Finalization Plan (Skill + Binary)

## Objective
Finalize the transition from "xtrlv2-compatible scaffolding" to a production-ready, versioned `tool.api` skill surface and a distributable binary/runtime entrypoint.

## Context
`dome` already aligns conceptually to `dome.api.tool.xtrlv2.*` and pinned xtrlv2 contracts. The remaining work is to harden this into:
1. A strict, schema-validated skill contract.
2. A deterministic binary interface for orchestration execution.

## Target End State

### Skill surface
- Authoritative method contract document and schemas for `dome.api.tool.xtrlv2.*`.
- Method allowlists bound to capability scopes.
- Typed error taxonomy with stable codes.
- Backward compatibility policy and semantic versioning.

### Binary surface
- Single CLI binary entrypoint (Python console script first, compiled artifact optional) supporting:
  - `plan`
  - `execute`
  - `gate`
  - `promote`
  - `validate-contracts`
- Deterministic exit codes and structured JSONL event output.
- Replay-safe run manifests pinned to contract versions.

## Workstreams

### WS-1: Skill contract finalization
1. Define `tool_contract.schema.json` and method-specific input/output schemas.
2. Add contract resolver from packet/task specs to method allowlists.
3. Enforce pre-dispatch schema validation in runtime.
4. Add negative tests for out-of-contract method calls.

### WS-2: Binary interface finalization
1. Introduce top-level CLI (`dome`) with subcommands mapped to orchestrator stages.
2. Make all stage outputs machine-consumable JSON.
3. Standardize failure codes and envelope schema.
4. Add reproducibility checks (same input contract => same deterministic planning artifacts).

### WS-3: Pinning and compatibility
1. Maintain explicit xtrlv2 pin manifest and compatibility matrix updates.
2. Add CI gate for pinned contract compatibility.
3. Document migration path for breaking schema updates.

### WS-4: Promotion readiness
1. Add release checklist for skill+binary contract completeness.
2. Require evidence bundle pointers in promotion decisions.
3. Ensure packet-level provenance ties to contract versions.

## Milestones

1. M1: Skill contract schemas + validator complete.
2. M2: Binary CLI entrypoint with deterministic envelopes complete.
3. M3: Cross-repo compatibility gates enforced in CI.
4. M4: Promotion/release checklist integrated and passing.

## Acceptance Criteria
- All `tool.api` calls validated against schema-bound contract before execution.
- Binary commands emit stable, versioned envelopes and deterministic exit behavior.
- CI fails on xtrlv2 pin drift or contract compatibility failures.
- Replay of packet inputs reproduces equivalent planned task graph and gate outcome.

## Risks and Mitigations
- Risk: contract drift between skill and binary wrappers.
  - Mitigation: generate wrappers from shared schema definitions.
- Risk: hidden side effects outside contract boundary.
  - Mitigation: deny-by-default method resolver + audit logs.
- Risk: breaking downstream repos.
  - Mitigation: semver + compatibility adapters + migration notes.

## Immediate Execution Queue
1. Draft `tool_contract` schemas and error taxonomy.
2. Add `validate-contracts` command and CI step.
3. Add binary-level integration tests for deterministic envelopes.
4. Publish migration notes for downstream consumers.
