#!/usr/bin/env python3
"""
List pending product candidates for review.

Usage:
    python tools/list_candidates.py                  # List all candidates
    python tools/list_candidates.py --top 10         # Show top 10
    python tools/list_candidates.py --category coding  # Filter by category
    python tools/list_candidates.py --details        # Show full details
"""

import json
import os
import sys
import argparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

CANDIDATES_FILE = os.path.join(PROJECT_ROOT, 'data', 'candidates', 'pending_review.json')


def load_candidates() -> list:
    """Load pending candidates."""
    if not os.path.exists(CANDIDATES_FILE):
        return []
    try:
        with open(CANDIDATES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def display_summary(candidate: dict, index: int) -> None:
    """Display candidate in summary format."""
    name = candidate.get('name', 'Unknown')
    score = candidate.get('final_score', candidate.get('trending_score', 0))
    dark_horse = candidate.get('dark_horse_index', 0)
    reason = candidate.get('_candidate_reason', '')
    source = candidate.get('source', '')
    categories = ', '.join(candidate.get('categories', ['other']))

    print(f"  [{index:2d}] {name:<35} Score:{score:3d}  DH:{dark_horse}  [{categories}]")
    if reason:
        print(f"       Reason: {reason}")


def display_details(candidate: dict, index: int) -> None:
    """Display candidate with full details."""
    print(f"\n  [{index}] {candidate.get('name', 'Unknown')}")
    print("  " + "-" * 60)

    fields = [
        ('Website', 'website'),
        ('Description', 'description'),
        ('Categories', 'categories'),
        ('Score', 'final_score'),
        ('Dark Horse Index', 'dark_horse_index'),
        ('Funding', 'funding_total'),
        ('Founded', 'founded_date'),
        ('Source', 'source'),
        ('Candidate Reason', '_candidate_reason'),
    ]

    for label, key in fields:
        value = candidate.get(key)
        if value:
            if isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            # Truncate long descriptions
            if key == 'description' and len(str(value)) > 100:
                value = str(value)[:100] + '...'
            print(f"    {label}: {value}")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description='List pending product candidates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Commands to approve candidates:
  python tools/approve_candidate.py "ProductName"   # Approve by name
  python tools/approve_candidate.py --index N       # Approve by index
  python tools/approve_candidate.py --all           # Approve all
'''
    )
    parser.add_argument('--top', '-n', type=int, default=0, help='Show top N candidates')
    parser.add_argument('--category', '-c', type=str, help='Filter by category')
    parser.add_argument('--details', '-d', action='store_true', help='Show full details')
    parser.add_argument('--sort', '-s', choices=['score', 'dark_horse', 'name'],
                        default='score', help='Sort by field')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    candidates = load_candidates()

    if not candidates:
        print("\n  No pending candidates found.")
        print(f"  Run: python main.py --generate-candidates")
        sys.exit(0)

    # Filter by category
    if args.category:
        candidates = [
            c for c in candidates
            if args.category.lower() in [cat.lower() for cat in c.get('categories', [])]
        ]

    # Sort
    if args.sort == 'score':
        candidates.sort(key=lambda x: x.get('final_score', 0), reverse=True)
    elif args.sort == 'dark_horse':
        candidates.sort(key=lambda x: x.get('dark_horse_index', 0), reverse=True)
    elif args.sort == 'name':
        candidates.sort(key=lambda x: x.get('name', '').lower())

    # Limit
    if args.top > 0:
        candidates = candidates[:args.top]

    # Output
    if args.json:
        print(json.dumps(candidates, indent=2, ensure_ascii=False))
        sys.exit(0)

    print(f"\n  Pending Candidates: {len(candidates)}")
    print("  " + "=" * 70)

    for idx, candidate in enumerate(candidates):
        if args.details:
            display_details(candidate, idx)
        else:
            display_summary(candidate, idx)

    print()
    print("  To approve: python tools/approve_candidate.py --index N")
    print("  Or:         python tools/approve_candidate.py \"ProductName\"")


if __name__ == '__main__':
    main()
