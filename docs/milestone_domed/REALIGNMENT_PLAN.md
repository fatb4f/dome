# Domed re-alignment plan (authoritative)

**Status:** Draft (authoritative plan for implementation)  
**Owner:** dome / domed  
**Last updated:** 2026-02-25

## 0. Purpose

Re-align `domed` to the original intent:

- `domed` runs as a **user service** (daemon) on the developer machine.
- `codex-cli` (and `dome-codex-skill`) interacts with `domed` for:
  - **tool discovery**
  - **tool/skill execution**
  - **event streaming + provenance**

This plan converts the current “proto-first skeleton daemon” into an operational gateway with a stable local contract.

## 0.1 Non-negotiable constraints

### Everything is spec’ed in git

All interfaces and inventories live in-repo and are reviewable:

- gRPC API: `proto/**`
- Tool/skill catalog + schemas: `ssot/**` (and/or `docs/**` if explicitly designated SSOT)
- Generated artifacts: `generated/**`

No runtime-only discovery source is considered authoritative.

### All usage must involve generated clients

- Any consumer of `domed` uses generated clients/stubs/types.
- No handwritten RPC calls, no “ad hoc” wire payloads.
- Spec changes must be accompanied by regenerated clients.
- CI must fail if `generated/**` is out-of-date.

## 0.2 Reference patterns

These are guiding references (not necessarily verbatim requirements):

- CLI-first skill design: https://github.com/nibzard/awesome-agentic-patterns/blob/main/patterns/cli-first-skill-design.md
- Code-first tool interface: https://github.com/nibzard/awesome-agentic-patterns/blob/main/patterns/code-first-tool-interface-pattern.md
- Code over API: https://github.com/nibzard/awesome-agentic-patterns/blob/main/patterns/code-over-api-pattern.md
- LLM-friendly API design: https://github.com/nibzard/awesome-agentic-patterns/blob/main/patterns/llm-friendly-api-design.md
- Progressive tool discovery: https://github.com/nibzard/awesome-agentic-patterns/blob/main/patterns/progressive-tool-discovery.md

## 1. Current state (what exists)

- gRPC service + generated stubs, basic job lifecycle, SQLite-backed job/event store.
- `ListCapabilities` returns a static capability.
- `SkillExecute` currently executes only synthetic jobs (`noop/log/fail`).
- Streaming RPC exists but does not tail (`follow` ignored).
- Provenance fields are placeholders.
- Transport is insecure TCP (localhost).
- User-service packaging is not present.

## 2. Target architecture

### 2.1 Runtime topology

- `domed` runs as a **systemd user service** (Linux) and/or launchd user agent (macOS) where applicable.
- `codex-cli` connects to `domed` over **local IPC**:
  - Primary: **Unix Domain Socket (UDS)** under `$XDG_RUNTIME_DIR`.
  - Fallback: loopback TCP for environments without UDS.

### 2.2 Responsibilities

`domed` is the gateway for:

1) **Discovery**
- List available tools/skills
- Return metadata: versions, descriptions, schemas/manifests, required permissions

2) **Execution**
- Accept requests to execute a tool/skill
- Dispatch to the appropriate executor (initially: local process runner)
- Persist job + events

3) **Observability**
- Stream events with correct `follow` semantics
- Provide stable, queryable job status + logs
n- Emit provenance (commit SHA, env fingerprint, tool versions)

## 3. Design decisions (authoritative)

### 3.1 Endpoint & identity

- Default endpoint becomes **UDS**:
  - `${XDG_RUNTIME_DIR}/dome/domed.sock`
- Default state becomes **XDG state**:
  - `${XDG_STATE_HOME:-~/.local/state}/dome/domed.sqlite`

### 3.2 Security

- IPC transport is local-only (UDS permissions).
- If TCP is used, bind to `127.0.0.1` only.
- No remote access.

### 3.3 Spec layout (SSOT)

**Tool/skill inventory and contracts** live in git and are the SSOT.

Recommended structure:

- `ssot/tools/<tool_id>/manifest.yaml`
  - `tool_id`, `version`, `title`, `description`
  - `kind` (tool vs skill), `executor` (e.g., `local-process`)
  - `entrypoint` (CLI command template) and default args
  - `input_schema` ref, `output_schema` ref
  - `permissions`/`side_effects` (at least “filesystem/network/process”)
- `ssot/tools/<tool_id>/schema/input.schema.json`
- `ssot/tools/<tool_id>/schema/output.schema.json`

### 3.4 Generated artifacts and gating

