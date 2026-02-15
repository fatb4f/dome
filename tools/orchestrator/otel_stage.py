"""Lightweight stage-level OTel helpers for orchestrator flows."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any


def _safe_set_attrs(span: Any, attrs: dict[str, Any]) -> None:
    for key, value in attrs.items():
        if value is None:
            continue
        if isinstance(value, (str, bool, int, float)):
            span.set_attribute(key, value)
        else:
            span.set_attribute(key, str(value))


@contextmanager
def stage_span(stage: str, attrs: dict[str, Any], enabled: bool) -> Any:
    """Start a stage span when OTel is enabled, otherwise no-op."""
    if not enabled:
        yield None
        return
    try:
        from opentelemetry import trace  # type: ignore
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore
    except Exception:
        yield None
        return

    provider = trace.get_tracer_provider()
    if provider.__class__.__name__ != "TracerProvider":
        try:
            trace.set_tracer_provider(TracerProvider())
        except Exception:
            pass

    tracer = trace.get_tracer("dome.orchestrator")
    with tracer.start_as_current_span(stage) as span:
        _safe_set_attrs(span, attrs)
        yield span

