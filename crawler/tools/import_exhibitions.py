import argparse
import json
import os
import time
from typing import Any, Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

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


def load_sources(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("Sources file must contain a JSON list")
    return data


def extract_exhibitors(html: str, source: Dict[str, Any]) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    selector = source.get("item_selector")
    items = soup.select(selector) if selector else soup.select("a")

    name_attr = source.get("name_attr", "text")
    url_attr = source.get("url_attr", "href")
    base_url = source.get("base_url") or source.get("list_url")

    exhibitors = []
    for item in items:
        name = item.get_text(strip=True) if name_attr == "text" else item.get(name_attr)
        url = item.get(url_attr)
        if not name:
            continue
        name = name.strip()
        if len(name) < 2:
            continue
        if url and base_url:
            url = urljoin(base_url, url)
        exhibitors.append({"name": name, "website": url or ""})

    return exhibitors


def build_entry(
    exhibitor: Dict[str, str],
    source: Dict[str, Any],
    fetch_site: bool,
    llm_settings,
) -> Dict[str, Any]:
    name = exhibitor["name"]
    website = exhibitor.get("website", "")
    description = ""
    categories = []

    if fetch_site and website:
        try:
            html = fetch_url(website)
            description = extract_meta_description(html)
            text = extract_text(html)
            categories = infer_categories(text)
            if llm_settings:
                prompt = (
                    "Summarize the exhibitor in one sentence and infer categories. "
                    "Return JSON with keys description and categories (array). "
                    f"Name: {name}\nWebsite: {website}\nText: {text[:1200]}"
                )
                llm_data = request_llm_json(prompt, llm_settings) or {}
                if isinstance(llm_data, dict):
                    description = llm_data.get("description", description)
                    categories = llm_data.get("categories", categories)
        except Exception:
            description = description or ""

    categories = normalize_categories(categories)
    status = source.get("status", "pending")
    event = source.get("event", "Event")
    year = source.get("year")

    return {
        "status": status,
        "name": name,
        "brand": name,
        "description": description,
        "website": website,
        "logo_url": logo_url_for_site(website),
        "categories": categories,
        "event": event,
        "event_year": year,
        "release_year": year,
        "press_url": "",
    }


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Import exhibition exhibitors into JSON files")
    parser.add_argument(
        "--sources",
        default=os.path.join("crawler", "data", "exhibitions", "sources.json"),
        help="Path to sources JSON",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join("crawler", "data", "exhibitions"),
        help="Output directory",
    )
    parser.add_argument("--limit", type=int, default=0, help="Limit exhibitors per source")
    parser.add_argument("--sleep", type=float, default=0.0, help="Sleep seconds between requests")
    parser.add_argument("--fetch-site", action="store_true", help="Fetch exhibitor website for descriptions")
    parser.add_argument("--provider", default="", help="LLM provider: openai or anthropic")
    parser.add_argument("--model", default="", help="LLM model override")
    args = parser.parse_args()

    sources = load_sources(args.sources)
    llm_settings = get_llm_settings(args.provider or None, args.model or None)

    os.makedirs(args.output_dir, exist_ok=True)

    for source in sources:
        list_url = source.get("list_url")
        if not list_url:
            continue
        html = fetch_url(list_url)
        exhibitors = extract_exhibitors(html, source)
        if args.limit:
            exhibitors = exhibitors[: args.limit]

        entries = []
        for exhibitor in exhibitors:
            entries.append(build_entry(exhibitor, source, args.fetch_site, llm_settings))
            if args.sleep:
                time.sleep(args.sleep)

        slug = slugify(source.get("event", "event"))
        output_path = os.path.join(args.output_dir, f"{slug}.json")
        existing = load_existing(output_path)
        merged = dedupe_by_name(existing + entries)
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(merged, handle, ensure_ascii=False, indent=2)

        print(f"Saved {len(merged)} entries -> {output_path}")


if __name__ == "__main__":
    main()
