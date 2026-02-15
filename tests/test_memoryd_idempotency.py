import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.telemetry import memoryd  # noqa: E402


def test_pending_runs_is_stable_and_filtered() -> None:
    discovered = ["run-001", "run-002", "run-003"]
    processed = ["run-002"]
    assert memoryd.pending_runs(discovered, processed) == ["run-001", "run-003"]


def test_checkpoint_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    payload = {"processed_runs": ["run-001", "run-002"]}
    memoryd.save_checkpoint(path, payload)
    out = memoryd.load_checkpoint(path)
    assert out == payload


def test_snapshot_from_run_dir_defaults_when_artifacts_missing(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-xyz"
    run_dir.mkdir(parents=True)
    out = memoryd.snapshot_from_run_dir(run_dir)
    assert out.run_id == "run-xyz"
    assert out.base_ref == "unknown"
    assert out.gate_status == "UNKNOWN"
    assert out.promotion_decision == "UNKNOWN"


def test_snapshot_from_run_dir_reads_primary_fields(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-abc"
    (run_dir / "gate").mkdir(parents=True)
    (run_dir / "promotion").mkdir(parents=True)
    (run_dir / "work.queue.json").write_text(json.dumps({"base_ref": "main"}), encoding="utf-8")
    (run_dir / "gate" / "gate.decision.json").write_text(
        json.dumps({"status": "APPROVE", "substrate_status": "PROMOTE", "risk_score": 12, "confidence": 0.91}),
        encoding="utf-8",
    )
    (run_dir / "promotion" / "promotion.decision.json").write_text(
        json.dumps({"decision": "APPROVE"}),
        encoding="utf-8",
    )
    (run_dir / "run.manifest.json").write_text(
        json.dumps({"runtime": {"repo_commit_sha": "abc123"}}),
        encoding="utf-8",
    )
    out = memoryd.snapshot_from_run_dir(run_dir)
    assert out.base_ref == "main"
    assert out.gate_status == "APPROVE"
    assert out.substrate_status == "PROMOTE"
    assert out.risk_score == 12
    assert abs(out.confidence - 0.91) < 0.0001
    assert out.repo_commit_sha == "abc123"

