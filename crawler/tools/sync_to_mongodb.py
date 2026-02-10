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

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Data files
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products_featured.json")
BLOGS_FILE = os.path.join(DATA_DIR, "blogs_news.json")
CANDIDATES_FILE = os.path.join(DATA_DIR, "candidates", "pending_review.json")
DARK_HORSES_DIR = os.path.join(DATA_DIR, "dark_horses")

# MongoDB connection
try:
    from pymongo import ASCENDING, DESCENDING, TEXT, MongoClient
    HAS_MONGO = True
except ImportError:
    HAS_MONGO = False


def get_mongo_db():
    """Get MongoDB connection."""
    if not HAS_MONGO:
        print("  x pymongo not installed. Run: pip install pymongo")
        return None

    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/weeklyai")
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        db = client.get_database()
        print(f"  OK Connected to MongoDB: {db.name}")
        return db
    except Exception as e:
        print(f"  x MongoDB connection failed: {e}")
        return None


def load_json(filepath: str) -> list:
    """Load JSON file."""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  x Failed to load {filepath}: {e}")
        return []


def _normalize_domain(url: str) -> str:
    """Normalize domain for dedupe: strip scheme/www/port and keep first path."""
    if not url:
        return ""
    raw = str(url).strip()
    if not raw:
        return ""
    if not re.match(r"^https?://", raw, re.IGNORECASE) and "." in raw:
        raw = f"https://{raw}"
    try:
        parsed = urlparse(raw)
        domain = (parsed.netloc or "").lower()
        domain = re.sub(r"^www\.", "", domain)
        domain = domain.split(":")[0]
        if not domain:
            return ""
        path = (parsed.path or "").strip("/")
        if path:
            first = path.split("/")[0]
            if len(first) > 1:
                return f"{domain}/{first}"
        return domain
    except Exception:
        return raw.lower()


def build_sync_key(item: Dict[str, Any]) -> str:
    """Create stable key matching backend key strategy."""
    website = item.get("website") or ""
    key = _normalize_domain(website)
    if key:
        return key
    name = (item.get("name") or "").lower().strip()
    return "".join(c for c in name if c.isalnum())


def normalize_key(item: dict) -> str:
    """Backward-compatible alias."""
    return build_sync_key(item)


