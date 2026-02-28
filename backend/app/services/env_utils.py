"""
Environment value helpers.
"""

from __future__ import annotations


def sanitize_env_value(raw: str | None, fallback: str = "") -> str:
    value = (raw if raw is not None else fallback).strip()
    if len(value) >= 2 and ((value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'")):
        value = value[1:-1]
    # Guard against literal escaped control chars leaked by some env providers.
    return value.replace("\\n", "").replace("\\r", "").strip()

