#!/usr/bin/env python3
"""
Interactive CLI to add curated products to products_featured.json.

Usage:
    python tools/add_product.py                     # Interactive mode
    python tools/add_product.py "ProductName"       # Pre-fill name
    python tools/add_product.py --quick "Name" "https://url" "Description"  # Quick add
"""

import json
import os
import re
import sys
import argparse
from datetime import datetime, timezone
from urllib.parse import urlparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

PRODUCTS_FILE = os.path.join(PROJECT_ROOT, 'data', 'products_featured.json')

ALLOWED_CATEGORIES = [
    'coding',
    'image',
    'video',
    'voice',
    'writing',
    'hardware',
    'finance',
    'education',
    'healthcare',
    'other',
]


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip('-') or 'unknown'


def domain_from_url(url: str) -> str:
    if not url:
        return ''
    parsed = urlparse(url)
    host = parsed.netloc or ''
    return host.replace('www.', '')


def fetch_logo_url(website: str) -> str:
    """Attempt to fetch logo from Clearbit or favicon."""
    domain = domain_from_url(website)
    if not domain:
        return ''

    # Try Clearbit Logo API first (high quality)
    clearbit_url = f"https://logo.clearbit.com/{domain}"

    # Try to verify it exists (optional)
    try:
        import urllib.request
        req = urllib.request.Request(clearbit_url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0')
        response = urllib.request.urlopen(req, timeout=3)
        if response.status == 200:
            return clearbit_url
    except Exception:
        pass

    # Fallback to favicon
    return f"https://{domain}/favicon.ico"


def prompt_required(label: str, default: str = '') -> str:
    while True:
        prompt_str = f"{label}"
        if default:
            prompt_str += f" [{default}]"
        prompt_str += ": "
        value = input(prompt_str).strip()
        if value:
            return value
        if default:
            return default
        print("  -> This field is required.")


def prompt_optional(label: str, default: str = '') -> str:
    prompt_str = f"{label}"
    if default:
        prompt_str += f" [{default}]"
    prompt_str += ": "
    value = input(prompt_str).strip()
    return value or default


def prompt_choice(label: str, choices: list, default: str) -> str:
    choices_display = '/'.join(choices)
    while True:
        value = input(f"{label} [{choices_display}] (default: {default}): ").strip().lower()
        if not value:
            return default
        if value in choices:
            return value
        print(f"  -> Invalid choice. Pick from: {choices_display}.")


def prompt_int(label: str, default: int, min_value: int, max_value: int) -> int:
    while True:
        raw = input(f"{label} ({min_value}-{max_value}) [default: {default}]: ").strip()
        if not raw:
            return default
        try:
            value = int(raw)
        except ValueError:
            print("  -> Please enter a number.")
            continue
        if min_value <= value <= max_value:
            return value
        print(f"  -> Enter a number between {min_value} and {max_value}.")


def load_existing_products() -> list:
    """Load existing products from products_featured.json."""
    if not os.path.exists(PRODUCTS_FILE):
        return []
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def save_products(products: list) -> None:
    """Save products to products_featured.json."""
    os.makedirs(os.path.dirname(PRODUCTS_FILE), exist_ok=True)
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)


def product_exists(products: list, name: str, website: str) -> bool:
    """Check if product already exists by name or website."""
    name_lower = name.lower().strip()
    website_lower = website.lower().strip()

    for p in products:
        if p.get('name', '').lower().strip() == name_lower:
            return True
        if p.get('website', '').lower().strip() == website_lower:
            return True
    return False


def generate_why_matters(product: dict) -> str:
    """Generate AI insight for why this product matters."""
    try:
        from utils.insight_generator import InsightGenerator
        generator = InsightGenerator()
        insight = generator.generate_insight(product)
        return insight or ''
    except Exception as exc:
        print(f"  -> Insight generation failed: {exc}")
        return ''


def calculate_score(product: dict) -> int:
    """Calculate a default score based on product attributes."""
    base_score = 75

    # Boost for funding
    funding = product.get('funding_total', '')
    if funding:
        if 'B' in funding.upper():
            base_score += 15
        elif 'M' in funding.upper():
            base_score += 10

    # Boost for dark horse index
    dark_horse = product.get('dark_horse_index', 0)
    if dark_horse >= 5:
        base_score += 10
    elif dark_horse >= 4:
        base_score += 5

    # Cap at 100
    return min(100, base_score)


