#!/usr/bin/env python3
"""
Backfill English product text fields for crawler/data/products_featured.json.

Usage:
  python tools/backfill_product_en_fields.py --dry-run
  python tools/backfill_product_en_fields.py --provider auto --batch-size 8
  python tools/backfill_product_en_fields.py --fields description,why_matters --limit 100
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Sequence
from urllib.parse import quote

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency in some environments
    load_dotenv = None

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products_featured.json")
sys.path.insert(0, PROJECT_ROOT)

SUPPORTED_FIELDS = ("description", "why_matters", "latest_news")
DEFAULT_FIELDS = ("description", "why_matters", "latest_news")
TRANSLATE_PUBLIC_URL = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q="
TRANSLATE_TIMEOUT_SECONDS = float(os.getenv("PUBLIC_TRANSLATE_TIMEOUT_SECONDS", "6"))


def _load_env() -> None:
    env_files = [os.path.join(REPO_ROOT, ".env"), os.path.join(PROJECT_ROOT, ".env")]

    if load_dotenv is not None:
        for env_file in env_files:
            load_dotenv(env_file)
        return

    for env_file in env_files:
        _load_env_fallback(env_file)


def _load_env_fallback(path: str) -> None:
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        return


def _load_json(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path: str, payload: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _chunked(items: Sequence[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    for start in range(0, len(items), size):
        yield list(items[start : start + size])


def _parse_fields(raw: str) -> List[str]:
    tokens = [part.strip() for part in str(raw or "").split(",") if part.strip()]
    if not tokens:
        return list(DEFAULT_FIELDS)
    invalid = [token for token in tokens if token not in SUPPORTED_FIELDS]
    if invalid:
        raise ValueError(f"Unsupported fields: {', '.join(invalid)} (supported: {', '.join(SUPPORTED_FIELDS)})")
    deduped: List[str] = []
    for token in tokens:
        if token not in deduped:
            deduped.append(token)
    return deduped


def _pick_available_provider(provider: str) -> str:
    provider = (provider or "local").strip().lower()
    if provider == "local":
        return "local"
    has_glm = bool(os.getenv("ZHIPU_API_KEY", "").strip())
    has_perplexity = bool(os.getenv("PERPLEXITY_API_KEY", "").strip())

    if provider == "auto":
        if has_perplexity:
            return "perplexity"
        if has_glm:
            return "glm"
        return "local"

    if provider == "glm":
        return "glm" if has_glm else "none"
    if provider == "perplexity":
        return "perplexity" if has_perplexity else "none"
    return "none"


def _build_translation_prompt(batch: Sequence[Dict[str, Any]], fields: Sequence[str]) -> str:
    payload: List[Dict[str, Any]] = []
    for item in batch:
        source = {"index": item["index"], "name": _normalize_text(item.get("name"))}
        for field in fields:
            text = _normalize_text(item.get(field))
            if text:
                source[field] = text
        payload.append(source)

    requested = ", ".join(f"{field}_en" for field in fields)
    payload_json = json.dumps(payload, ensure_ascii=False, indent=2)
    return f"""You are a strict translation engine for AI product metadata.

Translate Chinese product fields into fluent professional English.

INPUT JSON:
{payload_json}

RULES:
1. Keep product names, companies, model names, and URLs unchanged.
2. Preserve numbers, currencies, and dates exactly.
3. Output must be pure JSON array (no markdown, no explanation).
4. Preserve each `index` from input.
5. For each item, only include translated keys that were present in input.
6. Output keys must be: {requested}
7. If a source field is empty/missing, omit its translated key.

