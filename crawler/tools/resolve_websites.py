#!/usr/bin/env python3
"""
Resolve missing/unknown websites from source_url pages.

Usage:
  python tools/resolve_websites.py
  python tools/resolve_websites.py --dry-run
  python tools/resolve_websites.py --input data/products_featured.json --limit 50
  python tools/resolve_websites.py --aggressive
"""

import argparse
import json
import os
from typing import List, Dict

import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils.website_resolver import extract_official_website_from_source, is_placeholder_url

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DEFAULT_INPUT = os.path.join(DATA_DIR, "products_featured.json")


def load_json(path: str) -> List[Dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def save_json(path: str, payload: List[Dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def needs_resolution(product: Dict) -> bool:
    website = (product.get("website") or "").strip().lower()
    if not website:
        return True
    if website in {"unknown", "n/a", "na", "none"}:
        return True
    if is_placeholder_url(website):
        return True
    return False


def resolve_products(products: List[Dict], limit: int = 0, dry_run: bool = False, aggressive: bool = False) -> int:
    updated = 0
    processed = 0

    for product in products:
        if limit and processed >= limit:
            break
        if not needs_resolution(product):
            continue

        source_url = product.get("source_url", "")
        name = product.get("name", "")
        if not source_url or not name:
            continue

        processed += 1
        resolved = extract_official_website_from_source(source_url, name, aggressive=aggressive)
        if not resolved:
            continue

        updated += 1
        if dry_run:
            print(f"[DRY RUN] {name}: {product.get('website', '')} -> {resolved}")
        else:
            product["website"] = resolved
            product["website_source"] = "source_url"
            product.pop("needs_verification", None)

    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve missing websites from source_url")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Input JSON file")
    parser.add_argument("--output", default="", help="Output JSON file (default: overwrite input)")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without saving")
    parser.add_argument("--limit", type=int, default=0, help="Max products to process")
    parser.add_argument("--aggressive", action="store_true", help="Lower threshold for matching official websites")
    args = parser.parse_args()

    products = load_json(args.input)
    if not products:
        print(f"No products found in {args.input}")
        return 0

    updated = resolve_products(products, limit=args.limit, dry_run=args.dry_run, aggressive=args.aggressive)
    print(f"{'[DRY RUN] ' if args.dry_run else ''}Resolved websites: {updated}")

    if not args.dry_run and updated:
        output_path = args.output or args.input
        save_json(output_path, products)
        print(f"Saved {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
