import json
from pathlib import Path
import sys

import pytest

jsonschema = pytest.importorskip("jsonschema")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.run_demo import run_demo


def test_runtime_event_log_validates_against_event_schema(tmp_path: Path) -> None:
    pre_contract = tmp_path / "contract.json"
    pre_contract.write_text(
        json.dumps(
            {
                "packet_id": "pkt-event-schema-001",
                "base_ref": "main",
                "budgets": {"iteration_budget": 2},
                "actions": {"test": ["python", "-c", "print('ok')"]},
                "plan_card": {"why": "event schema", "what": "schema parity"},
            }
        ),
        encoding="utf-8",
    )

    event_log = tmp_path / "events.jsonl"
    run_demo(
        pre_contract_path=pre_contract,
        run_root=tmp_path / "runs",
        state_space_path=ROOT / "ssot/examples/state.space.json",
        reason_codes_path=ROOT / "ssot/policy/reason.codes.json",
        event_log=event_log,
        otel_export=False,
    )

    schema = json.loads((ROOT / "ssot/schemas/event.envelope.schema.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for line in event_log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        validator.validate(json.loads(line))