OUTPUT FORMAT:
[
  {{
    "index": 0,
    "{fields[0]}_en": "..."
  }}
]
"""


def _extract_translation_items(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        maybe_items = payload.get("items")
        if isinstance(maybe_items, list):
            return [item for item in maybe_items if isinstance(item, dict)]
        return [payload]
    return []


def _create_client(provider: str):
    if provider == "local":
        return object()
    if provider == "glm":
        try:
            from utils.glm_client import GLMClient  # noqa: WPS433
        except Exception as error:
            print(f"⚠ GLM client is unavailable: {error}")
            return None

        try:
            client = GLMClient()
            return client if client.is_available() else None
        except Exception as error:
            print(f"⚠ GLM client init failed: {error}")
            return None
    if provider == "perplexity":
        try:
            from utils.perplexity_client import PerplexityClient  # noqa: WPS433
        except Exception as error:
            print(f"⚠ Perplexity client is unavailable: {error}")
            return None

        try:
            client = PerplexityClient()
            return client if client.is_available() else None
        except Exception as error:
            print(f"⚠ Perplexity client init failed: {error}")
            return None
    return None


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _translate_public(text: str) -> str:
    text = _normalize_text(text)
    if not text:
        return ""
    if not _contains_cjk(text):
        return text

    try:
        import requests  # noqa: WPS433
    except Exception:
        return text

    url = f"{TRANSLATE_PUBLIC_URL}{quote(text)}"
    try:
        response = requests.get(url, timeout=max(1.0, TRANSLATE_TIMEOUT_SECONDS))
        response.raise_for_status()
        payload = response.json()
        parts = payload[0] if isinstance(payload, list) and payload else []
        translated = "".join(str(part[0]) for part in parts if isinstance(part, list) and part and part[0])
        return _normalize_text(translated) or text
    except Exception:
        return text


def _translate_batch(
    client: Any,
    provider: str,
    batch: Sequence[Dict[str, Any]],
    fields: Sequence[str],
    local_cache: Dict[str, str] | None = None,
) -> Dict[int, Dict[str, str]]:
    if provider == "local":
        cache = local_cache if isinstance(local_cache, dict) else {}
        output: Dict[int, Dict[str, str]] = {}
        for item in batch:
            index = int(item["index"])
            translated: Dict[str, str] = {}
            for field in fields:
                source_text = _normalize_text(item.get(field))
                if not source_text:
                    continue
                if source_text not in cache:
                    cache[source_text] = _translate_public(source_text)
                    time.sleep(0.01)
                target = _normalize_text(cache[source_text])
                if target:
                    translated[f"{field}_en"] = target
            if translated:
                output[index] = translated
        return output

    prompt = _build_translation_prompt(batch, fields)
    if provider == "glm":
        parsed = client.analyze(prompt, temperature=0.15, max_tokens=4096)
    else:
        parsed = client.analyze(prompt, temperature=0.15, max_tokens=4096)

    results: Dict[int, Dict[str, str]] = {}
    for item in _extract_translation_items(parsed):
        try:
            index = int(item.get("index"))
        except Exception:
            continue

        translated: Dict[str, str] = {}
        for field in fields:
            key = f"{field}_en"
            value = _normalize_text(item.get(key))
            if value:
                translated[key] = value
        if translated:
            results[index] = translated
    return results


def _candidate_fields(product: Dict[str, Any], fields: Sequence[str], only_missing: bool) -> List[str]:
    selected: List[str] = []
    for field in fields:
        src = _normalize_text(product.get(field))
        if not src:
            continue
        target_key = f"{field}_en"
        target = _normalize_text(product.get(target_key))
        if only_missing and target:
            continue
        selected.append(field)
    return selected


def _coverage(products: Sequence[Dict[str, Any]], fields: Sequence[str]) -> Dict[str, float]:
    total = max(1, len(products))
    rates: Dict[str, float] = {}
    for field in fields:
        key = f"{field}_en"
        filled = sum(1 for product in products if _normalize_text(product.get(key)))
        rates[key] = filled / total
    return rates


def _format_coverage(rates: Dict[str, float]) -> str:
    return ", ".join(f"{key}={value * 100:.1f}%" for key, value in rates.items())


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill English fields for products_featured.json")
    parser.add_argument("--input", default=PRODUCTS_FILE, help="Input JSON file path")
    parser.add_argument("--provider", choices=["local", "auto", "glm", "perplexity"], default="local", help="Translation provider")
    parser.add_argument("--dry-run", action="store_true", help="Preview only; do not call provider or write file")
    parser.add_argument("--limit", type=int, default=0, help="Max products to process (0 = all)")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size for translation requests")
    parser.add_argument("--fields", default="description,why_matters,latest_news", help="Comma-separated source fields")
    parser.add_argument("--only-missing", action="store_true", default=True, help="Only fill missing *_en fields")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing *_en fields")
    args = parser.parse_args()

    _load_env()

    fields = _parse_fields(args.fields)
    only_missing = bool(args.only_missing) and not args.overwrite
    products = _load_json(args.input, [])
    if not isinstance(products, list):
        print(f"✗ Invalid JSON structure in {args.input} (expected array)")
        return 1

    before_rates = _coverage(products, fields)

    candidates: List[Dict[str, Any]] = []
    for idx, product in enumerate(products):
        if not isinstance(product, dict):
            continue
        selected = _candidate_fields(product, fields, only_missing=only_missing)
        if not selected:
            continue
        item = {"index": idx, "name": product.get("name", "")}
        for field in selected:
            item[field] = product.get(field)
        candidates.append(item)

    if args.limit and args.limit > 0:
        candidates = candidates[: args.limit]

    print(f"Products loaded: {len(products)}")
    print(f"Candidates: {len(candidates)} (fields: {', '.join(fields)}, only_missing={only_missing})")
    print(f"Coverage before: {_format_coverage(before_rates)}")

    if args.dry_run:
        print("Dry run mode: no provider calls, no file writes.")
        return 0

    if not candidates:
        print("No candidates to process.")
        return 0

    provider = _pick_available_provider(args.provider)
    if provider == "none":
        print("⚠ No available translation provider (missing API keys). Skipping without changes.")
        return 0

    client = _create_client(provider)
    if client is None:
        print(f"⚠ Provider '{provider}' is not available in this environment. Skipping without changes.")
        return 0

    updated_fields = 0
    updated_products = 0
    failed_batches = 0
    local_cache: Dict[str, str] = {}

    batch_size = max(1, int(args.batch_size or 1))
    total_batches = (len(candidates) + batch_size - 1) // batch_size
    for batch_idx, batch in enumerate(_chunked(candidates, batch_size), start=1):
        print(f"  … Batch {batch_idx}/{total_batches}: processing {len(batch)} items")
        translated = _translate_batch(client, provider, batch, fields, local_cache=local_cache)
        if not translated:
            failed_batches += 1
            print(f"  ⚠ Batch {batch_idx}: no translations returned")
            continue

        batch_product_updates = 0
        for item in batch:
            index = item["index"]
            result = translated.get(index, {})
            if not result:
                continue
            product = products[index]
            changed = False
            for field in fields:
                target_key = f"{field}_en"
                source_text = _normalize_text(product.get(field))
                if not source_text:
                    continue
                translated_text = _normalize_text(result.get(target_key))
                if not translated_text:
                    continue
                if only_missing and _normalize_text(product.get(target_key)):
                    continue
                if _normalize_text(product.get(target_key)) != translated_text:
                    product[target_key] = translated_text
                    updated_fields += 1
                    changed = True
            if changed:
                batch_product_updates += 1
        updated_products += batch_product_updates
        print(f"  ✓ Batch {batch_idx}: updated_products={batch_product_updates}")

    if updated_fields > 0:
        _save_json(args.input, products)
        print(f"Saved: {args.input}")
    else:
        print("No field updates were applied.")

    after_rates = _coverage(products, fields)
    print(f"Coverage after: {_format_coverage(after_rates)}")
    print(
        "Summary: "
        f"provider={provider}, updated_products={updated_products}, "
        f"updated_fields={updated_fields}, failed_batches={failed_batches}, "
        f"timestamp={datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
