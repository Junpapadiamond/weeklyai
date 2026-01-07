import argparse
import json
import os
import time
from typing import Any, Dict, List

from import_helpers import (
    dedupe_by_name,
    extract_meta_description,
    extract_text,
    fetch_url,
    get_llm_settings,
    infer_categories,
    logo_url_for_site,
    normalize_categories,
    request_llm_json,
    slugify,
)


def load_seeds(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("Seeds file must contain a JSON list")
    return data


def load_existing(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            return data
    except Exception:
        return []
    return []


def build_entries(
    seed: Dict[str, Any],
    llm_settings,
    max_products: int,
    fetch_site: bool,
) -> List[Dict[str, Any]]:
    company = seed.get("name", "").strip()
    website = seed.get("website", "")
    press_url = seed.get("press_url", "")
    status = seed.get("status", "pending")
    release_year = seed.get("release_year")
    logo_url = seed.get("logo_url") or logo_url_for_site(website)

    description = ""
    categories = []
    text = ""

    if fetch_site and website:
        try:
            html = fetch_url(website)
            description = extract_meta_description(html)
            text = extract_text(html)
            categories = infer_categories(text)
        except Exception:
            description = description or ""

    entries: List[Dict[str, Any]] = []
    if llm_settings and text:
        prompt = (
            "Extract up to {max_products} AI-related products or offerings from the company. "
            "Return a JSON array of objects with keys: name, description, categories (array), "
            "website (optional), press_url (optional), release_year (optional). "
            f"Company: {company}\nWebsite: {website}\nText: {text[:1400]}"
        ).format(max_products=max_products)
        llm_data = request_llm_json(prompt, llm_settings)
        if isinstance(llm_data, list):
            for item in llm_data[:max_products]:
                if not isinstance(item, dict):
                    continue
                name = (item.get("name") or "").strip()
                if not name:
                    continue
                entry = {
                    "status": status,
                    "name": name,
                    "brand": company,
                    "description": item.get("description") or description,
                    "website": item.get("website") or website,
                    "logo_url": logo_url,
                    "categories": normalize_categories(item.get("categories") or categories),
                    "release_year": item.get("release_year") or release_year,
                    "press_url": item.get("press_url") or press_url,
                }
                entries.append(entry)

    if not entries:
        entries.append(
            {
                "status": status,
                "name": f"{company} AI Product (fill in)",
                "brand": company,
                "description": description or "TODO: add official product or press kit summary.",
                "website": website,
                "logo_url": logo_url,
                "categories": normalize_categories(categories),
                "release_year": release_year,
                "press_url": press_url,
            }
        )

    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description="Import company products from seed list")
    parser.add_argument(
        "--seeds",
        default=os.path.join("crawler", "data", "companies", "seeds.json"),
        help="Path to company seed JSON",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join("crawler", "data", "companies"),
        help="Output directory",
    )
    parser.add_argument("--max-products", type=int, default=3, help="Max products per company")
    parser.add_argument("--sleep", type=float, default=0.0, help="Sleep seconds between requests")
    parser.add_argument("--fetch-site", action="store_true", help="Fetch company website for context")
    parser.add_argument("--provider", default="", help="LLM provider: openai or anthropic")
    parser.add_argument("--model", default="", help="LLM model override")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing company files")
    args = parser.parse_args()

    seeds = load_seeds(args.seeds)
    llm_settings = get_llm_settings(args.provider or None, args.model or None)

    os.makedirs(args.output_dir, exist_ok=True)

    for seed in seeds:
        company = seed.get("name", "").strip()
        if not company:
            continue
        entries = build_entries(seed, llm_settings, args.max_products, args.fetch_site)
        slug = slugify(company)
        output_path = os.path.join(args.output_dir, f"{slug}.json")

        if not args.overwrite:
            existing = load_existing(output_path)
            entries = dedupe_by_name(existing + entries)

        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(entries, handle, ensure_ascii=False, indent=2)

        print(f"Saved {len(entries)} entries -> {output_path}")

        if args.sleep:
            time.sleep(args.sleep)


if __name__ == "__main__":
    main()
