from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.deprecated_path_lint import find_deprecated_references  # noqa: E402


def test_deprecated_path_lint_passes_for_current_docs() -> None:
    hits = find_deprecated_references(ROOT / "doc")
    assert hits == []