def _normalize_curated_product(product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Map curated dark-horse fields into standard product fields."""
    if not isinstance(product, dict):
        return None
    normalized = product.copy()
    if not normalized.get("logo_url"):
        normalized["logo_url"] = normalized.get("logo") or normalized.get("logoUrl") or ""
    if not normalized.get("categories"):
        category = normalized.get("category")
        if category:
            normalized["categories"] = [category]
    if not normalized.get("source"):
        normalized["source"] = "curated"
    if "is_hardware" not in normalized:
        normalized["is_hardware"] = False
    return normalized


def _merge_fields(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """Merge fields with simple quality heuristics."""
    numeric_max_fields = {"dark_horse_index", "final_score", "hot_score", "trending_score", "rating"}
    text_fields = {"description", "why_matters", "latest_news"}
    for field, value in source.items():
        if value in (None, "", [], {}):
            continue
        if field in numeric_max_fields:
            try:
                current = target.get(field) or 0
                target[field] = max(float(current), float(value))
            except Exception:
                if not target.get(field):
                    target[field] = value
            continue
        if field in text_fields:
            current = str(target.get(field) or "")
            candidate = str(value)
            if len(candidate) > len(current):
                target[field] = value
            continue
        if not target.get(field):
            target[field] = value


def load_dark_horses() -> List[Dict[str, Any]]:
    """Load curated dark-horse products from dark_horses/*.json."""
    if not os.path.isdir(DARK_HORSES_DIR):
        return []
    curated: List[Dict[str, Any]] = []
    for filename in sorted(os.listdir(DARK_HORSES_DIR)):
        if not filename.endswith(".json"):
            continue
        if filename == "template.json":
            continue
        path = os.path.join(DARK_HORSES_DIR, filename)
        try:
            data = load_json(path)
            if isinstance(data, dict):
                data = [data]
            if isinstance(data, list):
                curated.extend(item for item in data if isinstance(item, dict))
        except Exception:
            continue
    return curated


def merge_products(featured: List[Dict[str, Any]], curated: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge featured products and curated dark-horse products by normalized key."""
    by_key: Dict[str, Dict[str, Any]] = {}
    ordered: List[Dict[str, Any]] = []

    for item in featured:
        if not isinstance(item, dict):
            continue
        key = build_sync_key(item)
        if not key:
            continue
        if key in by_key:
            _merge_fields(by_key[key], item)
        else:
            by_key[key] = item
            ordered.append(item)

    for item in curated:
        normalized = _normalize_curated_product(item)
        if not normalized:
            continue
        key = build_sync_key(normalized)
        if not key:
            continue
        if key in by_key:
            _merge_fields(by_key[key], normalized)
        else:
            by_key[key] = normalized
            ordered.append(normalized)

    return ordered


def clear_non_curated(db, collection_name: str, dry_run: bool = False) -> int:
    """Remove items that are not from curated sources."""
    collection = db[collection_name]
    curated_sources = {"curated", "candidate_approved", "manual"}
    query = {"source": {"$nin": list(curated_sources)}}
    count = collection.count_documents(query)

    if dry_run:
        print(f"  [DRY RUN] Would delete {count} non-curated items from {collection_name}")
        return count

    if count > 0:
        result = collection.delete_many(query)
        print(f"  OK Deleted {result.deleted_count} non-curated items from {collection_name}")
        return result.deleted_count
    return 0


def sync_products(db, products: list, dry_run: bool = False) -> dict:
    """Sync products to MongoDB."""
    collection = db["products"]
    stats = {"inserted": 0, "updated": 0, "skipped": 0}
    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    for product in products:
        key = build_sync_key(product)
        if not key:
            stats["skipped"] += 1
            continue

        doc = product.copy()
        doc["_sync_key"] = key
        doc["synced_at"] = now_iso
        doc.setdefault("source", "curated")
        doc.setdefault("content_type", "product")
        doc.pop("_id", None)
        doc.pop("_candidate_reason", None)

        if dry_run:
            stats["updated"] += 1
            continue

        result = collection.update_one({"_sync_key": key}, {"$set": doc}, upsert=True)
        if result.upserted_id:
            stats["inserted"] += 1
        elif result.modified_count > 0:
            stats["updated"] += 1
        else:
            stats["skipped"] += 1

    return stats


def sync_blogs(db, blogs: list, dry_run: bool = False) -> dict:
    """Sync blogs/news to MongoDB."""
    collection = db["blogs"]
    stats = {"inserted": 0, "updated": 0, "skipped": 0}
    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    for blog in blogs:
        url = (blog.get("url") or blog.get("website") or "").strip()
        title = (blog.get("title") or blog.get("name") or "").strip()
        key = url or "".join(c.lower() for c in title if c.isalnum())
        if not key:
            stats["skipped"] += 1
            continue

        doc = blog.copy()
        doc["_sync_key"] = key
        doc["synced_at"] = now_iso
        doc.setdefault("content_type", "blog")
        doc.pop("_id", None)

        if dry_run:
            stats["updated"] += 1
            continue

        result = collection.update_one({"_sync_key": key}, {"$set": doc}, upsert=True)
        if result.upserted_id:
            stats["inserted"] += 1
        elif result.modified_count > 0:
            stats["updated"] += 1
        else:
            stats["skipped"] += 1
    return stats


def sync_candidates(db, candidates: list, dry_run: bool = False) -> dict:
    """Sync candidates to MongoDB (separate collection for review)."""
    collection = db["candidates"]
    stats = {"inserted": 0, "updated": 0, "skipped": 0}
    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    for candidate in candidates:
        key = build_sync_key(candidate)
        if not key:
            stats["skipped"] += 1
            continue

        doc = candidate.copy()
        doc["_sync_key"] = key
        doc["synced_at"] = now_iso
        doc.setdefault("status", "pending")
        doc.pop("_id", None)

        if dry_run:
            stats["updated"] += 1
            continue

        result = collection.update_one({"_sync_key": key}, {"$set": doc}, upsert=True)
        if result.upserted_id:
            stats["inserted"] += 1
        elif result.modified_count > 0:
            stats["updated"] += 1
        else:
            stats["skipped"] += 1
    return stats


def ensure_indexes(db, dry_run: bool = False) -> None:
    """Create recommended indexes for products/blogs collections."""
    products = db["products"]
    blogs = db["blogs"]
    product_indexes = [
        ("_sync_key_unique", [("_sync_key", ASCENDING)], {"unique": True}),
        ("website_1", [("website", ASCENDING)], {}),
        ("dark_horse_index_desc", [("dark_horse_index", DESCENDING)], {}),
        ("final_score_desc", [("final_score", DESCENDING)], {}),
        ("discovered_at_desc", [("discovered_at", DESCENDING)], {}),
        ("categories_1", [("categories", ASCENDING)], {}),
    ]
    blog_indexes = [
        ("_sync_key_unique", [("_sync_key", ASCENDING)], {"unique": True}),
        ("published_at_desc", [("published_at", DESCENDING)], {}),
        ("created_at_desc", [("created_at", DESCENDING)], {}),
    ]

    print("\n  Ensuring indexes...")
    for name, keys, opts in product_indexes:
        if dry_run:
            print(f"  [DRY RUN] products.{name}")
        else:
            products.create_index(keys, name=name, **opts)
            print(f"  OK products.{name}")

    if dry_run:
        print("  [DRY RUN] products.text_search")
    else:
        products.create_index(
            [("name", TEXT), ("description", TEXT), ("why_matters", TEXT)],
            name="text_search",
        )
        print("  OK products.text_search")

    for name, keys, opts in blog_indexes:
        if dry_run:
            print(f"  [DRY RUN] blogs.{name}")
        else:
            blogs.create_index(keys, name=name, **opts)
            print(f"  OK blogs.{name}")


def print_stats(name: str, stats: dict, dry_run: bool = False):
    """Print sync statistics."""
    prefix = "[DRY RUN] " if dry_run else ""
    print(
        f"  {prefix}{name}: {stats['inserted']} inserted, {stats['updated']} updated, {stats['skipped']} skipped"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Sync curated JSON data to MongoDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/sync_to_mongodb.py                  # Sync products only
  python tools/sync_to_mongodb.py --all            # Sync everything
  python tools/sync_to_mongodb.py --clear-old      # Clear non-curated first
  python tools/sync_to_mongodb.py --dry-run        # Preview changes
""",
    )
    parser.add_argument("--blogs", action="store_true", help="Also sync blogs_news.json")
    parser.add_argument("--candidates", action="store_true", help="Also sync candidates")
    parser.add_argument("--all", "-a", action="store_true", help="Sync everything")
    parser.add_argument("--clear-old", action="store_true", help="Clear non-curated items before sync")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--ensure-indexes", action="store_true", help="Only ensure indexes")
    args = parser.parse_args()

    if args.all:
        args.blogs = True
        args.candidates = True

    print("\n  MongoDB Sync Tool")
    print("  " + "=" * 40)
    db = get_mongo_db()
    if db is None:
        sys.exit(1)

    if args.ensure_indexes:
        ensure_indexes(db, args.dry_run)
        print()
        return

    if args.clear_old:
        print("\n  Clearing non-curated items...")
        clear_non_curated(db, "products", args.dry_run)
        if args.blogs:
            clear_non_curated(db, "blogs", args.dry_run)

    print("\n  Syncing products...")
    featured = load_json(PRODUCTS_FILE)
    curated = load_dark_horses()
    merged = merge_products(featured, curated)
    print(f"  Loaded featured: {len(featured)}")
    print(f"  Loaded dark_horses: {len(curated)}")
    print(f"  Merged+deduped: {len(merged)}")
    if merged:
        stats = sync_products(db, merged, args.dry_run)
        print_stats("Products", stats, args.dry_run)
    else:
        print("  x No products to sync")

    if args.blogs:
        print("\n  Syncing blogs...")
        blogs = load_json(BLOGS_FILE)
        if blogs:
            stats = sync_blogs(db, blogs, args.dry_run)
            print_stats("Blogs", stats, args.dry_run)
        else:
            print("  x No blogs to sync")

    if args.candidates:
        print("\n  Syncing candidates...")
        candidates = load_json(CANDIDATES_FILE)
        if candidates:
            stats = sync_candidates(db, candidates, args.dry_run)
            print_stats("Candidates", stats, args.dry_run)
        else:
            print("  x No candidates to sync")

    ensure_indexes(db, args.dry_run)

    print("\n  " + "-" * 40)
    if args.dry_run:
        print("  [DRY RUN] No changes made")
    else:
        print("  OK Sync complete!")
        print("\n  Collection counts:")
        print(f"    products:   {db['products'].count_documents({})}")
        if args.blogs:
            print(f"    blogs:      {db['blogs'].count_documents({})}")
        if args.candidates:
            print(f"    candidates: {db['candidates'].count_documents({})}")
    print()


if __name__ == "__main__":
    main()
