#!/usr/bin/env python3
"""
Auto-publish weekly dark horses and rising stars into products_featured.json.

Rules:
- Merge by website domain (no overwrite)
- Append new products only
"""

import argparse
import json
import os
from datetime import datetime
from urllib.parse import urlparse

UNKNOWN_COUNTRY_CODE = "UNKNOWN"
UNKNOWN_COUNTRY_NAME = "Unknown"
UNKNOWN_COUNTRY_DISPLAY = "Unknown"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
DARK_HORSES_DIR = os.path.join(DATA_DIR, 'dark_horses')
RISING_STARS_DIR = os.path.join(DATA_DIR, 'rising_stars')
FEATURED_FILE = os.path.join(DATA_DIR, 'products_featured.json')


def get_current_week() -> str:
    now = datetime.now()
    return f"{now.year}_{now.isocalendar()[1]:02d}"


def normalize_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    parsed = urlparse(url)
    domain = (parsed.netloc or "").lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain or url.lower()


def load_json(path: str) -> list:
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_json(path: str, payload: list) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def coerce_categories(raw: dict) -> list:
    categories = raw.get('categories')
    if isinstance(categories, str):
        categories = [categories]
    if isinstance(categories, list) and categories:
        return categories
    category = raw.get('category')
    if category:
        return [category]
    return ['other']


def copy_optional_fields(source: dict, target: dict, fields: list) -> None:
    for field in fields:
        value = source.get(field)
        if value not in (None, '', [], {}):
            target[field] = value


def resolve_region(raw: dict) -> str:
    region = str(raw.get('region') or '').strip()
    if region:
        return region
    flag = str(raw.get('country_flag') or '').strip()
    if flag:
        return flag
    return UNKNOWN_COUNTRY_DISPLAY


def build_featured_product(raw: dict) -> dict:
    dark_index = raw.get('dark_horse_index', 2)
    discovered_at = raw.get('discovered_at') or datetime.utcnow().strftime('%Y-%m-%d')
    first_seen = raw.get('first_seen') or raw.get('published_at') or f"{datetime.utcnow().isoformat()}Z"

    product = {
        'name': (raw.get('name') or '').strip(),
        'description': raw.get('description') or '',
        'website': (raw.get('website') or '').strip(),
        'logo_url': raw.get('logo_url') or raw.get('logo') or '',
        'categories': coerce_categories(raw),
        'dark_horse_index': dark_index,
        'why_matters': raw.get('why_matters') or '',
        'funding_total': raw.get('funding_total') or '',
        'region': resolve_region(raw),
        'country_code': raw.get('country_code') or UNKNOWN_COUNTRY_CODE,
        'country_name': raw.get('country_name') or UNKNOWN_COUNTRY_NAME,
        'country_flag': raw.get('country_flag') or '',
        'country_display': raw.get('country_display') or UNKNOWN_COUNTRY_DISPLAY,
        'country_source': raw.get('country_source') or 'unknown',
        'source_region': raw.get('source_region') or '',
        'source': raw.get('source') or 'auto_publish',
        'discovered_at': discovered_at,
        'first_seen': first_seen,
        'final_score': raw.get('final_score') or dark_index * 20,
        'trending_score': raw.get('trending_score') or dark_index * 18,
    }

    copy_optional_fields(raw, product, [
        'latest_news',
        'news_updated_at',
        'criteria_met',
        'hardware_category',
        'is_hardware',
        'source_url',
        'confidence',
        'discovery_method',
        'search_keyword',
        'company_country',
        'company_country_code',
        'hq_country',
        'headquarters_country',
        'community_verdict',
        'extra',
    ])

    return product


def load_weekly_sources(week: str) -> list:
    dark_file = os.path.join(DARK_HORSES_DIR, f'week_{week}.json')
    rising_file = os.path.join(RISING_STARS_DIR, f'global_{week}.json')
    dark_horses = load_json(dark_file)
    rising_stars = load_json(rising_file)
    return dark_horses + rising_stars


def merge_featured(featured: list, new_items: list) -> int:
    existing = {
        normalize_url(item.get('website', ''))
        for item in featured
        if item.get('website')
    }

    added = 0
    for raw in new_items:
        website = (raw.get('website') or '').strip()
        name = (raw.get('name') or '').strip()
        if not website or not name:
            continue
        key = normalize_url(website)
        if not key or key in existing:
            continue
        featured.append(build_featured_product(raw))
        existing.add(key)
        added += 1
    return added


def main() -> int:
    parser = argparse.ArgumentParser(description='Auto publish weekly products to products_featured.json')
    parser.add_argument('--week', default=get_current_week(), help='Week key: YYYY_WW')
    args = parser.parse_args()

    weekly_products = load_weekly_sources(args.week)
    if not weekly_products:
        print(f"No weekly products found for {args.week}")
        return 0

    featured = load_json(FEATURED_FILE)
    added = merge_featured(featured, weekly_products)
    if added:
        save_json(FEATURED_FILE, featured)
    print(f"Added {added} new products to products_featured.json")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
