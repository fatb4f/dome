# M5 Legacy Deprecation and Removal Schedule

## Scope

This schedule governs non-production legacy execution surfaces tracked in:

- `doc/milestone_domed/m5/m5_tool_migration_register.csv`

## Legacy surfaces

1. `dome-codex-skill run-skill-legacy`
- Status: deprecated (non-production compatibility path)
- Replacement: `dome-codex-skill run-skill` (generated client -> `domed`)

2. `tools/codex/browse_skill.py::run_task` subprocess path
- Status: deprecated backend used by `run-skill-legacy`
- Replacement: `run_task_via_domed`

## Timeline

Milestone start: February 25, 2026

1. Deprecation notice phase
- Start: February 25, 2026
- End: March 10, 2026
- Actions:
  - keep explicit deprecation warning in CLI output
  - preserve compatibility for short transition window

2. Soft removal phase
- Start: March 10, 2026
- End: March 24, 2026
- Actions:
  - disable legacy path in default operational docs/runbooks
  - require explicit override flag/env for any remaining local use

3. Hard removal phase (D8 target)
- Target date: March 24, 2026
- Actions:
  - remove `run-skill-legacy` command
  - remove/retire `run_task` subprocess execution path
  - update register entries from `DEPRECATE_REMOVE` to removed

## Enforcement linkage

- CI guardrails:
  - `tools/codex/check_generated_client_only.py`
  - `tools/codex/check_subprocess_policy.py`
- D8 issue: `#70`

