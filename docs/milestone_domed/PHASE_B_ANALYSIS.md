# Phase B Analysis (Post-Closure Gap Review)

Date: 2026-02-25
Scope: re-check Phase B against the authoritative plan after constraints update.

Update (2026-02-25, Phase B.1 closeout):
- Progressive discovery contract implemented (`ListTools` summary + `GetTool` detail).
- Manifest-first SSOT introduced under `ssot/tools/**` with compatibility fallback.
- Generated-client-only enforcement broadened.
- `just gen` and CI generation/drift gates in place.
- Manifest schema validation added to `validate-ssot` and CI.

## Status snapshot

- Issue `#73`: already closed.
- Issue `#74`: closed, with partial Phase B delivery in place.
- Authoritative constraints now require:
  - spec-in-git under `proto/**` + `ssot/**` + `generated/**`
  - progressive discovery (`ListTools` summary -> `GetTool/DescribeTool` descriptor)
  - generated-client-only usage and generation freshness gates

## What is already implemented

1. Discovery RPC exists:
   - `ListTools` in `proto/domed/v1/domed.proto`
2. Server-side discovery source is in git:
   - `ssot/domed/tool_registry.v1.json`
   - loaded by `tools/domed/service.py`
3. CLI/client discovery path uses generated stubs:
   - `tools/codex/domed_client.py`
   - `tools/codex/dome_cli.py` (`list-tools`)
4. Generated artifact drift gate exists in CI:
   - `.github/workflows/mvp-loop-gate.yml`
   - `tools/domed/check_codegen_drift.sh`

## Gaps vs authoritative Phase B

1. Progressive discovery is incomplete:
   - Missing `GetTool`/`DescribeTool` RPC for full descriptor retrieval.
   - Current `ListTools` returns full descriptor fields (`input_schema_ref`, `output_schema_ref`, `executor_backend`) instead of a lightweight summary.

2. SSOT layout does not yet match target:
   - Plan recommends `ssot/tools/<tool_id>/manifest.yaml` + per-tool schemas.
   - Current implementation uses monolithic `ssot/domed/tool_registry.v1.json`.

3. Tool descriptor depth is limited:
   - No explicit `permissions`/`side_effects` in discovery contract.
   - No schema payload fetch path (only string refs).

4. Generated-client-only gate is narrow:
   - Current checker (`tools/codex/check_generated_client_only.py`) validates only one CLI branch behavior.
   - It does not broadly detect handwritten RPC usage across all consumers.

5. `just gen` target is missing:
   - Generation scripts exist (`tools/domed/gen.sh`), but the plan calls for a standard top-level generation command.

## Info gathered for implementation planning

### Proto/API delta needed

- Add `GetTool` RPC and messages:
  - `GetToolRequest { tool_id }`
  - `GetToolResponse { status, descriptor }`
- Split current descriptor shape:
  - list summary type: id/version/title/short_description/kind
  - detailed type: schema refs, executor metadata, permissions, side effects

### SSOT data-model delta needed

- Add per-tool manifests under `ssot/tools/**`:
  - `ssot/tools/<tool_id>/manifest.yaml`
  - `ssot/tools/<tool_id>/schema/input.schema.json`
  - `ssot/tools/<tool_id>/schema/output.schema.json`
- Keep `ssot/domed/tool_registry.v1.json` only as:
  - compatibility layer, or
  - generated index derived from `ssot/tools/**`.

### Service + CLI delta needed

- `tools/domed/service.py`:
  - list endpoint reads summary data
  - `GetTool` resolves full descriptor from SSOT
- `tools/codex/domed_client.py`:
  - add `get_tool(tool_id)`
- `tools/codex/dome_cli.py`:
  - add `get-tool --tool-id <id>`

### CI/gating delta needed

- Add top-level generation entrypoint in `Justfile`:
  - `gen:` -> invoke `tools/domed/gen.sh` (+ catalog generation if applicable)
- Extend generated-client-only check:
  - detect direct `grpc.*channel` + `DomedServiceStub` usage outside approved thin-client module(s)
  - fail CI on violations.

## Recommended next execution slices

1. Contract slice:
   - proto update (`GetTool` + summary/detail split)
   - regenerate `generated/**`
   - update proto-breaking checks/tests

2. SSOT slice:
   - introduce `ssot/tools/**` manifests
   - add schema + fixture tests
   - keep compatibility loader for old registry until cutover

3. Consumer slice:
   - `domed_client.get_tool()`
   - CLI `get-tool`
   - integration tests for list + get path

4. CI slice:
   - `just gen`
   - stronger generated-client-only policy checks

## Suggestions incorporated from recent `#72` comments

1. Keep discovery progressive by contract:
   - `ListTools` returns summary only.
   - `GetTool` (or `DescribeTool`) returns full descriptor.

2. Treat `ssot/tools/**` as the target canonical shape:
   - move from registry-first to manifest-first.
   - keep `ssot/domed/tool_registry.v1.json` temporarily as compatibility/generated index only.

3. Enforce generated-client-only policy as a repo rule, not a single-path assertion:
   - CI should block handwritten gRPC channel/stub calls outside approved thin-client modules.

4. Standardize generation entrypoint and CI freshness:
   - add `just gen` (or documented equivalent) and keep generated drift checks mandatory.

5. Tracker hygiene recommendation:
   - because `#74` is closed while these deltas remain, record this as “Phase B.1 completion” (either by reopening `#74` or tracking a dedicated follow-up issue linked from `#72`).
