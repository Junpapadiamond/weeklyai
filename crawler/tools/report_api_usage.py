#!/usr/bin/env python3
"""
Generate API usage report from daily metrics file.

Usage:
  python tools/report_api_usage.py
  python tools/report_api_usage.py --days 7
  python tools/report_api_usage.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

# Ensure crawler root is importable when running from tools/.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils.api_usage_metrics import default_metrics_path


def _resolve_metrics_path() -> str:
    custom = (os.environ.get("API_USAGE_DAILY_FILE") or "").strip()
    return custom or default_metrics_path()


def _safe_load_json(path: str) -> Dict[str, Any]:
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass
    return {}


def _sort_dates(data: Dict[str, Any]) -> List[str]:
    out = []
    for key in data.keys():
        try:
            datetime.strptime(key, "%Y-%m-%d")
            out.append(key)
        except Exception:
            continue
    return sorted(out)


def _empty_counter() -> Dict[str, int]:
    return {
        "search_requests": 0,
        "chat_requests": 0,
        "input_tokens": 0,
        "output_tokens": 0,
    }


def _merge_counter(dst: Dict[str, int], src: Dict[str, Any]) -> None:
    for key in ("search_requests", "chat_requests", "input_tokens", "output_tokens"):
        try:
            dst[key] += int(src.get(key, 0) or 0)
        except Exception:
            continue


def build_report(data: Dict[str, Any], days: int) -> Dict[str, Any]:
    sorted_days = _sort_dates(data)
    if days > 0:
        sorted_days = sorted_days[-days:]

    provider_totals: Dict[str, Dict[str, int]] = {}
    script_totals: Dict[str, Dict[str, Dict[str, int]]] = {}
    grand_total = _empty_counter()

    for day in sorted_days:
        bucket = data.get(day)
        if not isinstance(bucket, dict):
            continue

        providers = bucket.get("providers")
        if isinstance(providers, dict):
            for provider, counter in providers.items():
                if not isinstance(counter, dict):
                    continue
                provider_bucket = provider_totals.setdefault(provider, _empty_counter())
                _merge_counter(provider_bucket, counter)
                _merge_counter(grand_total, counter)

        scripts = bucket.get("scripts")
        if isinstance(scripts, dict):
            for script_name, provider_map in scripts.items():
                if not isinstance(provider_map, dict):
                    continue
                script_bucket = script_totals.setdefault(script_name, {})
                for provider, counter in provider_map.items():
                    if not isinstance(counter, dict):
                        continue
                    script_provider_bucket = script_bucket.setdefault(provider, _empty_counter())
                    _merge_counter(script_provider_bucket, counter)

    return {
        "days": sorted_days,
        "provider_totals": provider_totals,
        "script_totals": script_totals,
        "grand_total": grand_total,
    }


def _format_line(label: str, counter: Dict[str, int]) -> str:
    return (
        f"{label:<24} "
        f"search={counter.get('search_requests', 0):>6} "
        f"chat={counter.get('chat_requests', 0):>6} "
        f"in_tok={counter.get('input_tokens', 0):>10} "
        f"out_tok={counter.get('output_tokens', 0):>10}"
    )


def print_report(report: Dict[str, Any], path: str) -> None:
    days = report.get("days") or []
    provider_totals = report.get("provider_totals") or {}
    script_totals = report.get("script_totals") or {}
    grand_total = report.get("grand_total") or _empty_counter()

    print("API Usage Report")
    print("=" * 88)
    print(f"Metrics file: {path}")
    if days:
        print(f"Date range: {days[0]} ~ {days[-1]} ({len(days)} days)")
    else:
        print("Date range: no data")
    print("-" * 88)

    print("By provider:")
    if not provider_totals:
        print("  (empty)")
    else:
        for provider, counter in sorted(
            provider_totals.items(),
            key=lambda x: (x[1].get("search_requests", 0) + x[1].get("chat_requests", 0)),
            reverse=True,
        ):
            print("  " + _format_line(provider, counter))

    print("-" * 88)
    print("By script/provider:")
    if not script_totals:
        print("  (empty)")
    else:
        for script_name in sorted(script_totals.keys()):
            print(f"  {script_name}")
            provider_map = script_totals.get(script_name) or {}
            for provider, counter in sorted(
                provider_map.items(),
                key=lambda x: (x[1].get("search_requests", 0) + x[1].get("chat_requests", 0)),
                reverse=True,
            ):
                print("    " + _format_line(provider, counter))

    print("-" * 88)
    print("Grand total:")
    print("  " + _format_line("all", grand_total))


def main() -> None:
    parser = argparse.ArgumentParser(description="Report crawler API usage metrics")
    parser.add_argument("--days", type=int, default=30, help="Trailing days to include (default: 30)")
    parser.add_argument("--json", action="store_true", help="Print report as JSON")
    args = parser.parse_args()

    path = _resolve_metrics_path()
    data = _safe_load_json(path)
    report = build_report(data, days=max(0, int(args.days)))

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print_report(report, path)


if __name__ == "__main__":
    main()
