# python-demo

A minimal runnable example of **Plan → Execute → Gate** where **telemetry is the only driver** for gating and state writes.

## Run (local)

1) Start the OTEL collector (forwarding to Langfuse):

```bash
cd ops/observability
cp .env.example .env
# fill keys, then:
./scripts/gen_langfuse_auth.sh
# paste LANGFUSE_AUTH into .env
docker compose up -d
```

2) Run the demo (in a new shell):

```bash
cd apps/python-demo
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Option A: install editable for the console script
pip install -e .

export TRACELOOP_BASE_URL=http://localhost:4318
mvp-agent-demo
```

Output:
- `apps/python-demo/out/state.space.json` (snapshot)
- stdout/stderr logs in `apps/python-demo/out/`

## Notes
- The demo writes artifacts to disk, but gating reads only the telemetry bundle.
- Trace export is OTLP/HTTP via Traceloop SDK; Collector forwards to Langfuse.
