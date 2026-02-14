from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.security import (  # noqa: E402
    assert_runtime_path,
    redact_sensitive_payload,
    redact_sensitive_text,
)


def test_runtime_path_rejects_absolute() -> None:
    with pytest.raises(ValueError):
        assert_runtime_path(Path("/tmp/outside"), ROOT, "--run-root")


def test_runtime_path_rejects_parent_traversal() -> None:
    with pytest.raises(ValueError):
        assert_runtime_path(Path("ops/runtime/../outside"), ROOT, "--run-root")


def test_runtime_path_accepts_ops_runtime_descendant() -> None:
    accepted = assert_runtime_path(Path("ops/runtime/runs"), ROOT, "--run-root")
    assert accepted == Path("ops/runtime/runs")


def test_redaction_scrubs_sensitive_keys_and_assignments() -> None:
    payload = {
        "notes": "token=abc123 api_key: zzz password=qwerty",
        "api_key": "super-secret-key",
        "nested": {"secret_value": "keep-me-out"},
    }
    redacted = redact_sensitive_payload(payload)
    assert "abc123" not in redacted["notes"]
    assert "zzz" not in redacted["notes"]
    assert "qwerty" not in redacted["notes"]
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["nested"]["secret_value"] == "[REDACTED]"


def test_redaction_on_text_only() -> None:
    out = redact_sensitive_text("credential=abc token:xyz")
    assert "abc" not in out
    assert "xyz" not in out
