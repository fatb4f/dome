# Memory Layering Model

## Intent

Define authority levels for runtime memory artifacts so retrieval is useful without becoming unsafe.

## Layers

1. Authoritative execution state
- Source: run artifacts, event envelope, guard/gate outcomes
- Role: ground truth for replay/audit

2. Working memory
- Source: run-scoped todo/state artifacts
- Role: short-horizon coordination and progress tracking

3. Session state externalization
- Source: templated state snapshots
- Role: continuity across long loops; non-authoritative

4. Identity/profile memory
- Source: reviewed profile docs with evidence pointers
- Role: preference/context hints; never permission authority

5. Synthesized memory
- Source: periodic synthesis over many runs
- Role: reusable rules/playbooks with support thresholds and expiry

## Authority rules

- Retrieval planning should prioritize authoritative + high-confidence synthesized entries.
- Non-authoritative layers cannot grant capabilities or bypass guardrails.
- Any prescriptive recommendation must map to TaskSpec keys and pass `python_standard`/guard checks.

## Lifecycle

1. Capture run facts.
2. Derive operational capsules.
3. Promote to conceptual/synthesized memory only with support threshold + provenance.
4. Decay or retire stale/contradicted concepts.

## Gate checklist

- [ ] Every synthesized rule has provenance (run/task/evidence refs).
- [ ] Support threshold required for promotion.
- [ ] TTL/revalidation policy applied.
- [ ] Failure vs policy semantics remain separated (`failure_reason_code` vs `policy_reason_code`).
