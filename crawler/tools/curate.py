#!/usr/bin/env python3
"""
WeeklyAI v2 editorial gate.

Review pending candidates one by one and promote only the product that passes
the editor's taste test.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CANDIDATES_DIR = os.path.join(DATA_DIR, "candidates")
PENDING_FILE = os.path.join(CANDIDATES_DIR, "pending_review.json")
FEATURED_FILE = os.path.join(DATA_DIR, "products_featured.json")
APPROVED_ARCHIVE_FILE = os.path.join(CANDIDATES_DIR, "curated_archive.json")
REJECTED_ARCHIVE_FILE = os.path.join(CANDIDATES_DIR, "rejected_archive.json")

VALID_HOOKS = {
    "weird_form",
    "new_behavior",
    "unexpected_combo",
    "quiet_real_problem",
    "new_interaction",
    "niche_depth",
}


def load_json(path: str) -> list:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_json(path: str, payload: list) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def normalize_domain(url: str) -> str:
    raw = str(url or "").strip()
    if not raw or raw.lower() == "unknown":
        return ""
    if not raw.startswith(("http://", "https://")):
        raw = f"https://{raw}"
    try:
        host = (urlparse(raw).netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return host.split(":")[0]
    except Exception:
        return raw.lower()


def normalize_name(value: str) -> str:
    return "".join(ch for ch in str(value or "").lower() if ch.isalnum())


def product_exists(featured: list, product: dict) -> bool:
    domain = normalize_domain(product.get("website", ""))
    name = normalize_name(product.get("name", ""))
    for item in featured:
        if domain and normalize_domain(item.get("website", "")) == domain:
            return True
        if name and normalize_name(item.get("name", "")) == name:
            return True
    return False


def coerce_categories(product: dict) -> list:
    categories = product.get("categories")
    if isinstance(categories, str):
        return [categories]
    if isinstance(categories, list) and categories:
        return categories
    category = product.get("category")
    return [category] if category else ["other"]


def infer_has_strong_image(product: dict) -> bool:
    image = (
        product.get("image_url")
        or product.get("cover_image")
        or product.get("hero_image")
        or product.get("og_image")
        or product.get("logo_url")
        or product.get("logo")
        or ""
    )
    return bool(str(image).strip())


def prepare_for_featured(candidate: dict) -> dict:
    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    product = {k: v for k, v in candidate.items() if not str(k).startswith("_")}
    product["screenshot_worthy"] = True
    hook = str(product.get("hook") or "").strip()
    if hook not in VALID_HOOKS:
        product["hook"] = "quiet_real_problem"
    product["categories"] = coerce_categories(product)
    product.setdefault("source", "curated")
    product.setdefault("first_seen", now_iso)
    product["last_seen"] = now_iso
    product["curated_at"] = now_iso
    product["has_strong_image"] = bool(product.get("has_strong_image", infer_has_strong_image(product)))
    product.setdefault("dark_horse_index", 4)
    product.setdefault("criteria_met", [product["hook"]])
    product.setdefault("final_score", product.get("dark_horse_index", 4) * 20)
    product.setdefault("trending_score", product.get("dark_horse_index", 4) * 18)
    product.setdefault("hot_score", product.get("final_score", 80))
    return product


def display_candidate(candidate: dict, index: int, total: int) -> None:
    print("\n" + "=" * 72)
    print(f"[{index + 1}/{total}] {candidate.get('name', 'Unknown')}")
    print("-" * 72)
    print(f"website:    {candidate.get('website', '')}")
    print(f"hook:       {candidate.get('hook', '')}")
    print(f"why:        {candidate.get('why_matters', '')}")
    print(f"image:      {candidate.get('image_url') or candidate.get('cover_image') or candidate.get('logo_url') or candidate.get('logo') or ''}")
    print(f"source:     {candidate.get('source_url', '')}")
    print(f"discovered: {candidate.get('discovered_at') or candidate.get('first_seen') or ''}")
    print("=" * 72)
    print("y promote  n archive  s skip  q quit")


def archive_item(path: str, candidate: dict, status: str) -> None:
    archive = load_json(path)
    item = dict(candidate)
    item["_curation_status"] = status
    item["_curated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    archive.insert(0, item)
    save_json(path, archive)


def choose_action(non_interactive: str = "") -> str:
    if non_interactive:
        return non_interactive
    while True:
        choice = input("> ").strip().lower()
        if choice in {"y", "n", "s", "q"}:
            return choice
        print("Use y, n, s, or q.")


def curate(limit: int = 0, dry_run: bool = False, action: str = "") -> int:
    pending = load_json(PENDING_FILE)
    featured = load_json(FEATURED_FILE)
    if not pending:
        print("No pending candidates.")
        return 0

    reviewed = 0
    remaining = list(pending)
    max_items = limit if limit > 0 else len(pending)

    for candidate in pending[:max_items]:
        try:
            idx = remaining.index(candidate)
        except ValueError:
            continue
        display_candidate(candidate, reviewed, len(pending))
        selected = choose_action(action)
        reviewed += 1

        if selected == "q":
            break
        if selected == "s":
            continue
        if selected == "n":
            if not dry_run:
                archive_item(REJECTED_ARCHIVE_FILE, candidate, "rejected")
                remaining.pop(idx)
                save_json(PENDING_FILE, remaining)
            print(f"Archived: {candidate.get('name')}")
            continue
        if selected == "y":
            product = prepare_for_featured(candidate)
            if product_exists(featured, product):
                print(f"Already featured: {candidate.get('name')}")
            elif dry_run:
                print(f"[DRY RUN] Would promote: {candidate.get('name')}")
            else:
                featured.insert(0, product)
                save_json(FEATURED_FILE, featured)
                archive_item(APPROVED_ARCHIVE_FILE, candidate, "approved")
                remaining.pop(idx)
                save_json(PENDING_FILE, remaining)
                print(f"Promoted: {candidate.get('name')}")

    print(f"\nReviewed {reviewed} candidate(s). Remaining: {len(remaining)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Review WeeklyAI v2 candidates with y/n/s/q.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum candidates to review")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files")
    parser.add_argument("--yes-first", action="store_true", help="Promote the first candidate non-interactively")
    parser.add_argument("--reject-first", action="store_true", help="Reject the first candidate non-interactively")
    args = parser.parse_args()

    action = ""
    limit = args.limit
    if args.yes_first:
        action = "y"
        limit = 1
    elif args.reject_first:
        action = "n"
        limit = 1

    return curate(limit=limit, dry_run=args.dry_run, action=action)


if __name__ == "__main__":
    raise SystemExit(main())
