# Phase D: Analysis, Dependency Gaps, and Implementation Plan

Date: 2026-02-25
Scope: Phase D (`#77`) streaming correctness and provenance.

## 1) Current-state analysis

### What is already present

- `StreamJobEvents` RPC exists and supports `since_seq`.
- Event storage preserves per-job monotonic sequence numbers.
- `GetJobStatus` returns a `RunProvenance` object shape.
- Phase C now emits execution events for real local-process paths.

### Gaps against Phase D requirements

1. `follow=true` behavior is not implemented:
   - current stream returns current snapshot only and exits.
   - no tail-until-terminal loop.

2. Resume semantics are underspecified in behavior tests:
   - `since_seq` filtering exists, but there is no explicit follow/resume contract test matrix.

3. Provenance remains placeholder-level:
   - `commit_sha` = `"unknown"`, tool versions empty JSON, env fingerprint = `"inmemory"`.
   - no repo/dirty/tool-version/environment capture path.

4. Persistence parity risks:
   - runtime store supports events, but provenance enrichment flow is not normalized between in-memory and SQLite daemon paths.

## 2) Phase D dependency matrix

Legend:
- `Blocker`: required for downstream items.
- `Soft dep`: parallelizable but merge depends on upstream stabilization.

| ID | Workstream | Output | Depends on | Type | Unblocks |
|---|---|---|---|---|---|
| D1 | Stream follow contract | explicit behavior contract for `follow=true` + terminal-stop rules | None | - | D2, D5 |
| D2 | Stream tail implementation | `StreamJobEvents(follow=true)` loop with bounded polling and terminal detection | D1 | Blocker | D4, D5 |
| D3 | Provenance collector | helper to collect commit SHA, dirty flag, tool versions, env fingerprint | None | - | D4, D6 |
| D4 | Status provenance wiring | `GetJobStatus` uses collected provenance from run/job context | D2, D3 | Blocker | D6 |
| D5 | Resume correctness tests | deterministic tests for `since_seq` + follow/non-follow paths | D1, D2 | Blocker | D6 |
| D6 | Docs + issue closure evidence | docs alignment + reproducible validation commands for `#77` | D4, D5 | Blocker | Phase D close |

## 3) Implementation plan (sequenced)

### Step D1: Define streaming semantics contract

Deliver:
- Document and codify:
  - `follow=false`: return all events `seq > since_seq`, then end stream.
  - `follow=true`: stream existing + future events until terminal state observed.
  - terminal states: `succeeded|failed|canceled`.

Acceptance:
- one source-of-truth behavior definition in code comments/tests.

### Step D2: Implement `follow=true` tail loop

Deliver:
- server stream loop with:
  - incremental cursor updates
  - short sleep/poll interval
  - terminal-state stop condition
  - context cancellation checks

Acceptance:
- behaves like tail-f for one job lifecycle.

### Step D3: Implement provenance collector

Deliver:
- module (e.g., `tools/domed/provenance.py`) capturing:
  - repo id/name
  - commit SHA (`git rev-parse HEAD`)
  - dirty flag (`git status --porcelain`)
  - tool versions (`domed` and executor backend id/version)
  - env fingerprint (`python`, platform, optional hostname hash)

Acceptance:
- resilient fallback when git metadata is unavailable.

### Step D4: Wire provenance into status

Deliver:
- `GetJobStatus` returns real provenance values for executed jobs.
- normalize representation across in-memory and SQLite-backed runtime.

Acceptance:
- non-placeholder provenance in integration tests.

### Step D5: Add test coverage for stream/resume/provenance

Deliver:
- tests for:
  - `since_seq` resume determinism
  - `follow=true` tail-until-terminal
  - provenance field population and fallback behavior

Acceptance:
- deterministic pass in CI.

### Step D6: Docs and tracker closeout

Deliver:
- update milestone docs with Phase D status and commands.
- update `#77` with evidence and close when criteria met.

Acceptance:
- issue body/checklist and repository behavior match.

## 4) Validation commands

- `python3 -m pytest -q tests/test_domed_service_integration.py tests/test_domed_service_execution_routing.py`
- `python3 -m pytest -q tests/test_domed_stream_follow.py tests/test_domed_provenance.py` (new)
- `python3 -m ruff check tools/domed tests`
- `python3 tools/codex/check_generated_client_only.py`
- `bash tools/domed/check_codegen_drift.sh`

## 5) Risk register and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Stream tail loops hang forever | High | terminal-state break + context-cancel handling + timeout test |
| High poll frequency causes CPU churn | Medium | bounded poll interval + no busy-spin |
| Git metadata unavailable in some envs | Medium | graceful fallback fields + explicit `unknown` markers |
| Provenance data inconsistencies across stores | Medium | centralized provenance collector + shared serialization |

## 6) Exit criteria for Phase D

Phase D is complete when:
1. `StreamJobEvents(follow=true)` tails until terminal state.
2. `since_seq` resume behavior is deterministic and tested.
3. `GetJobStatus` includes populated provenance (commit/tool/env) or explicit fallback values.
4. Validation commands are documented and reproducible in issue `#77`.
