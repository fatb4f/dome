# Observability (OTLP backend, Langfuse example)

This repo wires a **minimal standard-first** telemetry path:

- **Instrumentation:** OpenLLMetry (Traceloop SDK)
- **Semantic convention:** OpenTelemetry **GenAI** attributes (`gen_ai.*`) are the canonical span schema
- **Backend:** OTLP backend via OpenTelemetry Collector (Langfuse config is included in this repo)

## Why a Collector
A local Collector gives you:
- one stable OTLP endpoint for apps
- credential handling in one place
- a clean place to add processors / schema normalization later

## Prereqs
- Docker + Docker Compose

## 1) Set env vars
Copy and fill:

```bash
cp .env.example .env
```

Generate the Basic Auth value for Langfuse OTEL:

```bash
./scripts/gen_langfuse_auth.sh
```

## 2) Run the collector

```bash
docker compose up -d
```

Collector exposes:
- OTLP/gRPC: `localhost:4317`
- OTLP/HTTP: `localhost:4318`

## 3) Point apps at the collector

### Python (Traceloop SDK)
Set:

```bash
export TRACELOOP_BASE_URL=http://localhost:4318
```

Traceloop appends `/v1/traces` automatically.

## Langfuse OTEL endpoints
Langfuse expects OTLP/HTTP traces at:
- Cloud (EU): `https://cloud.langfuse.com/api/public/otel`
- Cloud (US): `https://us.cloud.langfuse.com/api/public/otel`
- Self-hosted: `https://<your-langfuse>/api/public/otel`

The OTLP/HTTP exporter appends `/v1/traces`.

## Memory daemon + binder (shadow mode)

Run one materialization + binder pass:

```bash
python tools/telemetry/memoryd.py \
  --once \
  --db ops/memory/memory.duckdb \
  --run-root ops/runtime/runs \
  --checkpoint ops/memory/checkpoints/materialize.state.json \
  --run-binder \
  --binder-mode strict
```

Validate checkpoint health including binder output:

```bash
python tools/telemetry/memory_alert_gate.py \
  --checkpoint ops/memory/checkpoints/materialize.state.json \
  --min-processed-runs 1 \
  --min-binder-derived-rows 1
```
