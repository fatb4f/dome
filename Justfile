set shell := ["bash", "-lc"]

clean-runtime:
    rm -rf ops/runtime/runs ops/runtime/mcp_events.jsonl

test:
    pytest -q

lint:
    python -m ruff check tools tests

validate-ssot:
    pytest -q tests/test_schema_examples_validate.py tests/test_ssot_policy_validate.py tests/test_ssot_roundtrip.py

ingest-catalog:
    python tools/orchestrator/ingest_pattern_catalog.py \
      --seed ssot/sources/awesome_agentic_patterns.seed.json \
      --out ssot/catalog/pattern.catalog.v1.json

plan:
    python tools/orchestrator/planner.py \
      --pre-contract ssot/examples/demo.pre_contract.json \
      --out ops/runtime/work.queue.json

implement:
    python tools/orchestrator/implementers.py \
      --work-queue ops/runtime/work.queue.json \
      --run-root ops/runtime/runs \
      --max-retries 2

check:
    python tools/orchestrator/checkers.py \
      --run-root ops/runtime/runs \
      --run-id pkt-dome-demo-0001 \
      --reason-codes ssot/policy/reason.codes.json \
      --risk-threshold 60

promote:
    python tools/orchestrator/promote.py \
      --run-root ops/runtime/runs \
      --run-id pkt-dome-demo-0001

state:
    python tools/orchestrator/state_writer.py \
      --run-root ops/runtime/runs \
      --run-id pkt-dome-demo-0001 \
      --state-space ssot/examples/state.space.json \
      --out ops/runtime/state.space.json

smoke:
    rm -rf ops/runtime/runs ops/runtime/mcp_events.jsonl
    python tools/orchestrator/run_demo.py \
      --pre-contract ssot/examples/demo.pre_contract.json \
      --run-root ops/runtime/runs \
      --state-space ssot/examples/state.space.json \
      --reason-codes ssot/policy/reason.codes.json

live-fix-demo:
    rm -rf ops/runtime/runs ops/runtime/mcp_events.jsonl
    python tools/orchestrator/run_live_fix_demo.py \
      --run-root ops/runtime/runs \
      --state-space ssot/examples/state.space.json \
      --reason-codes ssot/policy/reason.codes.json

ci: clean-runtime validate-ssot test smoke

codex-meta:
    python tools/codex/generate_context.py \
      --project dome=/home/src404/src/dome \
      --project oracle=/home/src404/src/oracle
