#!/usr/bin/env python3
"""
Sync curated JSON data to MongoDB.

Usage:
    python tools/sync_to_mongodb.py                # Sync products only
    python tools/sync_to_mongodb.py --blogs        # Also sync blogs
    python tools/sync_to_mongodb.py --all          # Sync everything
    python tools/sync_to_mongodb.py --clear-old    # Remove non-curated items first
    python tools/sync_to_mongodb.py --dry-run      # Show what would be synced
"""

import json
import os
import sys
import argparse
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Data files
PRODUCTS_FILE = os.path.join(PROJECT_ROOT, 'data', 'products_featured.json')
BLOGS_FILE = os.path.join(PROJECT_ROOT, 'data', 'blogs_news.json')
CANDIDATES_FILE = os.path.join(PROJECT_ROOT, 'data', 'candidates', 'pending_review.json')

# MongoDB connection
try:
    from pymongo import MongoClient
    from pymongo.errors import BulkWriteError
    HAS_MONGO = True
except ImportError:
    HAS_MONGO = False


def get_mongo_db():
    """Get MongoDB connection."""
    if not HAS_MONGO:
        print("  ✗ pymongo not installed. Run: pip install pymongo")
        return None

    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/weeklyai')
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client.get_database()
        print(f"  ✓ Connected to MongoDB: {db.name}")
        return db
    except Exception as e:
        print(f"  ✗ MongoDB connection failed: {e}")
        return None


def load_json(filepath: str) -> list:
    """Load JSON file."""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  ✗ Failed to load {filepath}: {e}")
        return []


def normalize_key(item: dict) -> str:
    """Create a unique key for deduplication."""
    # Prefer website, fallback to normalized name
    website = (item.get('website') or '').lower().strip()
    if website:
        return website
    name = (item.get('name') or '').lower().strip()
    return ''.join(c for c in name if c.isalnum())


def clear_non_curated(db, collection_name: str, dry_run: bool = False) -> int:
    """Remove items that are not from curated sources."""
    collection = db[collection_name]

    # Curated sources to keep
    curated_sources = {'curated', 'candidate_approved', 'manual'}

    # Find non-curated items
    query = {'source': {'$nin': list(curated_sources)}}
    count = collection.count_documents(query)

    if dry_run:
        print(f"  [DRY RUN] Would delete {count} non-curated items from {collection_name}")
        return count

    if count > 0:
        result = collection.delete_many(query)
        print(f"  ✓ Deleted {result.deleted_count} non-curated items from {collection_name}")
        return result.deleted_count

    return 0


def sync_products(db, products: list, dry_run: bool = False) -> dict:
    """Sync products to MongoDB."""
    collection = db['products']
    stats = {'inserted': 0, 'updated': 0, 'skipped': 0}

    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    for product in products:
        key = normalize_key(product)
        if not key:
            stats['skipped'] += 1
            continue

        # Prepare document
        doc = product.copy()
        doc['_sync_key'] = key
        doc['synced_at'] = now_iso
        doc.setdefault('source', 'curated')
        doc.setdefault('content_type', 'product')

        # Remove internal fields
        doc.pop('_id', None)
        doc.pop('_candidate_reason', None)

        if dry_run:
            stats['updated'] += 1
            continue

        # Upsert by sync key
        result = collection.update_one(
            {'_sync_key': key},
            {'$set': doc},
            upsert=True
        )

        if result.upserted_id:
            stats['inserted'] += 1
        elif result.modified_count > 0:
            stats['updated'] += 1
        else:
            stats['skipped'] += 1

    return stats


def sync_blogs(db, blogs: list, dry_run: bool = False) -> dict:
    """Sync blogs/news to MongoDB."""
    collection = db['blogs']
    stats = {'inserted': 0, 'updated': 0, 'skipped': 0}

    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    for blog in blogs:
        # Use URL or title as key
        url = (blog.get('url') or blog.get('website') or '').strip()
        title = (blog.get('title') or blog.get('name') or '').strip()
        key = url or ''.join(c.lower() for c in title if c.isalnum())

        if not key:
            stats['skipped'] += 1
            continue

        # Prepare document
        doc = blog.copy()
        doc['_sync_key'] = key
        doc['synced_at'] = now_iso
        doc.setdefault('content_type', 'blog')

        # Remove internal fields
        doc.pop('_id', None)

        if dry_run:
            stats['updated'] += 1
            continue

        # Upsert by sync key
        result = collection.update_one(
            {'_sync_key': key},
            {'$set': doc},
            upsert=True
        )

        if result.upserted_id:
            stats['inserted'] += 1
        elif result.modified_count > 0:
            stats['updated'] += 1
        else:
            stats['skipped'] += 1

    return stats


