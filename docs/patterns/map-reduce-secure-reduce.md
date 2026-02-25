# LLM Map-Reduce (Secure Reduce)

## Intent

Apply map-reduce over untrusted/large inputs while containing prompt-injection risk.

## Contract

1. Map workers run isolated per item/chunk and emit schema-bound minimal outputs.
2. Reduce consumes only validated map outputs (never raw input text).
3. Prefer deterministic code reduce; if LLM reduce is used, it sees only whitelisted fields.

## Required map output shape (example)

```json
{
  "doc_id": "string",
  "ok": true,
  "score": 0.0,
  "fields": {}
}
```

Constraints:
- reject unknown keys
- enforce types/ranges
- cap string lengths

## Failure modes and gates

- Schema-valid but malicious payload -> strict validators + allowlists.
- Cross-item contamination -> fresh context per map task.
- Reduce promptability -> no raw text in reduce input.
- Fanout cost spikes -> max fanout + per-run budget limits.

## TaskSpec binding

- Map tasks: `target.kind=data|artifact`, `action.kind=validate|rank`
- Reduce task: `target.kind=aggregate`, dependent on all map tasks
- Reason semantics: map/reduce failures recorded as `failure_reason_code`; guard denials in `policy_reason_code`

## Done checklist

- [ ] Map output schema enforced.
- [ ] Reduce input source restricted to validated map outputs.
- [ ] Poisoned-input test proves one malicious doc cannot steer global decision.
- [ ] Fanout budget test enforced.