def interactive_add(prefill_name: str = '') -> dict:
    """Interactive mode to add a product."""
    print("\n" + "=" * 50)
    print("  Add Curated Product to products_featured.json")
    print("=" * 50)

    name = prompt_required("Product name", prefill_name)
    website = prompt_required("Website URL")

    # Auto-fetch logo
    print("  -> Fetching logo...")
    auto_logo = fetch_logo_url(website)
    logo_url = prompt_optional("Logo URL", auto_logo)

    description = prompt_required("Description (1-2 sentences)")
    category = prompt_choice("Category", ALLOWED_CATEGORIES, default='other')

    print("\n-- Optional fields (press Enter to skip) --")
    region = prompt_optional("Region (e.g., US, CN, EU)")
    founded_date = prompt_optional("Founded date (YYYY or YYYY-MM)")
    funding_total = prompt_optional("Funding total (e.g., $50M)")
    dark_horse_index = prompt_int("Dark horse index", default=4, min_value=1, max_value=5)
    latest_news = prompt_optional("Latest news (e.g., 2025-11: Raised $10M)")
    why_matters = prompt_optional("Why it matters (leave blank to auto-generate)")

    # Build product
    discovered_at = datetime.utcnow().strftime('%Y-%m-%d')
    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    product = {
        'name': name,
        'description': description,
        'logo_url': logo_url,
        'website': website,
        'categories': [category],
        'rating': 4.5,
        'weekly_users': 0,
        'is_hardware': category == 'hardware',
        'source': 'curated',
        'dark_horse_index': dark_horse_index,
        'first_seen': now_iso,
        'last_seen': now_iso,
    }

    # Add optional fields if provided
    if region:
        product['region'] = region
    if founded_date:
        product['founded_date'] = founded_date
    if funding_total:
        product['funding_total'] = funding_total
    if latest_news:
        product['latest_news'] = latest_news

    # Generate score
    score = calculate_score(product)
    product['trending_score'] = score
    product['final_score'] = score
    product['hot_score'] = score
    product['top_score'] = score

    # Generate why_matters
    if why_matters:
        product['why_matters'] = why_matters
    else:
        print("  -> Generating AI insight...")
        auto_insight = generate_why_matters(product)
        if auto_insight:
            product['why_matters'] = auto_insight
            print(f"  -> Generated: {auto_insight[:60]}...")

    return product


def quick_add(name: str, website: str, description: str, category: str = 'other') -> dict:
    """Quick add mode with minimal prompts."""
    print(f"\n  Quick adding: {name}")

    # Auto-fetch logo
    logo_url = fetch_logo_url(website)

    discovered_at = datetime.utcnow().strftime('%Y-%m-%d')
    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    product = {
        'name': name,
        'description': description,
        'logo_url': logo_url,
        'website': website,
        'categories': [category],
        'rating': 4.5,
        'weekly_users': 0,
        'trending_score': 80,
        'final_score': 80,
        'hot_score': 80,
        'top_score': 80,
        'is_hardware': category == 'hardware',
        'source': 'curated',
        'dark_horse_index': 4,
        'first_seen': now_iso,
        'last_seen': now_iso,
    }

    # Generate why_matters
    print("  -> Generating AI insight...")
    auto_insight = generate_why_matters(product)
    if auto_insight:
        product['why_matters'] = auto_insight

    return product


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Add curated products to products_featured.json',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('name', nargs='?', default='', help='Product name (optional)')
    parser.add_argument('--quick', nargs=3, metavar=('NAME', 'URL', 'DESC'),
                        help='Quick add: --quick "Name" "https://..." "Description"')
    parser.add_argument('--category', default='other', choices=ALLOWED_CATEGORIES,
                        help='Category for quick add')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print product but do not save')

    args = parser.parse_args()

    # Load existing products
    products = load_existing_products()
    print(f"\n  Loaded {len(products)} existing products")

    # Build new product
    if args.quick:
        name, website, description = args.quick
        if product_exists(products, name, website):
            print(f"\n  Product already exists: {name}")
            sys.exit(1)
        new_product = quick_add(name, website, description, args.category)
    else:
        new_product = interactive_add(args.name)
        if product_exists(products, new_product['name'], new_product['website']):
            print(f"\n  Product already exists: {new_product['name']}")
            confirm = input("  Add anyway? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("  Cancelled.")
                sys.exit(0)

    # Preview
    print("\n" + "-" * 50)
    print("  Product Preview:")
    print("-" * 50)
    print(json.dumps(new_product, indent=2, ensure_ascii=False))

    if args.dry_run:
        print("\n  [DRY RUN] Not saved.")
        return

    # Confirm and save
    confirm = input("\n  Save to products_featured.json? [Y/n]: ").strip().lower()
    if confirm == 'n':
        print("  Cancelled.")
        return

    # Insert at beginning (highest priority)
    products.insert(0, new_product)

    # Re-sort by score
    products.sort(key=lambda x: x.get('final_score', 0), reverse=True)

    save_products(products)
    print(f"\n  Saved! Total products: {len(products)}")
    print(f"  -> {PRODUCTS_FILE}")


if __name__ == '__main__':
    main()
