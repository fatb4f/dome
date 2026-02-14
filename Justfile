set shell := ["bash", "-lc"]

clean-runtime:
    rm -rf ops/runtime

test:
    pytest -q

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
    rm -rf ops/runtime
    python tools/orchestrator/run_demo.py \
      --pre-contract ssot/examples/demo.pre_contract.json \
      --run-root ops/runtime/runs \
      --state-space ssot/examples/state.space.json \
      --reason-codes ssot/policy/reason.codes.json

ci: clean-runtime test smoke
