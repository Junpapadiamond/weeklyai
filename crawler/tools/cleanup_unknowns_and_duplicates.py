#!/usr/bin/env python3
"""
Cleanup products_featured.json
1) Remove products with empty website (keep "unknown" to allow manual verification)
2) Deduplicate by website domain
3) Deduplicate by normalized name
"""

import argparse
import json
import os
import re
from urllib.parse import urlparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
FEATURED_FILE = os.path.join(DATA_DIR, "products_featured.json")

UNKNOWN_VALUES = {"unknown", "n/a", "na", "none", ""}


def normalize_name(name: str) -> str:
    # Keep ASCII alphanumerics and CJK ideographs so CN products can dedupe by name too.
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", (name or "").lower())


def normalize_domain(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")) and "." in url:
        url = f"https://{url}"
    try:
        parsed = urlparse(url)
    except Exception:
        return url.lower()
    host = (parsed.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host or url.lower()


def product_quality(p: dict) -> int:
    score = 0
    score += int(p.get("dark_horse_index") or 0) * 10
    if p.get("logo_url"):
        score += 3
    if p.get("why_matters"):
        score += 2
    funding = str(p.get("funding_total") or "").lower()
    if funding and funding not in UNKNOWN_VALUES:
        score += 1
    if p.get("source_url"):
        score += 1
    if p.get("description"):
        score += 1
    return score


def is_unknown_website(value: str) -> bool:
    return str(value or "").strip().lower() in UNKNOWN_VALUES


def main() -> int:
    parser = argparse.ArgumentParser(description="Cleanup unknown websites and duplicates")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    args = parser.parse_args()

    if not os.path.exists(FEATURED_FILE):
        print(f"Missing {FEATURED_FILE}")
        return 1

    with open(FEATURED_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)

    removed_empty = []
    filtered = []
    for p in items:
        website_raw = str(p.get("website") or "").strip()
        if not website_raw:
            removed_empty.append(p)
            continue
        # Keep "unknown" websites; they are allowed but should not participate in domain de-dupe.
        filtered.append(p)

    by_domain = {}
    unknown_websites = []
    removed_domain_dupes = []
    for p in filtered:
        if is_unknown_website(p.get("website")):
            unknown_websites.append(p)
            continue

        domain = normalize_domain(p.get("website", ""))
        # If we can't extract a meaningful domain, keep the item but skip domain-based de-dupe.
        if not domain or domain in UNKNOWN_VALUES:
            unknown_websites.append(p)
            continue
        if domain not in by_domain:
            by_domain[domain] = p
        else:
            if product_quality(p) > product_quality(by_domain[domain]):
                removed_domain_dupes.append(by_domain[domain])
                by_domain[domain] = p
            else:
                removed_domain_dupes.append(p)

    by_name = {}
    removed_name_dupes = []
    for p in list(by_domain.values()) + unknown_websites:
        name_key = normalize_name(p.get("name", ""))
        if not name_key:
            by_name[id(p)] = p
            continue
        if name_key not in by_name:
            by_name[name_key] = p
        else:
            if product_quality(p) > product_quality(by_name[name_key]):
                removed_name_dupes.append(by_name[name_key])
                by_name[name_key] = p
            else:
                removed_name_dupes.append(p)

    final = list(by_name.values())

    print(f"original {len(items)}")
    print(f"removed_empty_website {len(removed_empty)}")
    print(f"removed_duplicate_by_domain {len(removed_domain_dupes)}")
    print(f"removed_duplicate_by_name {len(removed_name_dupes)}")
    print(f"final {len(final)}")

    if args.dry_run:
        return 0

    with open(FEATURED_FILE, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    print(f"Saved {FEATURED_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
