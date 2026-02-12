#!/usr/bin/env python3
"""
Run China-native news collection only.

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
from typing import Any, Dict, List


TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
CRAWLER_DIR = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, CRAWLER_DIR)

from spiders.cn_news_spider import CNNewsSpider  # noqa: E402


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


def _save_last_updated(output_dir: str) -> str:
    last_updated_file = os.path.join(output_dir, "last_updated.json")
    payload = {
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    }
    with open(last_updated_file, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    return last_updated_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect CN-native RSS news into blogs_news.json")
    parser.add_argument("--dry-run", action="store_true", help="Print summary only; do not write files")
    args = parser.parse_args()

    try:
        allowed_year = int(os.getenv("CONTENT_YEAR", str(datetime.now(timezone.utc).year)))
    except Exception:
        allowed_year = datetime.now(timezone.utc).year

    spider = CNNewsSpider()
    items = spider.crawl()
    blogs: List[Dict[str, Any]] = []

    for raw in items:
        item = _to_serializable(raw)
        item["content_type"] = "blog"
        if _item_year_ok(item, allowed_year):
            blogs.append(item)

    blogs.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    output_dir = os.path.join(CRAWLER_DIR, "data")
    blogs_file = os.path.join(output_dir, "blogs_news.json")

    print("\n📦 CN news-only result")
    print(f"  • total collected: {len(items)}")
    print(f"  • kept ({allowed_year}): {len(blogs)}")
    print(f"  • output file: {blogs_file}")

    if args.dry_run:
        print("  • dry_run=true, no files written")
        return 0

    os.makedirs(output_dir, exist_ok=True)
    with open(blogs_file, "w", encoding="utf-8") as fh:
        json.dump(blogs, fh, ensure_ascii=False, indent=2)
    last_updated_file = _save_last_updated(output_dir)

    print(f"✓ 新闻/讨论: {len(blogs)} 条 → blogs_news.json")
    print(f"✓ 已更新 {last_updated_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
