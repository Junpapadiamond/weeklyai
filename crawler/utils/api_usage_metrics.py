#!/usr/bin/env python3
"""
API usage metrics helpers.

Stores daily API usage for crawler providers in:
  crawler/data/metrics/api_usage_daily.json
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _crawler_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_metrics_path() -> str:
    return os.path.join(_crawler_root(), "data", "metrics", "api_usage_daily.json")


def _resolve_metrics_path() -> str:
    custom = (os.environ.get("API_USAGE_DAILY_FILE") or "").strip()
    if custom:
        return custom
    return default_metrics_path()


def infer_script_name() -> str:
    override = (os.environ.get("WEEKLYAI_CALLER_SCRIPT") or "").strip()
    if override:
        return override
    argv0 = ""
    if sys.argv:
        argv0 = str(sys.argv[0] or "").strip()
    if not argv0:
        return "unknown"
    return os.path.basename(argv0)


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _safe_load_json(path: str) -> Dict[str, Any]:
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def _safe_save_json(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _ensure_counter(root: Dict[str, Any], key: str) -> Dict[str, Any]:
    bucket = root.get(key)
    if not isinstance(bucket, dict):
        bucket = {
            "search_requests": 0,
            "chat_requests": 0,
            "input_tokens": 0,
            "output_tokens": 0,
        }
        root[key] = bucket
    return bucket


def _add_usage(
    bucket: Dict[str, Any],
    *,
    search_requests: int,
    chat_requests: int,
    input_tokens: int,
    output_tokens: int,
) -> None:
    bucket["search_requests"] = int(bucket.get("search_requests", 0)) + int(max(search_requests, 0))
    bucket["chat_requests"] = int(bucket.get("chat_requests", 0)) + int(max(chat_requests, 0))
    bucket["input_tokens"] = int(bucket.get("input_tokens", 0)) + int(max(input_tokens, 0))
    bucket["output_tokens"] = int(bucket.get("output_tokens", 0)) + int(max(output_tokens, 0))


def record_api_usage(
    *,
    provider: str,
    search_requests: int = 0,
    chat_requests: int = 0,
    input_tokens: int = 0,
    output_tokens: int = 0,
    script_name: Optional[str] = None,
) -> None:
    provider_key = str(provider or "").strip().lower()
    if not provider_key:
        return

    script_key = str(script_name or infer_script_name()).strip() or "unknown"
    path = _resolve_metrics_path()
    data = _safe_load_json(path)
    day = _today_utc()

    day_bucket = data.get(day)
    if not isinstance(day_bucket, dict):
        day_bucket = {}
        data[day] = day_bucket

    providers_bucket = day_bucket.get("providers")
    if not isinstance(providers_bucket, dict):
        providers_bucket = {}
        day_bucket["providers"] = providers_bucket

    scripts_bucket = day_bucket.get("scripts")
    if not isinstance(scripts_bucket, dict):
        scripts_bucket = {}
        day_bucket["scripts"] = scripts_bucket

    provider_counter = _ensure_counter(providers_bucket, provider_key)
    _add_usage(
        provider_counter,
        search_requests=search_requests,
        chat_requests=chat_requests,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    script_bucket = scripts_bucket.get(script_key)
    if not isinstance(script_bucket, dict):
        script_bucket = {}
        scripts_bucket[script_key] = script_bucket
    script_provider_counter = _ensure_counter(script_bucket, provider_key)
    _add_usage(
        script_provider_counter,
        search_requests=search_requests,
        chat_requests=chat_requests,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    day_bucket["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    _safe_save_json(path, data)

