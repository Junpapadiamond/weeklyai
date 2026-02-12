#!/usr/bin/env python3
"""
Prune curated weekly dark horses.

Why:
- Some providers (especially GLM) may output "headline-like" items (e.g. investment/news titles)
  that are not actual product/company names. These can slip into dark_horses files.

What it does:
- For hardware items in the weekly dark_horses file:
  - Run validate_hardware_product (local rule-based, no LLM calls).
  - Drop items that fail validation.
  - Drop items that are downgraded below dark_horse_index < 4 after validation.
- Writes back to:
  - crawler/data/dark_horses/week_<YYYY_WW>.json
  - backend/data/dark_horses/week_<YYYY_WW>.json (if present)

Usage:
  python tools/prune_dark_horses.py
  python tools/prune_dark_horses.py --week 2026_07
  python tools/prune_dark_horses.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Tuple


TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
CRAWLER_DIR = os.path.dirname(TOOLS_DIR)
REPO_ROOT = os.path.dirname(CRAWLER_DIR)

sys.path.insert(0, CRAWLER_DIR)

from prompts.analysis_prompts import validate_hardware_product  # noqa: E402


def _current_week() -> str:
    now = datetime.now()
    return f"{now.year}_{now.isocalendar()[1]:02d}"


def _load_list(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except Exception:
        return []
    return []


def _save_list(path: str, items: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def _is_hardware(item: Dict[str, Any]) -> bool:
    if item.get("category") == "hardware":
        return True
    if item.get("is_hardware") is True:
        return True
    if item.get("hardware_type") or item.get("hardware_category"):
        return True
    categories = item.get("categories")
    if isinstance(categories, list) and "hardware" in categories:
        return True
    return False


def prune(items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str]]]:
    kept: List[Dict[str, Any]] = []
    removed: List[Tuple[str, str]] = []

    for item in items:
        name = str(item.get("name") or "").strip() or "<unnamed>"

        if not _is_hardware(item):
            kept.append(item)
            continue

        ok, reason = validate_hardware_product(item)
        if not ok:
            removed.append((name, reason))
            continue

        kept.append(item)

    return kept, removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune weekly dark horses (hardware sanity filter)")
    parser.add_argument("--week", default="", help="Week string like 2026_07 (default: current week)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without saving files")
    args = parser.parse_args()

    week = (args.week or "").strip() or _current_week()

    crawler_file = os.path.join(CRAWLER_DIR, "data", "dark_horses", f"week_{week}.json")
    backend_file = os.path.join(REPO_ROOT, "backend", "data", "dark_horses", f"week_{week}.json")

    items = _load_list(crawler_file)
    if not items:
        print(f"ℹ️ No dark horses file found or empty: {crawler_file}")
        return 0

    kept, removed = prune(items)

    print("\n🧹 Prune weekly dark horses")
    print(f"  • week: {week}")
    print(f"  • input: {crawler_file}")
    print(f"  • total: {len(items)}")
    print(f"  • removed: {len(removed)}")
    print(f"  • kept: {len(kept)}")

    for name, reason in removed[:20]:
        print(f"    - {name} ({reason})")
    if len(removed) > 20:
        print(f"    … and {len(removed) - 20} more")

    if args.dry_run:
        return 0

    if kept == items:
        print("✓ No changes.")
        return 0

    _save_list(crawler_file, kept)
    if os.path.exists(backend_file):
        _save_list(backend_file, kept)

    print("✓ Saved pruned dark horses.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
