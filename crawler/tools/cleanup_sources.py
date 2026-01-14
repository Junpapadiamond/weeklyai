"""
Cleanup helper to remove blocked sources/domains from JSON outputs and MongoDB.
"""

import json
import os

BLOCKED_SOURCES = {'github', 'huggingface', 'huggingface_spaces'}
BLOCKED_DOMAINS = ('github.com', 'huggingface.co')


def is_blocked(item):
    source = (item.get('source') or '').lower().strip()
    if source in BLOCKED_SOURCES:
        return True
    website = (item.get('website') or '').lower().strip()
    return any(domain in website for domain in BLOCKED_DOMAINS)


def clean_json(path):
    if not os.path.exists(path):
        return 0, 0
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, list):
        return 0, 0
    cleaned = [item for item in data if isinstance(item, dict) and not is_blocked(item)]
    if len(cleaned) != len(data):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2)
    return len(data), len(cleaned)


def clean_mongo():
    try:
        from pymongo import MongoClient
    except ImportError:
        print("pymongo not installed, skip MongoDB cleanup.")
        return

    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/weeklyai')
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
    db = client.get_database()
    collection = db.products
    result = collection.delete_many({
        '$or': [
            {'source': {'$in': list(BLOCKED_SOURCES)}},
            {'website': {'$regex': r'github\\.com|huggingface\\.co', '$options': 'i'}}
        ]
    })
    print(f"MongoDB cleanup removed {result.deleted_count} documents.")


if __name__ == '__main__':
    base_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    targets = [
        os.path.join(base_dir, 'products_latest.json'),
        os.path.join(base_dir, 'products_featured.json'),
    ]
    for path in targets:
        before, after = clean_json(path)
        if before:
            print(f"{path}: {before} -> {after}")
    clean_mongo()
