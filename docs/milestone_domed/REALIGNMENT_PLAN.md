# Domed realignment plan (authoritative)

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
- Emit provenance (commit SHA, env fingerprint, tool versions)

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

### 3.3 Discovery model

Introduce a dedicated RPC (preferred) or extend existing:

- `ListTools` (or `ListSkills`) returns:
  - `tool_id` / `skill_id`
  - version
  - short description
  - input schema ref (JSON schema)
  - output schema ref
  - executor backend (initially: `local-process`)

### 3.4 Execution model

- `SkillExecute` becomes the generic “run request” path.
- `domed` routes `skill_id` to a configured executor.
- **Initial backend:** local process execution of the existing runner (e.g., `dome-codex-skill` / codex-browse wrappers).
- Events/logging become first-class streamed events.

### 3.5 Streaming semantics

- `StreamJobEvents(follow=true)` must block/poll and stream new events until terminal state.
- `since_seq` must resume from a sequence number.

### 3.6 Provenance

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

### Phase B — Real discovery surface

**Deliverables**
- New discovery RPC (or expanded `ListCapabilities`) returning a structured tool list
- Tool registry definition (static JSON/YAML committed in-repo for now)

**Acceptance criteria**
- `codex-cli` (or `dome-codex-skill`) can list tools/skills and obtain schema refs

**Work items**
- Define registry format under `ssot/` or `docs/` (single source of truth)
- Add server implementation to return the registry
- Add client CLI to print the registry

---

### Phase C — Real execution routing

**Deliverables**
- `SkillExecute` routes real requests to executor(s)
- Executor v0: local process runner
- Events emitted for:
  - start
  - stdout/stderr lines
  - structured progress
  - completion/failure

**Acceptance criteria**
- A real skill (e.g., codex_web_browse wrapper) executes via `domed` end-to-end
- Logs are visible via streaming

**Work items**
- Add executor interface
- Implement local-process executor
- Integrate with existing skill runner module(s)

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

### Phase E — Docs + contracts re-alignment

**Deliverables**
- Update docs to match code (`doc/skills/*`, milestone docs)
- Enforce contract validation in the run path (if required)

**Acceptance criteria**
- documented CLI flags and server semantics match implementation
- CI asserts doc/code alignment where feasible

## 5. Risks & mitigations

- **UDS portability (Windows):** keep TCP fallback; scope UDS as “best-effort”.
- **Executor complexity:** start with local-process; keep interface narrow.
- **Schema drift:** make registry the SSOT; validate in CI.

## 6. Definition of done

`domed` is considered realigned when:

- It can be installed and run as a user service.
- It exposes a discoverable tool list with schemas.
- It executes at least one real tool/skill end-to-end.
- It streams events correctly (`follow`, `since_seq`).
- It emits provenance suitable for debugging/audit.
