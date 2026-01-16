#!/usr/bin/env python3
"""
Cleanup Placeholder Values Tool for WeeklyAI

Removes or cleans up placeholder values like "未公开", "持续更新中", "TBD", "N/A"
from product data files.

Usage:
    python cleanup_placeholders.py                # Clean all files
    python cleanup_placeholders.py --dry-run     # Preview changes
"""

import json
import os
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products_featured.json')

# Placeholder patterns to clean up
PLACEHOLDER_PATTERNS = [
    '未公开',
    '持续更新中',
    'TBD',
    'N/A',
    'n/a',
    '暂无',
    '待定',
]

# Fields that should have placeholders removed (set to empty string or None)
FIELDS_TO_CLEAN = [
    'valuation',
    'pricing',
    'latest_news',
    'funding_total',
]


def is_placeholder(value):
    """Check if a value is a placeholder."""
    if not value or not isinstance(value, str):
        return False
    value_lower = value.strip().lower()
    return any(pattern.lower() in value_lower for pattern in PLACEHOLDER_PATTERNS)


def clean_product(product, verbose=False):
    """Clean placeholder values from a product."""
    changes = []

    for field in FIELDS_TO_CLEAN:
        if field in product:
            value = product[field]
            if is_placeholder(value):
                if verbose:
                    print(f"  {product.get('name', 'Unknown')}: {field} = '{value}' -> (removed)")
                product[field] = ''
                changes.append(field)

    return changes


def main():
    parser = argparse.ArgumentParser(description='Clean up placeholder values')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show all changes')
    args = parser.parse_args()

    if not os.path.exists(PRODUCTS_FILE):
        print(f"Error: {PRODUCTS_FILE} not found")
        return

    with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
        products = json.load(f)

    total_changes = 0
    for product in products:
        changes = clean_product(product, verbose=args.verbose or args.dry_run)
        total_changes += len(changes)

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Cleaned {total_changes} placeholder values")

    if not args.dry_run and total_changes > 0:
        with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        print(f"Saved {PRODUCTS_FILE}")


if __name__ == '__main__':
    main()
