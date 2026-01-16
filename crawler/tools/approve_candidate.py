#!/usr/bin/env python3
"""
Approve a candidate product and move it to products_featured.json.

Usage:
    python tools/approve_candidate.py "ProductName"     # Approve by name
    python tools/approve_candidate.py --index 0         # Approve by index
    python tools/approve_candidate.py --all             # Approve all candidates
    python tools/approve_candidate.py --list            # List candidates first
"""

import json
import os
import sys
import argparse
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

CANDIDATES_FILE = os.path.join(PROJECT_ROOT, 'data', 'candidates', 'pending_review.json')
PRODUCTS_FILE = os.path.join(PROJECT_ROOT, 'data', 'products_featured.json')
APPROVED_ARCHIVE = os.path.join(PROJECT_ROOT, 'data', 'candidates', 'approved_archive.json')


def load_json(filepath: str) -> list:
    """Load JSON file, return empty list if not exists."""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def save_json(filepath: str, data: list) -> None:
    """Save data to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_name(name: str) -> str:
    """Normalize product name for matching."""
    return ''.join(c.lower() for c in name if c.isalnum())


def find_candidate_by_name(candidates: list, name: str) -> tuple:
    """Find candidate by name, return (index, candidate) or (-1, None)."""
    name_norm = normalize_name(name)
    for idx, candidate in enumerate(candidates):
        if normalize_name(candidate.get('name', '')) == name_norm:
            return idx, candidate
    return -1, None


def prepare_for_featured(candidate: dict) -> dict:
    """Prepare candidate for products_featured.json."""
    # Remove internal candidate metadata
    product = {k: v for k, v in candidate.items() if not k.startswith('_')}

    # Ensure required fields
    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    if 'source' not in product:
        product['source'] = 'candidate_approved'

    if 'first_seen' not in product:
        product['first_seen'] = now_iso

    product['last_seen'] = now_iso

    # Ensure score fields exist
    score = product.get('final_score', product.get('trending_score', 75))
    product.setdefault('trending_score', score)
    product.setdefault('final_score', score)
    product.setdefault('hot_score', score)
    product.setdefault('top_score', score)

    return product


def product_exists_in_featured(products: list, candidate: dict) -> bool:
    """Check if candidate already exists in featured products."""
    candidate_name = normalize_name(candidate.get('name', ''))
    candidate_website = (candidate.get('website') or '').lower().strip()

    for p in products:
        if normalize_name(p.get('name', '')) == candidate_name:
            return True
        if candidate_website and (p.get('website') or '').lower().strip() == candidate_website:
            return True
    return False


def display_candidate(candidate: dict, index: int) -> None:
    """Display candidate summary."""
    name = candidate.get('name', 'Unknown')
    score = candidate.get('final_score', candidate.get('trending_score', 0))
    dark_horse = candidate.get('dark_horse_index', 0)
    reason = candidate.get('_candidate_reason', '')
    website = candidate.get('website', '')
    desc = (candidate.get('description') or '')[:80]

    print(f"  [{index}] {name}")
    print(f"      Score: {score} | Dark Horse: {dark_horse}")
    print(f"      Reason: {reason}")
    print(f"      URL: {website}")
    print(f"      Desc: {desc}...")
    print()


def approve_candidate(candidates: list, products: list, index: int, dry_run: bool = False) -> bool:
    """Approve a single candidate and move to products."""
    if index < 0 or index >= len(candidates):
        print(f"  Invalid index: {index}")
        return False

    candidate = candidates[index]
    name = candidate.get('name', 'Unknown')

    # Check if already exists
    if product_exists_in_featured(products, candidate):
        print(f"  Skipping '{name}' - already exists in featured products")
        return False

    if dry_run:
        print(f"  [DRY RUN] Would approve: {name}")
        return True

    # Prepare and add to products
    product = prepare_for_featured(candidate)
    products.append(product)

    print(f"  Approved: {name}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Approve candidates and move to products_featured.json',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python tools/approve_candidate.py "Emergent"       # Approve by name
  python tools/approve_candidate.py --index 0        # Approve first candidate
  python tools/approve_candidate.py --all            # Approve all
  python tools/approve_candidate.py --list           # Just list candidates
'''
    )
    parser.add_argument('name', nargs='?', default='', help='Product name to approve')
    parser.add_argument('--index', '-i', type=int, default=-1, help='Approve by index')
    parser.add_argument('--all', '-a', action='store_true', help='Approve all candidates')
    parser.add_argument('--list', '-l', action='store_true', help='List candidates without approving')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be approved')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation')

    args = parser.parse_args()

    # Load data
    candidates = load_json(CANDIDATES_FILE)
    products = load_json(PRODUCTS_FILE)

    if not candidates:
        print("\n  No pending candidates found.")
        print(f"  Run: python main.py --generate-candidates")
        sys.exit(0)

    print(f"\n  Loaded {len(candidates)} candidates, {len(products)} featured products")

    # List mode
    if args.list or (not args.name and args.index < 0 and not args.all):
        print("\n  Pending Candidates:")
        print("  " + "-" * 60)
        for idx, c in enumerate(candidates):
            display_candidate(c, idx)
        print(f"\n  Use --index N or 'ProductName' to approve.")
        sys.exit(0)

    # Determine which candidates to approve
    to_approve = []
    if args.all:
        to_approve = list(range(len(candidates)))
        if not args.yes and not args.dry_run:
            confirm = input(f"\n  Approve all {len(candidates)} candidates? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("  Cancelled.")
                sys.exit(0)
    elif args.index >= 0:
        to_approve = [args.index]
    elif args.name:
        idx, candidate = find_candidate_by_name(candidates, args.name)
        if idx < 0:
            print(f"\n  Candidate not found: '{args.name}'")
            print("  Available candidates:")
            for c in candidates[:5]:
                print(f"    - {c.get('name')}")
            if len(candidates) > 5:
                print(f"    ... and {len(candidates) - 5} more")
            sys.exit(1)
        to_approve = [idx]

    # Approve candidates (in reverse order to maintain indices)
    approved_count = 0
    approved_names = []
    for idx in sorted(to_approve, reverse=True):
        candidate = candidates[idx]
        if approve_candidate(candidates, products, idx, args.dry_run):
            approved_names.append(candidate.get('name'))
            approved_count += 1
            if not args.dry_run:
                candidates.pop(idx)

    if args.dry_run:
        print(f"\n  [DRY RUN] Would approve {approved_count} candidates")
        sys.exit(0)

    if approved_count == 0:
        print("\n  No candidates approved.")
        sys.exit(0)

    # Sort products by score
    products.sort(key=lambda x: x.get('final_score', 0), reverse=True)

    # Save updated files
    save_json(PRODUCTS_FILE, products)
    save_json(CANDIDATES_FILE, candidates)

    # Archive approved
    archive = load_json(APPROVED_ARCHIVE)
    for name in approved_names:
        archive.append({
            'name': name,
            'approved_at': datetime.now(timezone.utc).isoformat()
        })
    save_json(APPROVED_ARCHIVE, archive)

    print(f"\n  Approved {approved_count} candidate(s):")
    for name in approved_names:
        print(f"    + {name}")
    print(f"\n  Total featured products: {len(products)}")
    print(f"  Remaining candidates: {len(candidates)}")


if __name__ == '__main__':
    main()
