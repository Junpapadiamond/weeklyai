#!/usr/bin/env python3
"""
Backfill source_url (and optionally website) into products_featured.json
from weekly dark_horses / rising_stars files.

Usage:
  python tools/backfill_source_urls.py --dry-run
  python tools/backfill_source_urls.py --week 2026_05
"""

import argparse
import json
import os
import re
from typing import Dict, List


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DARK_HORSES_DIR = os.path.join(DATA_DIR, "dark_horses")
RISING_STARS_DIR = os.path.join(DATA_DIR, "rising_stars")
FEATURED_FILE = os.path.join(DATA_DIR, "products_featured.json")


def _normalize_name(name: str) -> str:
    if not name:
        return ""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _is_unknown(value: str) -> bool:
    if value is None:
        return True
    text = str(value).strip().lower()
    return text in {"", "unknown", "n/a", "na", "none"}


def _load_json(path: str) -> List[Dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def _collect_weekly_products(week: str = "") -> List[Dict]:
    weekly = []
    for folder in (DARK_HORSES_DIR, RISING_STARS_DIR):
        if not os.path.exists(folder):
            continue
        for filename in os.listdir(folder):
            if not filename.endswith(".json"):
                continue
            if week and week not in filename:
                continue
            weekly.extend(_load_json(os.path.join(folder, filename)))
    return weekly


def _score_candidate(item: Dict) -> int:
    score = 0
    if item.get("source_url"):
        score += 3
    if not _is_unknown(item.get("website")):
        score += 2
    if item.get("source_title"):
        score += 1
    return score


def build_index(weekly: List[Dict]) -> Dict[str, Dict]:
    index: Dict[str, Dict] = {}
    for item in weekly:
        key = _normalize_name(item.get("name", ""))
        if not key:
            continue
        if key not in index or _score_candidate(item) > _score_candidate(index[key]):
            index[key] = item
    return index


def backfill(featured: List[Dict], index: Dict[str, Dict], dry_run: bool = False) -> int:
    updated = 0
    for item in featured:
        key = _normalize_name(item.get("name", ""))
        if not key:
            continue
        match = index.get(key)
        if not match:
            continue

        changed = False

        if not item.get("source_url") and match.get("source_url"):
            if dry_run:
                print(f"[DRY RUN] source_url {item.get('name')}: {match.get('source_url')}")
            else:
                item["source_url"] = match.get("source_url")
                if match.get("source_title"):
                    item["source_title"] = match.get("source_title")
                changed = True

        if _is_unknown(item.get("website")) and not _is_unknown(match.get("website")):
            if dry_run:
                print(f"[DRY RUN] website {item.get('name')}: {match.get('website')}")
            else:
                item["website"] = match.get("website")
                item["website_source"] = match.get("website_source") or "weekly_match"
                changed = True

        if changed:
            updated += 1

    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill source_url into products_featured.json")
    parser.add_argument("--week", default="", help="Week key like 2026_05 (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    args = parser.parse_args()

    featured = _load_json(FEATURED_FILE)
    if not featured:
        print(f"No featured products found in {FEATURED_FILE}")
        return 0

    weekly = _collect_weekly_products(args.week)
    if not weekly:
        print("No weekly products found to backfill")
        return 0

    index = build_index(weekly)
    updated = backfill(featured, index, dry_run=args.dry_run)
    print(f"{'[DRY RUN] ' if args.dry_run else ''}Backfilled products: {updated}")

    if not args.dry_run and updated:
        with open(FEATURED_FILE, "w", encoding="utf-8") as f:
            json.dump(featured, f, ensure_ascii=False, indent=2)
        print(f"Saved {FEATURED_FILE}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