- Generated gRPC clients live in `generated/**`.
- Generated tool catalog indexes (if any) also live in `generated/**`.
- Repo must provide:
  - `just gen` (or equivalent) to regenerate all artifacts
  - CI: `just gen && git diff --exit-code generated/`

### 3.5 Discovery model (progressive)

Discovery should be progressive to keep the “common path” light:

- `ListTools` / `ListSkills` returns a **summary**:
  - `id`, `version`, `title`, `short_description`, `kind`
- `GetTool` / `DescribeTool` returns the **descriptor**:
  - schema refs (or schema payloads)
  - execution metadata (executor + entrypoint)
  - permissions + side effects

The discovery API reads the SSOT registry (and only that registry).

### 3.6 Execution model

- `SkillExecute` becomes the generic “run request” path.
- Routing is determined from the SSOT manifest:
  - `skill_id/tool_id` → executor backend + entrypoint
- **Initial backend:** local process execution of a CLI runner.
  - Aligns with CLI-first skill design.
  - Preserves “code over API”: tools remain code/CLI surfaces.
- Events/logging become first-class streamed events.

### 3.7 Streaming semantics

- `StreamJobEvents(follow=true)` must block/poll and stream new events until terminal state.
- `since_seq` must resume from a sequence number.

### 3.8 Provenance

`GetJobStatus` must populate:

- repository commit SHA
- tool versions (`domed`, executor)
- basic environment fingerprint:
  - python version
  - platform
  - optional git status (dirty/clean)

## 4. Phased implementation plan

### Phase A — Operate `domed` as a user service (foundation)

**Deliverables**
- systemd user unit(s): `ops/systemd/user/domed.service`
- install/uninstall helpers (Justfile targets)
- defaults updated to XDG paths + UDS

**Acceptance criteria**
- `systemctl --user start domed` starts successfully
- `dome-codex-skill` can connect without specifying endpoint
- service restart is safe; DB persists

**Work items**
- Add UDS bind support to gRPC server
- Add client-side endpoint detection:
  1) env var override
  2) UDS default
  3) TCP fallback

---

### Phase B — Spec-first discovery surface (registry + progressive RPC)

**Deliverables**
- SSOT tool registry in git (e.g., `ssot/tools/**`)
- Progressive discovery RPC(s): `ListTools` + `GetTool` (names TBD)
- Generated client usage in any CLI/consumer path

**Acceptance criteria**
- A client can list tools/skills (summary)
- A client can fetch full descriptor (schemas + execution metadata)
- No discovery data is invented at runtime; it is read from SSOT

**Work items**
- Define `manifest.yaml` shape + schema
- Add at least 1 real tool descriptor (codex browse wrapper)
- Implement server discovery endpoints from SSOT
- Add CLI commands that use generated clients for discovery

---

### Phase C — Real execution routing (executor interface + local-process backend + events)

**Deliverables**
- Executor interface inside `domed`
- Executor v0: local-process runner (spawns CLI from SSOT manifest)
- `SkillExecute` routes real `skill_id` requests to executor
- Event emission for:
  - job start
  - stdout/stderr lines
  - structured progress
  - completion/failure

**Acceptance criteria**
- A real tool/skill executes end-to-end via `domed`
- Logs visible via streaming
- The tool executed is selected strictly from SSOT (no implicit commands)

---

### Phase D — Streaming correctness + provenance

**Deliverables**
- `follow=true` tailing implementation
- `since_seq` resume correctness
- provenance fields populated

**Acceptance criteria**
- Streaming works like `tail -f` until terminal state
- status includes commit SHA and tool versions

---

### Phase E — Docs + contracts + generation alignment

**Deliverables**
- Update docs to match code (`doc/skills/*`, milestone docs)
- Enforce contract validation in the run path (if required)
- Enforce “generated clients only”:
  - repo provides generation command
  - CI gates on clean generated output

**Acceptance criteria**
- documented CLI flags and server semantics match implementation
- CI asserts generated artifacts are up to date

## 5. Risks & mitigations

- **UDS portability (Windows):** keep TCP fallback; scope UDS as “best-effort”.
- **Executor complexity:** start with local-process; keep interface narrow.
- **Schema drift:** make SSOT authoritative; validate in CI.

## 6. Definition of done

`domed` is considered realigned when:

- It can be installed and run as a user service.
- It exposes a discoverable tool list with schemas from SSOT.
- It executes at least one real tool/skill end-to-end via `domed`.
- It streams events correctly (`follow`, `since_seq`).
- It emits provenance suitable for debugging/audit.
- Tool specs and all clients are generated from in-repo specs, and CI enforces freshness.
