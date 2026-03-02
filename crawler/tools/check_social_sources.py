#!/usr/bin/env python3
"""
Check social source availability and emit actionable recommendations.

Outputs:
- Console summary
- Optional health write to crawler/data/social_source_health.json (source=diagnostics)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import requests

# project path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils.social_health import update_source_health
from utils.social_sources import (
    load_x_accounts_with_source,
    load_x_fallback_config,
    load_youtube_channel_configs_with_source,
)


def _to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _probe(url: str, timeout: int = 10) -> Tuple[int, str]:
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "WeeklyAI/1.0 source-check"},
        )
        return int(resp.status_code), ""
    except requests.Timeout:
        return 0, "timeout"
    except Exception as exc:
        return 0, str(exc)


def _load_blogs_news_counts() -> Dict[str, int]:
    path = os.path.join(PROJECT_ROOT, "data", "blogs_news.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    counter = Counter()
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                counter[(item.get("source") or "unknown").strip().lower()] += 1
    return dict(counter)


def check_youtube(timeout: int) -> Dict[str, Any]:
    channels, source = load_youtube_channel_configs_with_source()
    status_counter = Counter()
    invalid_channels: List[str] = []
    timeout_channels: List[str] = []
    for cfg in channels[:80]:
        if not bool(cfg.get("enabled", True)):
            continue
        channel_id = str(cfg.get("channel_id") or "").strip()
        if not channel_id:
            continue
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        status, err = _probe(url, timeout=timeout)
        if status == 0:
            status_counter[f"error:{err or 'unknown'}"] += 1
            timeout_channels.append(channel_id)
            continue
        status_counter[str(status)] += 1
        if status == 404:
            invalid_channels.append(channel_id)

    recommendations: List[str] = []
    if invalid_channels:
        recommendations.append(f"replace_invalid_channel_ids:{','.join(invalid_channels[:10])}")
    if timeout_channels:
        recommendations.append("youtube_network_timeouts_detected")
    return {
        "configured_channels": len(channels),
        "source": source,
        "status_breakdown": dict(status_counter),
        "invalid_channels": invalid_channels,
        "recommendations": recommendations,
    }


def check_x(timeout: int) -> Dict[str, Any]:
    accounts, source = load_x_accounts_with_source()
    cfg = load_x_fallback_config()
    nitter_instances = [str(x).strip().rstrip("/") for x in (cfg.get("nitter_instances") or []) if str(x).strip()]
    if not nitter_instances:
        nitter_instances = ["https://nitter.net"]
    handle = (accounts[0] if accounts else "OpenAI").strip().lstrip("@")

    nitter_counter = Counter()
    for base in nitter_instances[:5]:
        status, err = _probe(f"{base}/{handle}/rss", timeout=timeout)
        if status == 0:
            nitter_counter[f"error:{err or 'unknown'}"] += 1
        else:
            nitter_counter[str(status)] += 1

    rjina_status, rjina_err = _probe(f"https://r.jina.ai/http://twitter.com/{handle}", timeout=timeout)
    perplexity_status, perplexity_err = _probe("https://api.perplexity.ai/search", timeout=timeout)

    recommendations: List[str] = []
    if all(k.startswith("error:") or k in {"403", "404", "500"} for k in nitter_counter.keys()):
        recommendations.append("nitter_unhealthy_try_update_instances")
    if rjina_status in {403, 405} or rjina_status == 0:
        recommendations.append("r_jina_timeline_unreliable")
    if perplexity_status == 0:
        recommendations.append("perplexity_connectivity_issue")

    return {
        "configured_accounts": len(accounts),
        "source": source,
        "timeline_provider": cfg.get("timeline_provider"),
        "tweet_provider": cfg.get("tweet_provider"),
        "nitter_breakdown": dict(nitter_counter),
        "r_jina_status": rjina_status,
        "r_jina_error": rjina_err,
        "perplexity_status": perplexity_status,
        "perplexity_error": perplexity_err,
        "recommendations": recommendations,
    }


def check_reddit(timeout: int) -> Dict[str, Any]:
    status, err = _probe("https://www.reddit.com/r/artificial/new.json?limit=1", timeout=timeout)
    rss_status, rss_err = _probe("https://www.reddit.com/r/artificial/.rss", timeout=timeout)

    recommendations: List[str] = []
    if status in {403, 429}:
        recommendations.append("reddit_json_blocked_consider_rss_or_browser")
    if rss_status in {403, 429}:
        recommendations.append("reddit_rss_blocked_consider_browser")
    if status == 0 and rss_status == 0:
        recommendations.append("reddit_network_unreachable")

    return {
        "json_status": status,
        "json_error": err,
        "rss_status": rss_status,
        "rss_error": rss_err,
        "recommendations": recommendations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check social source health")
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--write-health", action="store_true", default=True)
    parser.add_argument("--no-write-health", action="store_false", dest="write_health")
    args = parser.parse_args()

    report = {
        "checked_at": _to_iso(datetime.now(timezone.utc)),
        "youtube": check_youtube(timeout=args.timeout),
        "x": check_x(timeout=args.timeout),
        "reddit": check_reddit(timeout=args.timeout),
        "blogs_news_counts": _load_blogs_news_counts(),
    }

    print("=== social source diagnostics ===")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.write_health:
        update_source_health("diagnostics", report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
