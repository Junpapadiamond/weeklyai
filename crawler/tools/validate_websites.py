#!/usr/bin/env python3
"""
Validate auto-resolved websites to avoid wrong URLs.

Strategy:
  - Only validate products where website_source indicates auto-resolution.
  - If domain doesn't contain any meaningful token from product name, mark as unknown.
"""

import argparse
import json
import os
import re
from urllib.parse import urlparse


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
FEATURED_FILE = os.path.join(DATA_DIR, "products_featured.json")

AUTO_SOURCES = {"source_url", "weekly_match"}


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        domain = (parsed.netloc or "").lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def _name_tokens(name: str):
    normalized = _normalize_name(name)
    return [t for t in re.findall(r"[a-z0-9]{3,}", normalized) if t]


def _should_validate(item: dict) -> bool:
    source = (item.get("website_source") or "").strip().lower()
    if source in AUTO_SOURCES:
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate auto-resolved websites")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    args = parser.parse_args()

    if not os.path.exists(FEATURED_FILE):
        print(f"Missing {FEATURED_FILE}")
        return 1

    with open(FEATURED_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)

    changed = 0
    for item in products:
        website = (item.get("website") or "").strip()
        if not website:
            continue
        if website.lower() in {"unknown", "n/a", "na", "none"}:
            continue
        if not _should_validate(item):
            continue

        domain = _extract_domain(website)
        tokens = _name_tokens(item.get("name", ""))
        if not tokens:
            continue

        if not any(token in domain for token in tokens):
            if args.dry_run:
                print(f"[DRY RUN] {item.get('name')} -> unknown (domain {domain})")
            else:
                item["website"] = "unknown"
                item["needs_verification"] = True
                item["website_source"] = ""
                if item.get("logo_url"):
                    item["logo_url"] = ""
                if item.get("logo_source"):
                    item["logo_source"] = ""
            changed += 1

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Validated products: {changed}")
    if not args.dry_run and changed:
        with open(FEATURED_FILE, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"Saved {FEATURED_FILE}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
