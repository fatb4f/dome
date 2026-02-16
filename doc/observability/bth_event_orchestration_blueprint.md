# Behind-the-Scenes Event Orchestration Blueprint

## Goal

Design a high-signal event-driven glue layer for local workflows and components:
- window/session control plane
- editor/runtime workflow automation
- package/security monitoring
- deterministic actions with auditable evidence

## Canonical Event Envelope

Use one shape across producers:

```json
{
  "topic": "domain.component.action.result",
  "ts_utc": "2026-02-16T19:00:00Z",
  "source": "producer-name",
  "component": "hyprwm|quickshell|systemd|...",
  "severity": "info|warn|error|critical",
  "correlation_id": "uuid-or-run-id",
  "host": "archlinux",
  "session_id": "optional-session-id",
  "workspace": "optional-path-or-tag",
  "payload": {}
}
```

Optional fields for actionability:
- `run_id`
- `attempt`
- `exit_code`
- `duration_ms`
- `evidence_path`

## High-Signal Topics by Area

### HyprWM
- `desktop.workspace.changed`
- `desktop.window.focus.changed`
- `desktop.monitor.layout.changed`
- `desktop.idle.locked`
- `desktop.session.reloaded`

Use-cases:
- context-aware profile routing
- workspace/session recovery
- monitor/layout drift remediation

### Quickshell
- `shell.action.invoked`
- `shell.workflow.triggered`
- `shell.widget.error`

Use-cases:
- explicit human-in-the-loop trigger into watcher profiles
- one-click runbook actions

### System Logs + systemd
- `service.start.failed`
- `service.restart.throttled`
- `service.unit.flapping`
- `system.coredump.created`
- `system.oom.killed`

Use-cases:
- deterministic triage (collect logs, status, config snapshot)
- guarded restart/reconcile

### Dotfiles
- `config.change.detected`
- `config.apply.started`
- `config.apply.completed`
- `config.apply.failed`
- `config.drift.detected`

Use-cases:
- auto-apply with validation gate
- rollback prompts on failure

### VSCode
- `editor.task.failed`
- `editor.test.failed`
- `editor.extension.crashed`

Use-cases:
- targeted diagnostics and minimal remediation

### Yazi
- `file.batch.completed`
- `file.path.access.denied`
- `file.op.delete|move|copy`

Use-cases:
- file workflow triggers and audit trail

### Zellij
- `term.session.started|ended`
- `term.pane.command.failed`
- `term.layout.changed`

Use-cases:
- session summaries
- failure routing to diagnostics

### Helix / Neovim
- `editor.save`
- `editor.lsp.diagnostic.error`
- `editor.format.failed`
- `editor.test.failed`

Use-cases:
- on-save checks
- focused lint/test loops

### Marimo
- `notebook.cell.failed`
- `notebook.kernel.restarted`
- `notebook.run.completed`

Use-cases:
- notebook reliability and reproducibility capture

### Python Workflows
- `python.test.failed`
- `python.lint.failed`
- `python.run.timeout`
- `python.dep.vuln.detected`

Use-cases:
- deterministic CI-like local gates
- dependency risk routing

## MCP and A2A Fit

### MCP (request/response execution plane)
Use MCP for deterministic actuators:
- run specific checks (`pytest`, lint, schema validation)
- gather evidence bundles
- apply constrained remediations

Pattern:
- watcher event trigger -> profile action -> MCP tool invocation -> result event

### A2A (cross-agent/cross-repo control plane)
Use A2A when orchestration spans multiple agents or repositories:
- planner/checker/implementer collaboration
- remote execution or delegated triage

Pattern:
- normalized local event -> A2A envelope -> remote agent action -> normalized return event

## Hygiene Guardrails

- idempotent handlers by default
- bounded retries and exponential backoff
- per-topic debounce (`topic + workspace + profile`)
- dead-letter capture for failed handlers
- append-only JSONL evidence
- strict redaction for secrets/tokens/PII
- stable schema versioning for replay
- explicit owner per topic/profile
- SLOs for automation:
  - trigger-to-action latency
  - handler success rate
  - false-positive rate

## Practical First Rollout

1. `service.start.failed` triage profile
2. `editor.test.failed` focused diagnostics
3. `package.txn.completed` compatibility smoke checks
4. `config.apply.failed` rollback and alert profile
5. `system.coredump.created` incident bundle profile

## Existing Local Implementation Pointers

- Event router: `~/src/watcher/bin/watchctl`
- Codex session source: `~/src/watcher/bin/codex-event-source`
- Package/security source: `~/src/watcher/bin/system-security-package-event-source`
- Profile map: `~/src/watcher/config/profiles.yaml`
- Control panes:
  - `~/src/watcher/bin/watchctl-control-dashboard`
  - `~/src/watcher/bin/watchctl-dome-oracle-status`
  - `~/src/watcher/bin/watchctl-opsctrl-dashboard` (auto-detects `~/src/opsctrl`)
- Alerts/evidence:
  - `~/.local/state/codex/watcher/watchctl-events.jsonl`
  - `~/.local/state/codex/watcher/codex-alerts.jsonl`
- Zellij layout (dotfiles): `~/src/dotfiles/dot_config/zellij/layouts/ops-event-mesh.kdl`
