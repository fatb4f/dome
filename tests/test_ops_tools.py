import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_alert_gate_script_pass_and_fail(tmp_path: Path) -> None:
    summary = {
        "run_id": "run-1",
        "results": [
            {"task_id": "a", "status": "PASS", "attempts": 1},
            {"task_id": "b", "status": "PASS", "attempts": 3},
        ],
    }
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    ok = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/orchestrator/alert_gate.py"),
            "--summary",
            str(summary_path),
            "--max-fail-ratio",
            "0.5",
            "--max-total-retries",
            "5",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert ok.returncode == 0

    fail = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/orchestrator/alert_gate.py"),
            "--summary",
            str(summary_path),
            "--max-fail-ratio",
            "0.0",
            "--max-total-retries",
            "0",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert fail.returncode == 2


def test_dlq_reprocess_script_outputs_manifest(tmp_path: Path) -> None:
    run_id = "run-dlq-1"
    dlq_dir = tmp_path / "runs" / run_id / "dlq"
    dlq_dir.mkdir(parents=True)
    (dlq_dir / "task-1.dlq.json").write_text(
        json.dumps({"task_id": "task-1", "reason_code": "TRANSIENT.TIMEOUT", "attempts": 3}),
        encoding="utf-8",
    )
    out_path = tmp_path / "dlq.out.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/orchestrator/dlq_reprocess.py"),
            "--run-root",
            str(tmp_path / "runs"),
            "--run-id",
            run_id,
            "--out",
            str(out_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == run_id
    assert payload["dlq_count"] == 1
