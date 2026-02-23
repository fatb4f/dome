# Remote Access Plan: Cloudflare Tunnel Reuse

## Decision
Centralize remote-access architecture in `dome` as a standalone subsystem.

## Source Context
- Existing bridge infra repo: `codex-fastmcp`
- Existing hostname in use there: `mcp.meowrz.uk` (from `codex-fastmcp/Caddyfile`)
- Existing public router IP: reuse the same WAN endpoint already used by fastmcp deployment (kept outside git)

## Objective
Use the existing Cloudflare domain/tunnel footprint for phone-triggered Codex resume access, without exposing inbound SSH directly.

## Architecture
1. Edge ingress
- Cloudflare Tunnel (`cloudflared`) terminates internet ingress.
- Cloudflare Access policy gates identity/session at edge.

2. Local target
- Target is a local trigger endpoint or SSH forced-command path that only launches Codex resume flow.
- No broad shell exposure by default.

3. Session execution
- Trigger calls project-scoped resume wrapper (`flock` + `resume--last` in project CWD).
- Runtime launch delegated to user session via `app2unit`/`systemd --user`.

4. Audit and feedback
- Trigger/launch outcomes written to structured logs.
- Logs normalized into identity-graph feedback contracts where applicable.

## Reuse Strategy
1. Domain and tunnel
- Reuse the same DNS zone currently serving `mcp.meowrz.uk`.
- Add dedicated remote-access hostname(s), for example:
  - `codex-remote.<zone>`
  - `codex-trigger.<zone>`
- Keep bridge (`/mcp`) and remote-access endpoints logically separated.

2. Router/WAN
- Reuse the same router public IP path currently associated with fastmcp deployment.
- Prefer Cloudflare Tunnel origin connectivity over direct inbound port forwarding.

3. Policy isolation
- Separate Cloudflare Access app policy for remote Codex trigger.
- Short session TTL and explicit device/user constraints.
- Keys-only local auth and restricted command surface.

## Implementation Tasks
- [ ] Define `dome` remote-access contract schema (trigger request/result envelope).
- [ ] Add a `dome` runbook for Cloudflare app/tunnel policy wiring.
- [ ] Implement local trigger wrapper contract (`project_key`, lock, resume semantics).
- [ ] Add CI/static checks to ensure remote-access endpoint remains least-privilege.
- [ ] Add replay tests for trigger idempotency and lock behavior.

## Non-Goals (Current Phase)
- Full remote desktop.
- Bot-driven trigger channels (Telegram path deferred/rejected for now).
- Mandatory MFA method enforcement until hardware token rollout.

## Notes
- `dropbear + dracut` remains out-of-scope for standard post-boot Codex usage (initramfs-only use case).
- Multiplexer is optional and not required for this trigger-first model.
