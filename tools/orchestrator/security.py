#!/usr/bin/env python
"""Security helpers for runtime path guardrails and secret redaction."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


_SENSITIVE_KEY_TOKENS = ("secret", "token", "password", "api_key", "apikey", "credential")
_ASSIGNMENT_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(token\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(password\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(secret\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(credential\s*[=:]\s*)([^\s,;]+)"),
)


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in _SENSITIVE_KEY_TOKENS)


def redact_sensitive_text(value: str) -> str:
    redacted = value
    for pattern in _ASSIGNMENT_PATTERNS:
        redacted = pattern.sub(r"\1[REDACTED]", redacted)
    return redacted


def redact_sensitive_payload(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, node in value.items():
            if _is_sensitive_key(str(key)):
                out[str(key)] = "[REDACTED]"
            else:
                out[str(key)] = redact_sensitive_payload(node)
        return out
    if isinstance(value, list):
        return [redact_sensitive_payload(item) for item in value]
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value


def assert_runtime_path(path: Path, repo_root: Path, label: str) -> Path:
    """Reject absolute/parent-traversal paths and enforce ops/runtime write root."""
    if path.is_absolute():
        raise ValueError(f"{label} must be repo-relative under ops/runtime (absolute paths are not allowed): {path}")
    if ".." in path.parts:
        raise ValueError(f"{label} must not contain parent traversal: {path}")
    allowed_root = (repo_root / "ops" / "runtime").resolve()
    resolved = (repo_root / path).resolve()
    if resolved != allowed_root and allowed_root not in resolved.parents:
        raise ValueError(f"{label} must resolve under ops/runtime: {path}")
    return path
