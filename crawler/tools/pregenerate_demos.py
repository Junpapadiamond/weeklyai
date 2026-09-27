"""Pregenerate a bounded number of dark-horse workflows; cache hits are free."""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.demo_experiences import prepare_experience, ready_experience, provider_available
from app.services.demo_store import DemoStore, env_int
from app.services.product_service import ProductService
from app.services.product_repository import ProductRepository
from app.services import product_filters


def candidates(products):
    return sorted((p for p in products if float(p.get("dark_horse_index") or 0) >= 4),
                  key=lambda p: (str(p.get("discovered_at") or ""), float(p.get("dark_horse_index") or 0)), reverse=True)


def load_candidates(snapshot=None):
    if snapshot:
        # Keep MongoDB enabled for the shared budget/cache, but read this run's
        # unpublished catalog rather than yesterday's live product collection.
        products = json.loads(Path(snapshot).read_text(encoding="utf-8"))
        products = ProductRepository._dedupe_products(product_filters.normalize_products(products), product_filters)
        products = ProductService.filter_discovery_products(products)
    else:
        products = ProductService.get_discovery_products()
    return candidates(products)


def export(entry):
    for folder in (ROOT / "backend/data/demos", ROOT / "crawler/data/demos"):
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / (entry["cache_key"] + ".json")
        text = json.dumps(entry, ensure_ascii=False, indent=2) + "\n"
        if target.exists() and target.read_text(encoding="utf-8") == text:
            continue
        temp = target.with_suffix(".tmp")
        temp.write_text(text, encoding="utf-8")
        temp.replace(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=env_int("DEMO_PREGENERATE_LIMIT", 5))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--product")
    parser.add_argument("--snapshot", type=Path, help="Prepare this catalog before its MongoDB publication")
    args = parser.parse_args()
    if not 0 <= args.limit <= 20:
        parser.error("--limit must be between 0 and 20")
    if args.limit == 0:
        return
    # CI must share the deployment's database budget; ephemeral CI SQLite resets daily.
    if os.getenv("CI") and not os.getenv("MONGO_URI") and not args.dry_run:
        print("Skipped: configure MONGO_URI for the shared generation budget.")
        return
    store = None if args.dry_run else DemoStore()
    products = load_candidates(args.snapshot)
    if args.product:
        products = [p for p in products if p["name"].casefold() == args.product.casefold() or str(p.get("_id")) == args.product]
    attempts = generated = cached = 0
    for product in products:
        ready = ready_experience(product, store)
        if ready:
            if not args.dry_run:
                export(ready)
            cached += 1
            continue
        if attempts >= args.limit:
            break
        if args.dry_run:
            print("Would generate:", product["name"])
            attempts += 1
            continue
        if not provider_available():
            print("Skipped: no model provider configured.")
            break
        attempts += 1
        result, status = prepare_experience(product, "daily-pregeneration", store, user_limit=args.limit, origin="pregenerated")
        if status == 200:
            export(result["experience"])
            generated += 1
            print("Prepared:", product["name"])
        else:
            print("Deferred:", product["name"], result.get("error") or result.get("state"))
        if status == 429:
            break
    print(json.dumps({"attempts": attempts, "prepared": generated, "cached": cached, "dry_run": args.dry_run}))


if __name__ == "__main__":
    main()
