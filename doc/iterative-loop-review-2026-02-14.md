# Iterative Loop Review (Clean)

**Date:** 2026-02-14  
**Repo:** `/home/src404/src/dome`  
**Purpose:** Replace malformed transcript content with a review-ready artifact.

## Findings (Ordered)

1. **High**: Runnable command snippets were malformed in prior draft (`bashrm`, `bashpytest`) and not copy-safe.
2. **High**: Patch blocks were not directly applyable (`diffdiff` headers, broken context).
3. **Medium**: Repro claims lacked commit-linked context for auditability.
4. **Medium**: Time-sensitive statements (e.g. “tests pass”) were written as absolutes without commit/timestamp anchors.

## Verified Live-Demo Command

Run from repo root:

```bash
rm -rf ops/runtime
python tools/orchestrator/run_live_fix_demo.py \
  --run-root ops/runtime/runs \
  --state-space ssot/examples/state.space.json \
  --reason-codes ssot/policy/reason.codes.json
```

Expected key outputs under:

- `ops/runtime/runs/pkt-dome-livefix-0001/work.queue.json`
- `ops/runtime/runs/pkt-dome-livefix-0001/summary.json`
- `ops/runtime/runs/pkt-dome-livefix-0001/iteration.loop.json`
- `ops/runtime/runs/pkt-dome-livefix-0001/gate/gate.decision.json`
- `ops/runtime/runs/pkt-dome-livefix-0001/promotion/promotion.decision.json`
- `ops/runtime/runs/pkt-dome-livefix-0001/state.space.json`
- `ops/runtime/runs/pkt-dome-livefix-0001/run.manifest.json`
- `ops/runtime/mcp_events.jsonl`

## Current-State Notes

- Iteration is implemented as **task-level retry history** (`RetryingWorker`) plus `iteration.loop.json` rendering.
- It is **not** currently an outer controller loop over repeated PLAN→EXECUTE→GATE cycles.

## Recommended Next Patch Set

1. Add early work-queue validation in dispatcher (duplicate `task_id`, unknown dependency).
2. Convert worker exceptions to structured `FAIL` payloads instead of hard abort.
3. Split overloaded `task.result` topic into raw vs persisted result streams.
4. Add event-bus locking for topic map + event-log append path.
5. Guard pytest discovery from runtime artifacts via pytest config (`testpaths`, `norecursedirs`).

## Review Metadata

- This file intentionally omits speculative timings and unverified hash claims.
- Keep future run claims anchored with:
  - commit SHA
  - UTC timestamp
  - exact command used
  - artifact path(s)
