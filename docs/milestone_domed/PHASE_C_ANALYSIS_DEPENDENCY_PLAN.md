# Phase C: Analysis, Dependency Matrix, and Implementation Plan

Date: 2026-02-25
Scope: Phase C (`#76`) real execution routing in `domed`.

## 1) Current-state analysis

### What exists now

- `SkillExecute` API and lifecycle state store are implemented.
- Discovery is progressive and manifest-first (`ssot/tools/**` preferred).
- Job/event persistence exists (in-memory + SQLite stores).
- Generated-client-only checks and codegen drift gates are in place.

### Primary gap for Phase C

- `SkillExecute` still runs synthetic execution paths (`skill-execute`, `job.noop`, `job.log`, `job.fail`) in-process.
- There is no executor abstraction and no routing from SSOT manifest to a real command runner.
- Event model is present, but stdout/stderr/progress from a real subprocess is not yet wired.

## 2) Phase C dependency matrix

Legend:
- `Blocker`: must land first.
- `Soft dep`: parallel work allowed, merge depends on upstream output.

| ID | Workstream | Output | Depends on | Type | Unblocks |
|---|---|---|---|---|---|
| C1 | Executor contract | `tools/domed/executor.py` protocol/types (`ExecutionRequest`, `ExecutionResult`, events) | None | - | C2, C3, C4 |
| C2 | Manifest execution fields | extend manifests with `entrypoint` + default args/env policy | C1 | Blocker | C3, C5 |
| C3 | Local-process executor backend | `tools/domed/executors/local_process.py` subprocess runner + streaming callbacks | C1, C2 | Blocker | C4, C6 |
| C4 | Service routing integration | `SkillExecute` routes `skill_id` to executor by SSOT manifest | C2, C3 | Blocker | C6 |
| C5 | Real skill onboarding | at least one non-synthetic skill mapped in `ssot/tools/**` | C2 | Soft dep | C6 |
| C6 | Event-stream correctness for execution | emit start/stdout/stderr/progress/final events from executor path | C3, C4 | Blocker | C7 |
| C7 | Validation + hardening | tests + docs + issue evidence for acceptance closure | C4, C5, C6 | Blocker | Phase C close |

## 3) Implementation plan (sequenced)

### Step C1: Define executor interface

Deliver:
- New module for executor contracts:
  - request: run/job IDs, tool ID, profile, task payload, constraints, cwd/env policy
  - result: exit code, terminal state, artifacts (optional)
  - callbacks/events: stdout, stderr, progress, terminal

Acceptance:
- Interface is backend-agnostic and narrow.

### Step C2: Extend SSOT manifests for execution metadata

Deliver:
- Add execution metadata fields to tool manifests:
  - `entrypoint` (argv template)
  - `working_dir_policy` (repo-relative / fixed)
  - `env_allowlist` (optional)
- Add/update manifest schema validation for these fields.

Acceptance:
- Executor has sufficient data to run without hardcoded per-tool logic.

### Step C3: Implement local-process backend

Deliver:
- Spawn subprocess from manifest `entrypoint`.
- Capture stdout/stderr line-by-line.
- Apply timeouts and safe defaults.
- Return structured terminal result.

Acceptance:
- Backend can run a real command and stream lines.

### Step C4: Route `SkillExecute` through executor

Deliver:
- Replace synthetic-only branch in service with:
  - resolve tool manifest by `skill_id`
  - construct executor request
  - stream events into state store
  - transition state based on exit outcome

Acceptance:
- Unknown tool ID returns typed not-found/policy error.
- Selected tool is strictly SSOT-defined.

### Step C5: Onboard one real skill

Deliver:
- Add one non-synthetic runnable mapping (target: codex browse wrapper path already used by CLI tooling).
- Keep synthetic jobs available for controlled tests (optional).

Acceptance:
- At least one real tool executes end-to-end via `SkillExecute`.

### Step C6: Event model completion for execution

Deliver:
- Emit event types from real execution path:
  - state change (queued->running)
  - log lines (stdout/stderr channel marker)
  - progress (if parsable)
  - terminal (succeeded/failed/canceled)

Acceptance:
- `StreamJobEvents(follow=false)` shows full sequence after run.

### Step C7: Validate, document, close

Deliver:
- Integration tests for real execution routing.
- Not-found, non-zero exit, and cancellation-path tests.
- Update milestone docs and `#76` with evidence.

Acceptance criteria mapping to `#76`:
- Real skill executes via `domed`.
- Logs visible through streaming.

## 4) Test plan

### New/updated tests

- `tests/test_domed_executor_local_process.py`
  - command success/failure
  - stdout/stderr capture
  - timeout behavior
- `tests/test_domed_service_execution_routing.py`
  - manifest resolution by `skill_id`
  - end-to-end run and event stream assertions
  - unknown `skill_id` typed error
- Extend existing integration tests for real runner path.

### Validation commands

- `python3 -m pytest -q tests/test_domed_executor_local_process.py tests/test_domed_service_execution_routing.py`
- `python3 -m pytest -q tests/test_domed_service_integration.py tests/test_domed_client_stub_matrix.py`
- `python3 -m ruff check tools/domed tests`
- `python3 tools/codex/check_generated_client_only.py`
- `bash tools/domed/check_codegen_drift.sh`

## 5) Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Command execution surface grows too broad | High | enforce manifest-driven allowlist only; no arbitrary command execution |
| Deadlocks on subprocess output | Medium | line-buffered non-blocking read strategy and bounded waits |
| Event ordering regressions | Medium | single writer through store append API and ordered emission tests |
| Environment leakage from host | Medium | explicit env allowlist and constrained working directory policies |

## 6) Exit criteria for Phase C

Phase C is complete when:
1. `SkillExecute` routes to executor via SSOT manifest data.
2. At least one non-synthetic skill executes end-to-end.
3. Streaming exposes stdout/stderr/progress/terminal events.
4. Tests cover success, failure, unknown-skill, and cancellation paths.
5. `#76` has reproducible evidence and can be closed.
