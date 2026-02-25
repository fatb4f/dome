# M5-D7 Production Cutover Runbook

## Objective

Operate production execution through `domed` only, with generated thin clients.

## Production path

1. Start daemon:

```bash
domed --bind 127.0.0.1:50051 --db-path ops/runtime/domed/domed.sqlite
```

2. Verify daemon:

```bash
python tools/domed/operator_healthcheck.py --endpoint 127.0.0.1:50051 --profile work
```

3. Execute production command path:

```bash
dome-codex-skill run-skill \
  --task-json /path/to/task.json \
  --domed-endpoint 127.0.0.1:50051 \
  --profile work
```

## Non-production path (deprecated)

`run-skill-legacy` is explicitly deprecated and scheduled for removal (see D6 schedule).

## Enforcement gates

- `tools/codex/check_generated_client_only.py`
- `tools/codex/check_subprocess_policy.py`
- CI workflow: `.github/workflows/mvp-loop-gate.yml`

## Cutover acceptance checks

1. `run-skill` uses generated client path only.
2. subprocess policy guard passes.
3. operator healthcheck succeeds against running daemon.

