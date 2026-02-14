import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.audit_drill import collect_audit_bundle  # noqa: E402
from tools.orchestrator.run_demo import run_demo  # noqa: E402


def test_run_manifest_contains_provenance_and_hash_chain(tmp_path: Path) -> None:
    pre_contract = tmp_path / "contract.json"
    pre_contract.write_text(
        json.dumps(
            {
                "packet_id": "pkt-prov-001",
                "base_ref": "main",
                "budgets": {"iteration_budget": 2},
                "actions": {"test": ["python", "-c", "print('ok')"]},
                "plan_card": {"why": "provenance", "what": "hash chain"},
            }
        ),
        encoding="utf-8",
    )
    run_root = tmp_path / "runs"
    out = run_demo(
        pre_contract_path=pre_contract,
        run_root=run_root,
        state_space_path=ROOT / "ssot/examples/state.space.json",
        reason_codes_path=ROOT / "ssot/policy/reason.codes.json",
        event_log=tmp_path / "events.jsonl",
        otel_export=False,
    )
    run_id = out["run_id"]
    manifest = json.loads(Path(out["run_manifest_path"]).read_text(encoding="utf-8"))
    assert manifest["runtime"]["repo_commit_sha"]
    assert manifest["runtime"]["tool_versions"]["python"]
    assert manifest["runtime"]["environment_fingerprint"]["platform"]
    assert manifest["inputs"]["input_hashes"]["work_queue_sha256"]

    audit = collect_audit_bundle(run_root=run_root, run_id=run_id)
    assert audit["hashes"]["work_queue_sha256"] == manifest["inputs"]["input_hashes"]["work_queue_sha256"]
