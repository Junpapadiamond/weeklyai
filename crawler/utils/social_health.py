"""
Social source health report helpers.

Writes `crawler/data/social_source_health.json` unless disabled by env:
- SOCIAL_HEALTH_DISABLE_WRITE=true
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict


_UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
_CRAWLER_DIR = os.path.dirname(_UTILS_DIR)
_DATA_DIR = os.path.join(_CRAWLER_DIR, "data")
DEFAULT_HEALTH_FILE = os.path.join(_DATA_DIR, "social_source_health.json")


def _to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _write_enabled() -> bool:
    raw = (os.getenv("SOCIAL_HEALTH_DISABLE_WRITE") or "").strip().lower()
    return raw not in {"1", "true", "yes", "on"}


def _health_path() -> str:
    override = (os.getenv("SOCIAL_HEALTH_FILE") or "").strip()
    return override or DEFAULT_HEALTH_FILE


def load_social_health() -> Dict[str, Any]:
    path = _health_path()
    if not os.path.exists(path):
        return {"updated_at": "", "sources": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {"updated_at": "", "sources": {}}
    if isinstance(data, dict):
        if "sources" not in data or not isinstance(data.get("sources"), dict):
            data["sources"] = {}
        return data
    return {"updated_at": "", "sources": {}}


def save_social_health(payload: Dict[str, Any]) -> None:
    if not _write_enabled():
        return
    path = _health_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def update_source_health(source: str, details: Dict[str, Any]) -> None:
    report = load_social_health()
    report["updated_at"] = _to_iso(datetime.now(timezone.utc))
    sources = report.get("sources")
    if not isinstance(sources, dict):
        sources = {}
        report["sources"] = sources

    payload = dict(details or {})
    payload["updated_at"] = report["updated_at"]
    sources[source] = payload
    save_social_health(report)
