#!/usr/bin/env python3
"""
Remove products with invalid or unknown websites from JSON data files and MongoDB.

Targets:
- crawler/data/products_featured.json
- crawler/data/dark_horses/*.json
- crawler/data/rising_stars/*.json
- crawler/data/candidates/*.json
- MongoDB collection: products (if MONGO_URI set)
"""

import json
import os
from typing import Any, Dict, List, Tuple

UNKNOWN_VALUES = {
    "unknown", "n/a", "na", "none", "null", "undefined", ""
}


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def is_valid_website(value: Any) -> bool:
    if not value:
        return False
    raw = str(value).strip()
    if not raw:
        return False
    lowered = raw.lower()
    if lowered in UNKNOWN_VALUES:
        return False
    if not lowered.startswith(("http://", "https://")):
        return False
    return True


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: str, payload: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def clean_items(items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    kept = []
    removed = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if is_valid_website(item.get("website")):
            kept.append(item)
        else:
            removed.append(item)
    return kept, removed


def clean_file(path: str) -> Tuple[int, int]:
    payload = _load_json(path)
    if isinstance(payload, list):
        kept, removed = clean_items(payload)
        if removed:
            _save_json(path, kept)
        return len(kept), len(removed)

    if isinstance(payload, dict) and isinstance(payload.get("products"), list):
        kept, removed = clean_items(payload["products"])
        if removed:
            payload["products"] = kept
            _save_json(path, payload)
        return len(kept), len(removed)

    return 0, 0


def iter_json_files() -> List[str]:
    files: List[str] = []
    featured = os.path.join(DATA_DIR, "products_featured.json")
    if os.path.exists(featured):
        files.append(featured)

    for folder in ("dark_horses", "rising_stars", "candidates"):
        dir_path = os.path.join(DATA_DIR, folder)
        if not os.path.isdir(dir_path):
            continue
        for name in sorted(os.listdir(dir_path)):
            if not name.endswith(".json"):
                continue
            files.append(os.path.join(dir_path, name))

    return files


def clean_mongodb() -> int:
    mongo_uri = os.getenv("MONGO_URI", "").strip()
    if not mongo_uri:
        print("MongoDB: MONGO_URI not set, skipping")
        return 0
    try:
        from pymongo import MongoClient
    except Exception:
        print("MongoDB: pymongo not installed, skipping")
        return 0

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
    db = client.get_database()
    collection = db.products

    query = {
        "$or": [
            {"website": {"$in": list(UNKNOWN_VALUES)}},
            {"website": {"$exists": False}},
            {"website": None},
            {"website": {"$not": {"$regex": r"^https?://", "$options": "i"}}},
        ]
    }
    result = collection.delete_many(query)
    print(f"MongoDB: removed {result.deleted_count} items")
    return int(result.deleted_count)


def main() -> int:
    files = iter_json_files()
    total_removed = 0

    print(f"Cleaning {len(files)} JSON files...")
    for path in files:
        kept, removed = clean_file(path)
        total_removed += removed
        if removed:
            print(f"  - {path}: removed {removed}, kept {kept}")
        else:
            print(f"  - {path}: no changes")

    clean_mongodb()
    print(f"Total removed (JSON): {total_removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
