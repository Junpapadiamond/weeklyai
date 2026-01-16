#!/usr/bin/env python3
"""
Logo Enhancement Tool for WeeklyAI

Fetches high-quality logos for products and blogs using:
1. Clearbit Logo API (high-res company logos)
2. Google Favicon API (better quality than direct favicon.ico)
3. Open Graph image extraction (fallback)

Usage:
    python enhance_logos.py                    # Update all files
    python enhance_logos.py --products-only    # Only products_featured.json
    python enhance_logos.py --blogs-only       # Only blogs_news.json
    python enhance_logos.py --dry-run          # Preview changes without saving
"""

import json
import os
import sys
import argparse
import hashlib
from urllib.parse import urlparse
from typing import Optional, Dict, Any, List
import time

# Optional dependencies
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Data file paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products_featured.json')
BLOGS_FILE = os.path.join(DATA_DIR, 'blogs_news.json')
LOGO_CACHE_FILE = os.path.join(DATA_DIR, 'logo_cache.json')

# Known bad logo patterns (generic favicons)
BAD_LOGO_PATTERNS = [
    'github.githubassets.com/favicons',
    'huggingface.co/front/assets',
    'favicon.ico',  # Generic favicon.ico (often low quality)
]

# Domain-specific logo overrides (known high-quality logos)
LOGO_OVERRIDES = {
    'openai.com': 'https://cdn.oaistatic.com/assets/apple-touch-icon-180x180-mwd5d8qb.png',
    'anthropic.com': 'https://www.anthropic.com/images/icons/apple-touch-icon.png',
    'google.com': 'https://www.google.com/images/branding/googleg/1x/googleg_standard_color_128dp.png',
    'microsoft.com': 'https://img-prod-cms-rt-microsoft-com.akamaized.net/cms/api/am/imageFileData/RE1Mu3b',
    'meta.com': 'https://static.xx.fbcdn.net/rsrc.php/y1/r/4lCu2zih0ca.svg',
    'nvidia.com': 'https://www.nvidia.com/favicon.ico',
    'huggingface.co': 'https://huggingface.co/front/assets/huggingface_logo-noborder.svg',
    'github.com': 'https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png',
}


def get_domain(url: str) -> Optional[str]:
    """Extract domain from URL."""
    if not url:
        return None
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        parsed = urlparse(url)
        return parsed.netloc.lower().replace('www.', '')
    except Exception:
        return None


def is_bad_logo(logo_url: str) -> bool:
    """Check if logo URL is a known bad/generic favicon."""
    if not logo_url:
        return True
    logo_lower = logo_url.lower()
    return any(pattern in logo_lower for pattern in BAD_LOGO_PATTERNS)


def get_clearbit_logo(domain: str) -> Optional[str]:
    """Get logo from Clearbit Logo API (free, no API key needed)."""
    if not domain:
        return None
    return f"https://logo.clearbit.com/{domain}"


def get_google_favicon(domain: str, size: int = 128) -> Optional[str]:
    """Get favicon from Google's favicon service (better quality)."""
    if not domain:
        return None
    return f"https://www.google.com/s2/favicons?domain={domain}&sz={size}"


def verify_logo_url(url: str, timeout: int = 5) -> bool:
    """Verify that a logo URL is accessible and returns an image."""
    if not HAS_REQUESTS or not url:
        return False
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code != 200:
            return False
        content_type = response.headers.get('content-type', '').lower()
        return any(img_type in content_type for img_type in ['image/', 'svg'])
    except Exception:
        return False


def get_best_logo(website: str, current_logo: str, cache: Dict[str, str],
                  verify: bool = True) -> str:
    """Get the best available logo for a website."""
    domain = get_domain(website)
    if not domain:
        return current_logo or ''

    # Check cache first
    cache_key = domain
    if cache_key in cache:
        return cache[cache_key]

    # Check for domain-specific overrides
    for override_domain, override_logo in LOGO_OVERRIDES.items():
        if override_domain in domain:
            cache[cache_key] = override_logo
            return override_logo

    # If current logo is good, keep it
    if current_logo and not is_bad_logo(current_logo):
        cache[cache_key] = current_logo
        return current_logo

    # Try Clearbit first (highest quality)
    clearbit_url = get_clearbit_logo(domain)
    if verify and clearbit_url:
        if verify_logo_url(clearbit_url):
            cache[cache_key] = clearbit_url
            return clearbit_url
    elif not verify and clearbit_url:
        # Without verification, prefer Clearbit for known tech domains
        tech_domains = ['ai', 'dev', 'io', 'tech', 'app', 'cloud']
        if any(td in domain for td in tech_domains):
            cache[cache_key] = clearbit_url
            return clearbit_url

    # Fall back to Google Favicon (always works)
    google_url = get_google_favicon(domain)
    cache[cache_key] = google_url
    return google_url


