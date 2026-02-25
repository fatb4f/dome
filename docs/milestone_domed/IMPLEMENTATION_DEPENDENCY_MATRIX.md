# Domed Re-Alignment: Implementation Dependency Matrix and Plan

Date: 2026-02-25
Scope: actionable implementation sequencing after Phase B re-analysis.

## 1) Dependency matrix

Legend:
- `Blocker`: must complete before dependent work starts.
- `Soft dep`: can start in parallel, but final merge depends on upstream output.

| ID | Workstream | Primary outputs | Depends on | Type | Unblocks |
|---|---|---|---|---|---|
| W1 | Contract evolution (progressive discovery) | `proto/domed/v1/domed.proto` updates for `ListTools` summary + `GetTool` detail; regenerated `generated/**` | None | - | W3, W4, W5 |
| W2 | SSOT tool manifest model | `ssot/tools/<tool_id>/manifest.yaml` + per-tool schemas + compatibility index strategy | None | - | W3, W4 |
| W3 | Discovery service implementation | `tools/domed/service.py` list/get logic from SSOT manifests | W1, W2 | Blocker | W4, W6 |
| W4 | Thin-client + CLI implementation | `tools/codex/domed_client.py` `get_tool()`; `tools/codex/dome_cli.py` `get-tool` command | W1, W3 | Blocker | W6 |
| W5 | Generation entrypoint standardization | `Justfile` `gen` target; generation docs | W1 | Soft dep | W6 |
| W6 | CI/policy enforcement hardening | generated drift gate via `gen`; broaden generated-client-only checks | W4, W5 | Blocker | W7 |
| W7 | Docs/tracker convergence | milestone docs + issue state alignment (`#72`/Phase B.1) | W3, W4, W6 | Soft dep | Close Phase B.1 |

## 2) Artifact-level dependencies

| Artifact | Produced by | Consumed by |
|---|---|---|
| `proto/domed/v1/domed.proto` (`GetTool`, summary/detail split) | W1 | W3, W4, codegen checks |
| `generated/python/domed/v1/*.py` + descriptor + manifest | W1 | W4, tests, CI |
| `ssot/tools/**/manifest.yaml` + schemas | W2 | W3, W7 |
| Compatibility index (`ssot/domed/tool_registry.v1.json`, temporary) | W2 | W3 (transition path) |
| `tools/domed/service.py` discovery handlers | W3 | W4, integration tests |
| `tools/codex/domed_client.py` + `tools/codex/dome_cli.py` | W4 | CLI tests, policy checks |
| `Justfile` `gen` + CI workflow adjustments | W5/W6 | all contributors + CI |

## 3) Implementation plan (execution order)

### Step 1: W1 contract slice

Deliver:
- Add RPC:
  - `GetTool(GetToolRequest) returns (GetToolResponse)`
- Make `ListTools` return summary only.
- Define detail descriptor payload for `GetTool`.
- Regenerate `generated/**`.

Acceptance:
- Proto compiles and generated files are updated.
- Existing proto compatibility checks pass.

Validation:
- `bash tools/domed/check_proto_breaking.sh --base-ref origin/main`
- `bash tools/domed/check_codegen_drift.sh`
- `pytest -q tests/test_domed_codegen.py`

### Step 2: W2 SSOT manifest slice

Deliver:
- Add `ssot/tools/<tool_id>/manifest.yaml`.
- Add per-tool `schema/input.schema.json` and `schema/output.schema.json`.
- Keep legacy registry as compatibility index during migration.

Acceptance:
- At least one real tool manifest exists (codex-browse wrapper target).
- Manifest parsing/validation tests exist.

Validation:
- `pytest -q tests/test_domed_tool_registry.py` (or renamed manifest tests)
- `pytest -q tests/test_schema_examples_validate.py tests/test_ssot_roundtrip.py`

### Step 3: W3 service slice

Deliver:
- `ListTools` reads manifest summaries.
- `GetTool` resolves full descriptor from SSOT manifest.
- Stable not-found semantics for unknown tool IDs.

Acceptance:
- Discovery data is loaded from SSOT only.
- No runtime-invented discovery payloads.

Validation:
- `pytest -q tests/test_domed_service_integration.py`

### Step 4: W4 consumer slice

Deliver:
- `DomedClient.get_tool(tool_id)`.
- CLI `get-tool --tool-id`.
- Preserve generated-client-only behavior.

Acceptance:
- End-to-end list -> get flow works over daemon endpoint.

Validation:
- `pytest -q tests/test_domed_client_stub_matrix.py tests/test_dome_cli_list_tools.py`
- Add/extend test for `get-tool` CLI path.

### Step 5: W5 generation ergonomics slice

Deliver:
- Add `just gen` that runs canonical generation (`tools/domed/gen.sh` + any required indexes).
- Document in milestone docs and README.

Acceptance:
- One command reproduces all generated outputs.

Validation:
- `just gen`
- `git diff --exit-code generated/`

### Step 6: W6 CI/policy hardening slice

Deliver:
- CI calls standardized generation entrypoint.
- Broaden generated-client-only checker:
  - detect direct `grpc.*channel` / `DomedServiceStub` usage outside approved thin-client modules.

Acceptance:
- CI fails on handwritten RPC usage outside policy.
- CI fails on generated drift.

Validation:
- `.github/workflows/mvp-loop-gate.yml` green.
- `python tools/codex/check_generated_client_only.py` green with policy tests.

### Step 7: W7 docs/tracker completion slice

Deliver:
- Update `docs/milestone_domed/PHASE_B_ANALYSIS.md` status to complete.
- Align issue tracker state (Phase B.1 complete under `#72`).

Acceptance:
- Documentation and issue state match actual implementation.

## 4) Parallelization strategy

Safe parallel starts:
- W1 and W2 can start immediately in parallel.
- W5 can start after W1 proto shape is stable enough.

Merge-critical path:
- W1 -> W3 -> W4 -> W6
- W2 must join before W3 finalization.

## 5) Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| Proto churn breaks clients | Medium | Keep changes additive where possible; regenerate and run stub matrix tests each change |
| SSOT migration leaves dual sources inconsistent | High | Treat manifests as source of truth; generate compatibility index deterministically |
| Overbroad RPC linting blocks valid internals | Medium | Define explicit allowlist modules for direct gRPC usage |
| CI runtime drift | Medium | Use single `just gen` path and enforce in CI |

## 6) Definition of done for this plan

Done when:
1. Progressive discovery is fully implemented (`ListTools` summary + `GetTool` detail).
2. Discovery reads from `ssot/tools/**` manifests.
3. CLI/client discovery functions are generated-client-only and fully tested.
4. CI enforces generation freshness and RPC usage policy repo-wide.
5. Tracker/docs state are synchronized with implementation reality.
