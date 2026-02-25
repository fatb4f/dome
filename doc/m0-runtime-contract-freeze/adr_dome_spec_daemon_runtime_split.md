# ADR: Dome Spec Plane vs Daemon Runtime Plane

Status: accepted  
Scope: M0 contract freeze (`#61`) and downstream milestones (`#58`, `#59`, `#60`)  
Date: 2026-02-25

## Decision

`dome` is the specification/control plane.  
`domed` is the runtime/data plane.

This is a hard architectural boundary.

## Responsibilities

### Dome (spec/control plane)

- Owns contract definitions and schema authority.
- Owns loop planning/decomposition semantics.
- Owns policy, gate, and promotion decision logic.
- Owns skill requirement declarations and capability requirements.

### Daemon (runtime/data plane)

- Owns capability discovery serving.
- Owns execution lifecycle (submit/status/cancel).
- Owns streaming logs/events and resume semantics.
- Owns idempotency ledger, locking, and runtime execution mechanics.
- Owns run provenance emission as runtime facts.

## Non-overlap invariants

1. Dome must not execute tools directly in production runtime paths.
2. Daemon must not implement gate/promotion policy decisions.
3. All execution between planes uses contract-defined envelopes only.
4. Contract changes must be git-tracked and compatibility-gated.
5. Runtime invocation path is thin-client-only.

## Contract seam

Minimum shared seam:

- `SkillExecute` request/response envelope
- Capability discovery contract
- Job lifecycle operations (submit/status/cancel)
- Stream events/logs contract (cursor/resume semantics)
- Typed error namespace and correlation identity fields

## Enforcement

### CI/policy gates

- Reject non-thin-client runtime invocation paths.
- Reject direct tool execution from control-plane modules.
- Reject control-policy logic in daemon runtime modules.
- Enforce schema/API compatibility on contract changes.

### Runtime checks

- Verify capability discovery before execution dispatch.
- Emit canonical run provenance record for every run.
- Preserve idempotency and lock semantics under retries.

## Consequences

- Clear ownership and reduced architectural drift.
- Enables in-process or out-of-process daemon deployment without changing contracts.
- Requires explicit adapters and stronger compatibility discipline.
