from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.substrate_layout import ensure_substrate_layout


def test_substrate_layout_and_doctor(tmp_path: Path) -> None:
    ensure_substrate_layout(tmp_path, "run-x")
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/orchestrator/state_doctor.py"),
            "--run-root",
            str(tmp_path),
            "--run-id",
            "run-x",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
