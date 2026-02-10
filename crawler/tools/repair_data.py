#!/usr/bin/env python3
"""
One-time data repair script for products_featured.json.

Fixes:
1. Empty criteria_met on scored products (backfill from existing fields)
2. Missing categories (default to ["other"])
3. Bad/missing region field (default to globe emoji)
4. Well-known products that should be excluded
5. Non-numeric funding_total (normalize to raw + USD estimate)

Usage:
    python tools/repair_data.py --dry-run     # Preview changes
    python tools/repair_data.py               # Apply fixes in-place
"""

import json
import os
import re
import sys
import argparse
from copy import deepcopy
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

FEATURED_FILE = os.path.join(PROJECT_ROOT, "data", "products_featured.json")

# Well-known products that shouldn't appear as dark horses.
# Mirrors auto_discover.py WELL_KNOWN_PRODUCTS.
WELL_KNOWN_PRODUCTS = {
    "chatgpt", "openai", "claude", "anthropic", "gemini", "bard",
    "copilot", "github copilot", "dall-e", "dall-e 3", "sora",
    "midjourney", "stable diffusion", "stability ai",
    "cursor", "perplexity", "elevenlabs", "eleven labs",
    "synthesia", "runway", "runway ml", "pika", "pika labs",
    "bolt.new", "bolt", "v0.dev", "v0", "replit", "together ai", "groq",
    "character.ai", "character ai", "jasper", "jasper ai",
    "notion ai", "grammarly", "copy.ai", "writesonic",
    "huggingface", "hugging face", "langchain", "llamaindex",
    "kimi", "moonshot", "doubao", "qwen", "wenxin", "ernie",
}


def _infer_criteria(product: dict) -> list[str]:
    """Infer criteria_met from existing product fields."""
    criteria = []

    funding = product.get("funding_total") or ""
    if funding and funding.lower() not in ("unknown", "n/a", ""):
        criteria.append("funding_signal")

    why = product.get("why_matters") or ""
    if any(kw in why for kw in [
        "YC", "a16z", "Sequoia", "Benchmark", "Andreessen",
        "前OpenAI", "前Google", "前Meta", "ex-Google", "ex-OpenAI",
    ]):
        criteria.append("notable_team_or_investors")

    users = product.get("weekly_users") or 0
    try:
        users = int(users)
    except (ValueError, TypeError):
        users = 0
    if users >= 50000:
        criteria.append("rapid_growth")

    desc = (product.get("description") or "") + " " + why
    if any(kw in desc for kw in ["首创", "首个", "first", "breakthrough", "novel"]):
        criteria.append("technical_innovation")

    if product.get("is_hardware"):
        criteria.append("hardware_differentiation")

    score = product.get("dark_horse_index") or 0
    try:
        score = int(float(str(score)))
    except (ValueError, TypeError):
        score = 0
    if score >= 4 and not criteria:
        criteria.append("high_score_inferred")

    return criteria


def _is_well_known(name: str) -> bool:
    """Check if product name matches a well-known product."""
    name_lower = name.lower().strip()
    if name_lower in WELL_KNOWN_PRODUCTS:
        return True
    for known in WELL_KNOWN_PRODUCTS:
        if known in name_lower or name_lower in known:
            return True
    return False


def _parse_funding_usd(raw: str) -> float:
    """Best-effort parse of funding string into USD float. Returns 0 on failure."""
    if not raw or not isinstance(raw, str):
        return 0
    raw = raw.strip()

    # Remove common prefixes/suffixes
    cleaned = re.sub(r"[^\d.MBKmkb$€¥万亿]", " ", raw)
    # Try patterns like "$35M", "35M", "3500万"
    m = re.search(r"[\$]?\s*([\d.]+)\s*(B|billion|M|million|K|thousand|万|亿)", raw, re.IGNORECASE)
    if not m:
        return 0

    num = float(m.group(1))
    unit = m.group(2).lower()

    multipliers = {
        "b": 1e9, "billion": 1e9,
        "m": 1e6, "million": 1e6,
        "k": 1e3, "thousand": 1e3,
        "万": 1e4, "亿": 1e8,
    }
    return num * multipliers.get(unit, 1)


def repair(products: list[dict], dry_run: bool = False) -> dict:
    """Apply all repairs and return stats."""
    stats = {
        "criteria_backfilled": 0,
        "categories_fixed": 0,
        "regions_fixed": 0,
        "well_known_removed": 0,
        "funding_normalized": 0,
        "total": len(products),
    }

    to_remove = []

    for i, product in enumerate(products):
        name = product.get("name", "")

        # --- 1. Remove well-known products ---
        if _is_well_known(name):
            to_remove.append(i)
            stats["well_known_removed"] += 1
            continue

        # --- 2. Backfill empty criteria_met ---
        criteria = product.get("criteria_met")
        if not criteria or not isinstance(criteria, list) or len(criteria) == 0:
            score = 0
            try:
                score = int(float(str(product.get("dark_horse_index", 0))))
            except (ValueError, TypeError):
                pass
            if score >= 4:
                inferred = _infer_criteria(product)
                if inferred:
                    product["criteria_met"] = inferred
                    stats["criteria_backfilled"] += 1

        # --- 3. Fix missing categories ---
        cats = product.get("categories")
        if not cats or not isinstance(cats, list) or len(cats) == 0:
            product["categories"] = ["other"]
            stats["categories_fixed"] += 1

        # --- 4. Fix bad/missing region ---
        region = product.get("region")
        if not region or not isinstance(region, str) or not region.strip():
            product["region"] = "\U0001f30d"  # 🌍
            stats["regions_fixed"] += 1

        # --- 5. Normalize funding_total ---
        funding_raw = product.get("funding_total")
        if funding_raw and isinstance(funding_raw, str):
            usd = _parse_funding_usd(funding_raw)
            if usd > 0 and "funding_total_usd" not in product:
                product["funding_total_usd"] = usd
                product["funding_total_raw"] = funding_raw
                stats["funding_normalized"] += 1

    # Remove well-known products (in reverse to preserve indices)
    for i in reversed(to_remove):
        products.pop(i)

    return stats


def main():
    parser = argparse.ArgumentParser(description="Repair products_featured.json data quality")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--input", default=FEATURED_FILE, help="Input file path")
    args = parser.parse_args()

    filepath = args.input
    print(f"\n  Data Repair Tool")
    print(f"  {'=' * 40}")
    print(f"  Input: {filepath}")

    if not os.path.exists(filepath):
        print(f"  ERROR: File not found: {filepath}")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        products = json.load(f)

    print(f"  Products loaded: {len(products)}")

    # Make a deep copy for dry-run comparison
    original_count = len(products)
    stats = repair(products, dry_run=args.dry_run)

    print(f"\n  Repair Results:")
    print(f"    criteria_met backfilled:  {stats['criteria_backfilled']}")
    print(f"    categories fixed:         {stats['categories_fixed']}")
    print(f"    regions fixed:            {stats['regions_fixed']}")
    print(f"    well-known removed:       {stats['well_known_removed']}")
    print(f"    funding normalized:       {stats['funding_normalized']}")
    print(f"    products before:          {original_count}")
    print(f"    products after:           {len(products)}")

    if args.dry_run:
        print(f"\n  [DRY RUN] No changes written.")
    else:
        # Write back with backup
        backup_path = filepath + f".bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(filepath, "r", encoding="utf-8") as f:
            original_data = f.read()
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(original_data)
        print(f"\n  Backup saved to: {backup_path}")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"  Repaired data written to: {filepath}")

    print()


if __name__ == "__main__":
    main()
