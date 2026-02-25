# codex-browse Skill Fold Status

## Implemented
- DOME wrapper module: `tools/codex/browse_skill.py`
- DOME CLI bridge: `tools/codex/dome_cli.py`
- Skill declaration: `doc/skills/codex_web_browse/SKILL.md`

## Contract gates
- Validates codex-browse `task/result/prefs` schemas before/after runner invocation.
- Validates identity-graph pinned contracts:
  - `browse_feedback_event@1.0.0`
  - `browse_feedback_batch@1.0.0`
  - `feedforward_policy_bundle@1.0.0`

## Commands
```bash
python3 tools/codex/dome_cli.py validate-contracts \
  --codex-browse-root /home/src404/src/codex-browse \
  --identity-graph-root /home/src404/src/identity-graph

python3 tools/codex/dome_cli.py run-skill \
  --codex-browse-root /home/src404/src/codex-browse \
  --task-json /path/to/task.json \
  --prefs-json /path/to/prefs.json
```

## Remaining
- Add `dome` console script entrypoint mapping subcommands (`plan`, `execute`, `gate`, `promote`, `validate-contracts`).
- Add replay/fuzz/hypothesis harness for skill task envelopes and emitted feedback events.