def sync_candidates(db, candidates: list, dry_run: bool = False) -> dict:
    """Sync candidates to MongoDB (separate collection for review)."""
    collection = db['candidates']
    stats = {'inserted': 0, 'updated': 0, 'skipped': 0}

    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    for candidate in candidates:
        key = normalize_key(candidate)
        if not key:
            stats['skipped'] += 1
            continue

        # Prepare document
        doc = candidate.copy()
        doc['_sync_key'] = key
        doc['synced_at'] = now_iso
        doc.setdefault('status', 'pending')

        # Remove internal fields but keep candidate reason
        doc.pop('_id', None)

        if dry_run:
            stats['updated'] += 1
            continue

        # Upsert by sync key
        result = collection.update_one(
            {'_sync_key': key},
            {'$set': doc},
            upsert=True
        )

        if result.upserted_id:
            stats['inserted'] += 1
        elif result.modified_count > 0:
            stats['updated'] += 1
        else:
            stats['skipped'] += 1

    return stats


def print_stats(name: str, stats: dict, dry_run: bool = False):
    """Print sync statistics."""
    prefix = "[DRY RUN] " if dry_run else ""
    print(f"  {prefix}{name}: {stats['inserted']} inserted, {stats['updated']} updated, {stats['skipped']} skipped")


def main():
    parser = argparse.ArgumentParser(
        description='Sync curated JSON data to MongoDB',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python tools/sync_to_mongodb.py                  # Sync products only
  python tools/sync_to_mongodb.py --all            # Sync everything
  python tools/sync_to_mongodb.py --clear-old      # Clear non-curated first
  python tools/sync_to_mongodb.py --dry-run        # Preview changes
'''
    )
    parser.add_argument('--blogs', action='store_true', help='Also sync blogs_news.json')
    parser.add_argument('--candidates', action='store_true', help='Also sync candidates')
    parser.add_argument('--all', '-a', action='store_true', help='Sync everything')
    parser.add_argument('--clear-old', action='store_true',
                        help='Clear non-curated items before sync')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')

    args = parser.parse_args()

    if args.all:
        args.blogs = True
        args.candidates = True

    print("\n  MongoDB Sync Tool")
    print("  " + "=" * 40)

    # Connect to MongoDB
    db = get_mongo_db()
    if db is None:
        sys.exit(1)

    # Clear old non-curated items if requested
    if args.clear_old:
        print("\n  Clearing non-curated items...")
        clear_non_curated(db, 'products', args.dry_run)
        if args.blogs:
            clear_non_curated(db, 'blogs', args.dry_run)

    # Sync products
    print("\n  Syncing products...")
    products = load_json(PRODUCTS_FILE)
    if products:
        stats = sync_products(db, products, args.dry_run)
        print_stats("Products", stats, args.dry_run)
    else:
        print("  ⚠ No products to sync")

    # Sync blogs
    if args.blogs:
        print("\n  Syncing blogs...")
        blogs = load_json(BLOGS_FILE)
        if blogs:
            stats = sync_blogs(db, blogs, args.dry_run)
            print_stats("Blogs", stats, args.dry_run)
        else:
            print("  ⚠ No blogs to sync")

    # Sync candidates
    if args.candidates:
        print("\n  Syncing candidates...")
        candidates = load_json(CANDIDATES_FILE)
        if candidates:
            stats = sync_candidates(db, candidates, args.dry_run)
            print_stats("Candidates", stats, args.dry_run)
        else:
            print("  ⚠ No candidates to sync")

    # Summary
    print("\n  " + "-" * 40)
    if args.dry_run:
        print("  [DRY RUN] No changes made")
    else:
        print("  ✓ Sync complete!")

        # Show collection counts
        print(f"\n  Collection counts:")
        print(f"    products:   {db['products'].count_documents({})}")
        if args.blogs:
            print(f"    blogs:      {db['blogs'].count_documents({})}")
        if args.candidates:
            print(f"    candidates: {db['candidates'].count_documents({})}")

    print()


if __name__ == '__main__':
    main()