def load_cache() -> Dict[str, str]:
    """Load logo cache from file."""
    if os.path.exists(LOGO_CACHE_FILE):
        try:
            with open(LOGO_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_cache(cache: Dict[str, str]):
    """Save logo cache to file."""
    try:
        with open(LOGO_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not save cache: {e}")


def enhance_logos(items: List[Dict[str, Any]], cache: Dict[str, str],
                  verify: bool = True, verbose: bool = True) -> tuple:
    """Enhance logos for a list of items."""
    updated = 0
    skipped = 0

    for item in items:
        name = item.get('name', 'Unknown')
        website = item.get('website', '')
        current_logo = item.get('logo_url', '')

        if not website:
            skipped += 1
            continue

        new_logo = get_best_logo(website, current_logo, cache, verify=verify)

        if new_logo != current_logo:
            if verbose:
                print(f"  ✓ {name}: {current_logo[:50]}... -> {new_logo[:50]}...")
            item['logo_url'] = new_logo
            updated += 1
        else:
            skipped += 1

        # Rate limiting to be nice to APIs
        if verify:
            time.sleep(0.1)

    return updated, skipped


def main():
    parser = argparse.ArgumentParser(description='Enhance logos for WeeklyAI data files')
    parser.add_argument('--products-only', action='store_true', help='Only update products')
    parser.add_argument('--blogs-only', action='store_true', help='Only update blogs')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without saving')
    parser.add_argument('--no-verify', action='store_true', help='Skip URL verification (faster)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show all changes')
    args = parser.parse_args()

    if not HAS_REQUESTS:
        print("Warning: 'requests' library not installed. URL verification disabled.")
        print("Install with: pip install requests")
        args.no_verify = True

    # Load cache
    cache = load_cache()
    print(f"Loaded {len(cache)} cached logo mappings")

    total_updated = 0
    total_skipped = 0

    # Process products
    if not args.blogs_only:
        if os.path.exists(PRODUCTS_FILE):
            print(f"\n📦 Processing products_featured.json...")
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                products = json.load(f)

            updated, skipped = enhance_logos(
                products, cache,
                verify=not args.no_verify,
                verbose=args.verbose
            )
            total_updated += updated
            total_skipped += skipped

            print(f"  Products: {updated} updated, {skipped} unchanged")

            if not args.dry_run and updated > 0:
                with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(products, f, indent=2, ensure_ascii=False)
                print(f"  ✓ Saved {PRODUCTS_FILE}")
        else:
            print(f"Warning: {PRODUCTS_FILE} not found")

    # Process blogs
    if not args.products_only:
        if os.path.exists(BLOGS_FILE):
            print(f"\n📰 Processing blogs_news.json...")
            with open(BLOGS_FILE, 'r', encoding='utf-8') as f:
                blogs = json.load(f)

            updated, skipped = enhance_logos(
                blogs, cache,
                verify=not args.no_verify,
                verbose=args.verbose
            )
            total_updated += updated
            total_skipped += skipped

            print(f"  Blogs: {updated} updated, {skipped} unchanged")

            if not args.dry_run and updated > 0:
                with open(BLOGS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(blogs, f, indent=2, ensure_ascii=False)
                print(f"  ✓ Saved {BLOGS_FILE}")
        else:
            print(f"Warning: {BLOGS_FILE} not found")

    # Save cache
    if not args.dry_run:
        save_cache(cache)
        print(f"\n✓ Saved {len(cache)} logo mappings to cache")

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Summary: {total_updated} logos updated, {total_skipped} unchanged")


if __name__ == '__main__':
    main()
