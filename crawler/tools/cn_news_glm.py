#!/usr/bin/env python3
"""
Collect CN blog/news signals through GLM web search and merge into blogs_news.json.

Output:
- crawler/data/blogs_news.json
- crawler/data/last_updated.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
CRAWLER_DIR = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, CRAWLER_DIR)

from tools.cn_news_only import (  # noqa: E402
    _dedupe,
    _item_year_ok,
    _load_existing_blogs,
    _parse_dt,
    _save_last_updated,
    _split_by_market,
    _with_market_meta,
    count_market,
)
from utils.glm_client import glm_search, is_glm_available  # noqa: E402


CN_GLM_SOURCE = "cn_news_glm"
DEFAULT_CN_GLM_QUERIES = [
    "中国 AI 创业 公司 融资 发布 最新 动态",
    "中国 大模型 智能体 产品 发布 上线",
    "中国 AI 芯片 机器人 公司 新进展",
    "国产 AI 工具 Agent 平台 近期新闻",
]


def _parse_any_datetime(raw: str) -> Optional[datetime]:
    value = (raw or "").strip()
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        pass

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


def _to_iso(dt: Optional[datetime]) -> str:
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_result_to_blog(result: Dict[str, Any], query: str) -> Optional[Dict[str, Any]]:
    title = str(result.get("title") or "").strip()
    url = str(result.get("url") or result.get("link") or "").strip()
    snippet = str(result.get("content") or result.get("snippet") or "").strip()
    source_hint = str(result.get("source") or "zhipu_web_search").strip()
    raw_date = str(result.get("date") or result.get("publish_date") or "").strip()

    if not title or not url:
        return None

    parsed_date = _parse_any_datetime(raw_date)
    item = {
        "name": title[:160],
        "description": (snippet or title)[:300],
        "logo_url": "",
        "website": url,
        "categories": ["other"],
        "weekly_users": 0,
        "trending_score": 74,
        "rating": 3.9,
        "source": CN_GLM_SOURCE,
        "published_at": _to_iso(parsed_date),
        "extra": {
            "source_type": "glm_web_search",
            "news_market": "cn",
            "glm_query": query,
            "glm_source_hint": source_hint,
            "glm_raw_date": raw_date,
        },
    }
    return _with_market_meta(item)


def _collect_glm_cn_blogs(
    queries: List[str],
    *,
    limit_per_query: int,
    allowed_year: int,
) -> Tuple[List[Dict[str, Any]], int]:
    total_raw_results = 0
    collected: List[Dict[str, Any]] = []

    for query in queries:
        query = (query or "").strip()
        if not query:
            continue
        raw_results = glm_search(query, max_results=limit_per_query, region="cn")
        total_raw_results += len(raw_results)
        for raw in raw_results:
            if not isinstance(raw, dict):
                continue
            item = _normalize_result_to_blog(raw, query)
            if item and _item_year_ok(item, allowed_year):
                collected.append(item)

    collected = _dedupe(collected)
    collected.sort(key=lambda x: _parse_dt(str(x.get("published_at") or "")).timestamp(), reverse=True)
    return collected, total_raw_results


def _merge_glm_cn_slice(
    existing_blogs: List[Dict[str, Any]],
    fresh_glm_cn_blogs: List[Dict[str, Any]],
    *,
    allowed_year: int,
) -> Tuple[List[Dict[str, Any]], str]:
    existing_cn, existing_non_cn = _split_by_market(existing_blogs)
    existing_cn_non_glm = [
        item for item in existing_cn if str(item.get("source") or "").strip().lower() != CN_GLM_SOURCE
    ]

    if fresh_glm_cn_blogs:
        selected_cn = existing_cn_non_glm + fresh_glm_cn_blogs
        strategy = "replace_glm_slice"
    else:
        selected_cn = existing_cn
        strategy = "keep_existing_cn"

    merged = existing_non_cn + selected_cn
    merged = [_with_market_meta(item) for item in merged if _item_year_ok(item, allowed_year)]
    merged = _dedupe(merged)
    merged.sort(key=lambda x: _parse_dt(str(x.get("published_at") or "")).timestamp(), reverse=True)
    return merged, strategy


def _load_queries(path: str) -> List[str]:
    query_path = (path or "").strip()
    if not query_path:
        return DEFAULT_CN_GLM_QUERIES
    if not os.path.exists(query_path):
        return DEFAULT_CN_GLM_QUERIES

    try:
        with open(query_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception:
        return DEFAULT_CN_GLM_QUERIES

    if isinstance(payload, list):
        return [str(item).strip() for item in payload if str(item).strip()]
    return DEFAULT_CN_GLM_QUERIES


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect CN news/blog through GLM and merge into blogs_news.json")
    parser.add_argument("--dry-run", action="store_true", help="Print summary only; do not write files")
    parser.add_argument("--limit-per-query", type=int, default=8, help="Max GLM search results per query")
    parser.add_argument(
        "--queries-file",
        type=str,
        default="",
        help="Optional JSON file containing query list, fallback to built-in queries",
    )
    args = parser.parse_args()

    if not is_glm_available():
        print("❌ GLM is not available (missing ZHIPU_API_KEY or USE_GLM_FOR_CN=false)")
        return 1

    try:
        allowed_year = int(os.getenv("CONTENT_YEAR", str(datetime.now(timezone.utc).year)))
    except Exception:
        allowed_year = datetime.now(timezone.utc).year

    queries = _load_queries(args.queries_file)
    output_dir = os.path.join(CRAWLER_DIR, "data")
    blogs_file = os.path.join(output_dir, "blogs_news.json")
    existing = _load_existing_blogs(blogs_file)

    fresh_glm, total_raw = _collect_glm_cn_blogs(
        queries,
        limit_per_query=max(1, min(args.limit_per_query, 20)),
        allowed_year=allowed_year,
    )
    merged, strategy = _merge_glm_cn_slice(existing, fresh_glm, allowed_year=allowed_year)

    print("\n📦 CN GLM news merge result")
    print(f"  • queries: {len(queries)}")
    print(f"  • raw search hits: {total_raw}")
    print(f"  • fresh glm cn kept ({allowed_year}): {len(fresh_glm)}")
    print(
        f"  • existing total: {len(existing)} "
        f"(cn={count_market(existing, 'cn')}, us={count_market(existing, 'us')}, global={count_market(existing, 'global')})"
    )
    print(
        f"  • merged total: {len(merged)} "
        f"(cn={count_market(merged, 'cn')}, us={count_market(merged, 'us')}, global={count_market(merged, 'global')})"
    )
    print(f"  • cn strategy: {strategy}")
    print(f"  • output file: {blogs_file}")

    if args.dry_run:
        print("  • dry_run=true, no files written")
        return 0

    os.makedirs(output_dir, exist_ok=True)
    with open(blogs_file, "w", encoding="utf-8") as fh:
        json.dump(merged, fh, ensure_ascii=False, indent=2)
    last_updated_file = _save_last_updated(output_dir)
    print(f"✓ 新闻/讨论: {len(merged)} 条 → blogs_news.json")
    print(f"✓ 已更新 {last_updated_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
