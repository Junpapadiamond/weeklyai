#!/usr/bin/env python3
"""
Run China-native news collection and merge into blogs_news.json.

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


CN_SOURCE = "cn_news"
US_LIKE_SOURCES = {
    "hackernews",
    "reddit",
    "tech_news",
    "youtube",
    "x",
    "producthunt",
}


def _to_serializable(item: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, value in item.items():
        if callable(value) or key == "_id":
            continue
        if isinstance(value, datetime):
            out[key] = value.isoformat()
        else:
            out[key] = value
    return out


def _parse_year(value: str) -> int:
    cleaned = (value or "").strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo:
            dt = dt.astimezone(timezone.utc)
        return dt.year
    except Exception:
        return 0


def _item_year_ok(item: Dict[str, Any], allowed_year: int) -> bool:
    extra = item.get("extra") if isinstance(item.get("extra"), dict) else {}
    published = (
        item.get("published_at")
        or extra.get("published_at")
        or item.get("discovered_at")
    )
    if not published:
        return False
    return _parse_year(str(published)) == allowed_year


def _parse_dt(value: str) -> datetime:
    cleaned = (value or "").strip()
    if not cleaned:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


def _infer_market(item: Dict[str, Any]) -> str:
    extra = item.get("extra") if isinstance(item.get("extra"), dict) else {}
    explicit = str(item.get("market") or extra.get("news_market") or "").strip().lower()
    if explicit in {"cn", "us", "global", "hybrid"}:
        return "global" if explicit == "hybrid" else explicit

    source = str(item.get("source") or "").strip().lower()
    if source == CN_SOURCE:
        return "cn"
    if source in US_LIKE_SOURCES:
        return "us"

    region = str(item.get("region") or "").strip().lower()
    if "cn" in region or "中国" in region or "🇨🇳" in region:
        return "cn"
    if "us" in region or "美国" in region or "🇺🇸" in region:
        return "us"
    return "global"


def _with_market_meta(item: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(item)
    extra = out.get("extra") if isinstance(out.get("extra"), dict) else {}
    market = _infer_market(out)
    out["market"] = market
    if market == "cn":
        out["region"] = "🇨🇳"
    elif market == "us" and not out.get("region"):
        out["region"] = "🇺🇸"
    elif market == "global" and not out.get("region"):
        out["region"] = "🌍"
    extra["news_market"] = market
    out["extra"] = extra
    out["content_type"] = "blog"
    return out


def _blog_key(item: Dict[str, Any]) -> str:
    source = str(item.get("source") or "unknown").strip().lower()
    website = str(item.get("website") or "").strip().lower()
    name = str(item.get("name") or "").strip().lower()
    if website and website not in {"unknown", "n/a", "na", "none", "null"}:
        return f"{source}|w:{website}"
    return f"{source}|n:{name}"


def _load_existing_blogs(blogs_file: str) -> List[Dict[str, Any]]:
    if not os.path.exists(blogs_file):
        return []
    try:
        with open(blogs_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except Exception:
        return []
    return []


def count_market(items: List[Dict[str, Any]], market: str) -> int:
    target = (market or "").strip().lower()
    return sum(1 for item in items if _infer_market(item) == target)


def _split_by_market(items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    cn: List[Dict[str, Any]] = []
    non_cn: List[Dict[str, Any]] = []
    for item in items:
        normalized = _with_market_meta(item)
        if normalized.get("market") == "cn":
            cn.append(normalized)
        else:
            non_cn.append(normalized)
    return cn, non_cn


def _dedupe(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped: List[Dict[str, Any]] = []
    seen = set()
    for item in items:
        key = _blog_key(item)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def merge_cn_blogs(
    existing_blogs: List[Dict[str, Any]],
    fresh_cn_blogs: List[Dict[str, Any]],
    *,
    baseline_blogs: Optional[List[Dict[str, Any]]] = None,
    allowed_year: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], str]:
    existing_cn, existing_non_cn = _split_by_market(existing_blogs)
    baseline_cn: List[Dict[str, Any]] = []
    if baseline_blogs:
        baseline_cn, _ = _split_by_market(baseline_blogs)

    selected_cn = list(fresh_cn_blogs)
    strategy = "fresh"
    if not selected_cn:
        if baseline_cn:
            selected_cn = baseline_cn
            strategy = "baseline"
        else:
            selected_cn = existing_cn
            strategy = "existing"

    merged = existing_non_cn + selected_cn
    if allowed_year is not None:
        merged = [_with_market_meta(item) for item in merged if _item_year_ok(item, allowed_year)]
    else:
        merged = [_with_market_meta(item) for item in merged]

    merged = _dedupe(merged)
    merged.sort(key=lambda x: _parse_dt(str(x.get("published_at") or "")).timestamp(), reverse=True)
    return merged, strategy


def _save_last_updated(output_dir: str) -> str:
    last_updated_file = os.path.join(output_dir, "last_updated.json")
    payload = {
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    }
    with open(last_updated_file, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    return last_updated_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect CN-native RSS news and merge into blogs_news.json")
    parser.add_argument("--dry-run", action="store_true", help="Print summary only; do not write files")
    parser.add_argument(
        "--baseline-file",
        type=str,
        default="",
        help="Optional baseline blogs file used to preserve CN slice when current run has no CN results",
    )
    args = parser.parse_args()

    try:
        allowed_year = int(os.getenv("CONTENT_YEAR", str(datetime.now(timezone.utc).year)))
    except Exception:
        allowed_year = datetime.now(timezone.utc).year

    from spiders.cn_news_spider import CNNewsSpider  # noqa: E402

    spider = CNNewsSpider()
    items = spider.crawl()
    cn_blogs: List[Dict[str, Any]] = []

    for raw in items:
        item = _with_market_meta(_to_serializable(raw))
        if _item_year_ok(item, allowed_year):
            cn_blogs.append(item)

    output_dir = os.path.join(CRAWLER_DIR, "data")
    blogs_file = os.path.join(output_dir, "blogs_news.json")
    existing = _load_existing_blogs(blogs_file)
    baseline_path = (args.baseline_file or "").strip()
    baseline = _load_existing_blogs(baseline_path) if baseline_path else []
    merged, strategy = merge_cn_blogs(
        existing,
        cn_blogs,
        baseline_blogs=baseline,
        allowed_year=allowed_year,
    )

    print("\n📦 CN news merge result")
    print(f"  • total collected: {len(items)}")
    print(f"  • cn kept ({allowed_year}): {len(cn_blogs)}")
    if baseline_path:
        print(
            f"  • baseline total: {len(baseline)} "
            f"(cn={count_market(baseline, 'cn')}, us={count_market(baseline, 'us')}, global={count_market(baseline, 'global')})"
        )
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
