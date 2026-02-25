---
name: codex_web_browse
description: DOME wrapper skill for codex-browse contract-validated browsing tasks and identity-graph pin checks.
---

## Purpose
Expose `codex-browse` as a DOME-managed skill surface with pinned contract validation against `identity-graph`.

## Entrypoint
- Binary wrapper: `tools/codex/dome_cli.py`
- Validate contracts:
  - `python3 tools/codex/dome_cli.py validate-contracts --codex-browse-root <path> --identity-graph-root <path>`
- Run skill task:
  - `python3 tools/codex/dome_cli.py run-skill --codex-browse-root <path> --task-json <task.json> [--prefs-json <prefs.json>]`

## Guarantees
- Task/prefs/result envelopes validated against `codex-browse` schemas.
- `identity-graph` contract pin checks for:
  - `browse_feedback_event`
  - `browse_feedback_batch`
  - `feedforward_policy_bundle`

## Notes
- This wrapper is local and deterministic.
- It does not add browser/network behavior beyond what `codex-browse` implements.
