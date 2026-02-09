#!/usr/bin/env python3
"""
Verify social signal spiders (YouTube + X) without writing repo data files.

What it checks:
- Schema: required fields exist and URLs are http(s)
- Freshness: published_at within SOCIAL_HOURS window (best-effort)
- Classification: data_classifier.classify_product(source=youtube/x) must be 'blog'
- Evidence: required extra fields exist

Optional:
- Write a small subset JSON to /tmp for rss_to_products --dry-run.

Usage:
  /usr/bin/python3 crawler/tools/verify_social_signals.py
  SOCIAL_HOURS=96 /usr/bin/python3 crawler/tools/verify_social_signals.py --write-subset /tmp/social_subset.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple


def _ensure_import_paths() -> None:
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    crawler_root = os.path.join(repo_root, "crawler")
    # Allow imports like `from spiders...` and `from tools...` (matches crawler/main.py behavior)
    if crawler_root not in sys.path:
        sys.path.insert(0, crawler_root)


def _print_dependency_hint(repo_root: str, missing_module: str) -> None:
    req_file = os.path.join(repo_root, "crawler", "requirements.txt")
    print(f"❌ Missing dependency: {missing_module}")
    print(f"Install with: /usr/bin/python3 -m pip install -r {req_file}")
    print("Run verifier with: /usr/bin/python3 crawler/tools/verify_social_signals.py")


def _load_env_files(repo_root: str) -> bool:
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        _print_dependency_hint(repo_root, "python-dotenv")
        return False

    load_dotenv(os.path.join(repo_root, ".env"))
    load_dotenv(os.path.join(repo_root, "crawler", ".env"))
    return True


def _to_dt(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def _is_http_url(value: str) -> bool:
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def _get_published_at(item: Dict[str, Any]) -> str:
    direct = (item.get("published_at") or "").strip()
    if direct:
        return direct
    extra = item.get("extra") or {}
    if isinstance(extra, dict):
        return str(extra.get("published_at") or "").strip()
    return ""


def validate_items(
    items: List[Dict[str, Any]],
    source: str,
    *,
    hours: int,
    year: int,
) -> Tuple[List[str], Dict[str, int]]:
    errors: List[str] = []
    stats = defaultdict(int)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    for idx, item in enumerate(items):
        prefix = f"{source}[{idx}]"
        stats["total"] += 1

        if (item.get("source") or "").lower() != source:
            errors.append(f"{prefix}: source mismatch")
            stats["bad_source"] += 1

        name = (item.get("name") or "").strip()
        if not name:
            errors.append(f"{prefix}: missing name")
            stats["missing_name"] += 1

        website = (item.get("website") or "").strip()
        if not _is_http_url(website):
            errors.append(f"{prefix}: invalid website")
            stats["invalid_website"] += 1

        description = (item.get("description") or "").strip()
        if len(description) < 20:
            errors.append(f"{prefix}: description too short ({len(description)})")
            stats["short_description"] += 1

        published_at = _get_published_at(item)
        if not published_at:
            errors.append(f"{prefix}: missing published_at")
            stats["missing_published_at"] += 1
        else:
            parsed = _to_dt(published_at)
            if parsed and parsed < cutoff:
                errors.append(f"{prefix}: stale published_at ({published_at})")
                stats["stale_published_at"] += 1
            if parsed and parsed.year != year:
                errors.append(f"{prefix}: wrong year ({parsed.year} != {year})")
                stats["wrong_year"] += 1

        extra = item.get("extra") or {}
        if not isinstance(extra, dict):
            errors.append(f"{prefix}: extra not dict")
            stats["bad_extra"] += 1
        else:
            if source == "youtube":
                if not extra.get("channel"):
                    errors.append(f"{prefix}: missing extra.channel")
                    stats["missing_channel"] += 1
                if not extra.get("video_id"):
                    errors.append(f"{prefix}: missing extra.video_id")
                    stats["missing_video_id"] += 1
            if source == "x":
                if not extra.get("query"):
                    errors.append(f"{prefix}: missing extra.query")
                    stats["missing_query"] += 1
                if not extra.get("tweet_id"):
                    # Not hard-fail but helpful for evidence UI.
                    stats["missing_tweet_id"] += 1

    return errors, dict(stats)


def sample(items: List[Dict[str, Any]], n: int = 3) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for item in items[:n]:
        extra = item.get("extra") if isinstance(item.get("extra"), dict) else {}
        out.append(
            {
                "title": (item.get("name") or "")[:120],
                "url": item.get("website"),
                "published_at": _get_published_at(item),
                "extra": {
                    "channel": (extra or {}).get("channel"),
                    "video_id": (extra or {}).get("video_id"),
                    "author_handle": (extra or {}).get("author_handle"),
                    "tweet_id": (extra or {}).get("tweet_id"),
                    "query": (extra or {}).get("query"),
                },
            }
        )
    return out


def main() -> int:
    _ensure_import_paths()

    parser = argparse.ArgumentParser(description="Verify YouTube/X social signal spiders")
    parser.add_argument("--hours", type=int, default=int(os.getenv("SOCIAL_HOURS", "96")), help="Freshness window hours")
    parser.add_argument("--year", type=int, default=int(os.getenv("CONTENT_YEAR", str(datetime.now(timezone.utc).year))), help="Allowed content year")
    parser.add_argument("--limit", type=int, default=60, help="Max items per source")
    parser.add_argument("--write-subset", type=str, default="", help="Write a small subset JSON (for rss_to_products)")
    parser.add_argument("--subset-size", type=int, default=8, help="Items per source for subset file")
    args = parser.parse_args()

    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if not _load_env_files(repo_root):
        return 2

    # Keep spider behavior aligned with explicit verifier arguments.
    os.environ["SOCIAL_HOURS"] = str(args.hours)
    os.environ["CONTENT_YEAR"] = str(args.year)

    try:
        from spiders.youtube_spider import YouTubeSpider
        from spiders.x_spider import XSpider
        from tools.data_classifier import classify_product
    except ModuleNotFoundError as exc:
        _print_dependency_hint(repo_root, exc.name or "module")
        return 2

    youtube_items = YouTubeSpider().crawl()[: args.limit]
    x_items = XSpider().crawl()[: args.limit]

    print("=== verify_social_signals ===")
    print(f"SOCIAL_HOURS={args.hours}  CONTENT_YEAR={args.year}  limit={args.limit}")
    print(f"youtube={len(youtube_items)}  x={len(x_items)}")
    print("sources:", dict(Counter([(i.get("source") or "").lower() for i in (youtube_items + x_items)])))

    # Classification checks
    bad_class = []
    for src, items in (("youtube", youtube_items), ("x", x_items)):
        for idx, item in enumerate(items):
            ctype = classify_product(item)
            if ctype != "blog":
                bad_class.append(f"{src}[{idx}]: classified={ctype}")
    if bad_class:
        print(f"❌ Classification issues: {len(bad_class)}")
        for e in bad_class[:20]:
            print(" -", e)
    else:
        print("✅ Classification: youtube/x → blog")

    # Schema checks
    yt_errors, yt_stats = validate_items(youtube_items, "youtube", hours=args.hours, year=args.year)
    x_errors, x_stats = validate_items(x_items, "x", hours=args.hours, year=args.year)

    if yt_errors:
        print(f"❌ YouTube schema issues: {len(yt_errors)}")
        for e in yt_errors[:20]:
            print(" -", e)
        if len(yt_errors) > 20:
            print(" ...")
    else:
        print("✅ YouTube schema OK")

    if x_errors:
        print(f"❌ X schema issues: {len(x_errors)}")
        for e in x_errors[:20]:
            print(" -", e)
        if len(x_errors) > 20:
            print(" ...")
    else:
        print("✅ X schema OK")

    print("\nStats:")
    print("  youtube:", yt_stats)
    print("  x:", x_stats)

    print("\nSamples:")
    print("  youtube:", json.dumps(sample(youtube_items, 3), ensure_ascii=False, indent=2))
    print("  x:", json.dumps(sample(x_items, 3), ensure_ascii=False, indent=2))

    if args.write_subset:
        payload = []
        payload.extend(youtube_items[: args.subset_size])
        payload.extend(x_items[: args.subset_size])
        with open(args.write_subset, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"\n✅ wrote subset: {args.write_subset} items={len(payload)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
