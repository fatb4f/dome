from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.otel_stage import stage_span  # noqa: E402


def test_stage_span_noop_when_disabled() -> None:
    with stage_span("dome.test.stage", {"run.id": "run-001"}, enabled=False) as span:
        assert span is None


def test_stage_span_enabled_is_safe_without_backend() -> None:
    with stage_span("dome.test.stage", {"run.id": "run-002", "task.count": 3}, enabled=True):
        pass

