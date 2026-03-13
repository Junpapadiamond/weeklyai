#!/usr/bin/env python3
"""
Backfill zh-CN primary display fields for products/blogs data files.

Goals:
- Keep primary display fields Chinese-first for zh locale.
- Preserve original non-Chinese text in *_en fields when missing.
- Support provider fallback: GLM/Perplexity -> public translate API.

Usage:
  python tools/backfill_primary_zh_fields.py --dry-run
  python tools/backfill_primary_zh_fields.py --targets products,blogs --provider auto
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
except Exception:  # pragma: no cover
    load_dotenv = None

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products_featured.json")
BLOGS_FILE = os.path.join(DATA_DIR, "blogs_news.json")
sys.path.insert(0, PROJECT_ROOT)

SUPPORTED_TARGETS = ("products", "blogs")
TARGET_FIELD_SPECS: Dict[str, Sequence[tuple[str, str]]] = {
    "products": (
        ("description", "description_en"),
        ("why_matters", "why_matters_en"),
        ("latest_news", "latest_news_en"),
    ),
    "blogs": (
        ("name", "name_en"),
        ("description", "description_en"),
    ),
}

PLACEHOLDER_VALUES = {
    "unknown",
    "n/a",
    "na",
    "none",
    "null",
    "undefined",
    "tbd",
    "暂无",
    "待定",
    "未公开",
}

TRANSLATE_PUBLIC_URL = (
    "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=zh-CN&dt=t&q="
)
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


def _is_placeholder(value: str) -> bool:
    normalized = _normalize_text(value).lower()
    if not normalized:
        return True
    return normalized in PLACEHOLDER_VALUES


def _contains_han(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _contains_kana(text: str) -> bool:
    for ch in text:
        code = ord(ch)
        if 0x3040 <= code <= 0x30FF:
            return True
    return False


def _contains_non_ascii_script(text: str) -> bool:
    for ch in text:
        if ord(ch) > 127:
            return True
    return False


def _needs_zh_translation(text: str) -> bool:
    normalized = _normalize_text(text)
    if _is_placeholder(normalized):
        return False
    if _contains_kana(normalized):
        return True
    if _contains_han(normalized):
        return False
    # Catch full English / Japanese / other non-zh scripts.
    return bool(normalized) and (_contains_non_ascii_script(normalized) or any(c.isalpha() for c in normalized))


def _chunked(items: Sequence[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    for start in range(0, len(items), size):
        yield list(items[start : start + size])


def _parse_targets(raw: str) -> List[str]:
    tokens = [part.strip() for part in str(raw or "").split(",") if part.strip()]
    if not tokens or "all" in tokens:
        return list(SUPPORTED_TARGETS)
    invalid = [token for token in tokens if token not in SUPPORTED_TARGETS]
    if invalid:
        raise ValueError(f"Unsupported targets: {', '.join(invalid)} (supported: {', '.join(SUPPORTED_TARGETS)})")
    ordered: List[str] = []
    for token in tokens:
        if token not in ordered:
            ordered.append(token)
    return ordered


def _pick_available_provider(provider: str) -> str:
    selected = (provider or "auto").strip().lower()
    has_glm = bool(os.getenv("ZHIPU_API_KEY", "").strip())
    has_perplexity = bool(os.getenv("PERPLEXITY_API_KEY", "").strip())

    if selected == "auto":
        if has_glm:
            return "glm"
        if has_perplexity:
            return "perplexity"
        return "local"
    if selected == "glm":
        return "glm" if has_glm else "local"
    if selected == "perplexity":
        return "perplexity" if has_perplexity else "local"
    return "local"


def _create_client(provider: str):
    if provider == "local":
        return object()
    if provider == "glm":
        try:
            from utils.glm_client import GLMClient  # noqa: WPS433
        except Exception as error:
            print(f"⚠ GLM client unavailable ({error}), fallback to local translate")
            return None
        try:
            client = GLMClient()
            if client.is_available():
                return client
        except Exception as error:
            print(f"⚠ GLM client init failed ({error}), fallback to local translate")
        return None
    if provider == "perplexity":
        try:
            from utils.perplexity_client import PerplexityClient  # noqa: WPS433
        except Exception as error:
            print(f"⚠ Perplexity client unavailable ({error}), fallback to local translate")
            return None
        try:
            client = PerplexityClient()
            if client.is_available():
                return client
        except Exception as error:
            print(f"⚠ Perplexity client init failed ({error}), fallback to local translate")
        return None
    return None


def _build_translation_prompt(batch: Sequence[Dict[str, Any]], target: str) -> str:
    payload_json = json.dumps(batch, ensure_ascii=False, indent=2)
    return f"""You are a strict translation engine for WeeklyAI metadata.

Translate each `text` into natural Simplified Chinese for zh-CN display cards.

Rules:
1. Keep product/company/model names unchanged.
2. Keep numbers, currencies, percentages, and dates exactly unchanged.
3. Keep key technical terms in English when helpful (e.g. LLM, API, GPU, Agent).
4. Do not add facts, do not summarize, do not omit key details.
5. Return pure JSON array only, no markdown.
6. Output format for each item: {{"id": <id>, "translated": "<zh text>"}}
7. Target dataset: {target}

INPUT:
{payload_json}
"""


def _extract_translation_items(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        items = payload.get("items")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
        return [payload]
    return []


def _translate_public(text: str) -> str:
    source = _normalize_text(text)
    if not source:
        return ""
    # Pure Chinese text should not be sent for translation.
    # Japanese often mixes Kanji (Han) + Kana, so do not short-circuit when Kana exists.
    if _contains_han(source) and not _contains_kana(source):
        return source

    url = f"{TRANSLATE_PUBLIC_URL}{quote(source)}"
    try:
        import requests  # noqa: WPS433

        response = requests.get(url, timeout=max(1.0, TRANSLATE_TIMEOUT_SECONDS))
        response.raise_for_status()
        payload = response.json()
        parts = payload[0] if isinstance(payload, list) and payload else []
        translated = "".join(
            str(part[0]) for part in parts if isinstance(part, list) and part and part[0]
        )
        return _normalize_text(translated) or source
    except Exception:
        pass

    try:
        from urllib.request import urlopen  # noqa: WPS433

        with urlopen(url, timeout=max(1.0, TRANSLATE_TIMEOUT_SECONDS)) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        parts = payload[0] if isinstance(payload, list) and payload else []
        translated = "".join(
            str(part[0]) for part in parts if isinstance(part, list) and part and part[0]
        )
        return _normalize_text(translated) or source
    except Exception:
        return source


def _translate_batch(
    provider: str,
    client: Any,
    batch: Sequence[Dict[str, Any]],
    target: str,
    local_cache: Dict[str, str] | None = None,
) -> Dict[int, str]:
    if provider == "local":
        cache = local_cache if isinstance(local_cache, dict) else {}
        output: Dict[int, str] = {}
        for item in batch:
            text = _normalize_text(item.get("text"))
            if not text:
                continue
            if text not in cache:
                cache[text] = _translate_public(text)
                time.sleep(0.01)
            translated = _normalize_text(cache[text])
            if translated:
                output[int(item["id"])] = translated
        return output

    prompt = _build_translation_prompt(batch, target=target)
    parsed = client.analyze(prompt, temperature=0.1, max_tokens=4096)
    result: Dict[int, str] = {}
    for item in _extract_translation_items(parsed):
        try:
            item_id = int(item.get("id"))
        except Exception:
            continue
        translated = _normalize_text(item.get("translated"))
        if translated:
            result[item_id] = translated
    return result


def _collect_work_items(
    records: Sequence[Dict[str, Any]],
    *,
    target: str,
    overwrite_en: bool = False,
) -> tuple[List[Dict[str, Any]], int, int, int]:
    specs = TARGET_FIELD_SPECS[target]
    work_items: List[Dict[str, Any]] = []
    preserved_en_fields = 0
    skipped_fields = 0
    scanned_fields = 0

    for idx, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        item_name = _normalize_text(record.get("name"))
        for field, en_field in specs:
            source = _normalize_text(record.get(field))
            if not source:
                continue
            scanned_fields += 1
            should_translate = _needs_zh_translation(source)
            existing_en = _normalize_text(record.get(en_field))
            if should_translate and (overwrite_en or not existing_en):
                record[en_field] = source
                preserved_en_fields += 1

            if not should_translate:
                skipped_fields += 1
                continue

            work_items.append(
                {
                    "id": len(work_items),
                    "index": idx,
                    "field": field,
                    "text": source,
                    "name": item_name,
                }
            )
    return work_items, preserved_en_fields, skipped_fields, scanned_fields


def _apply_translations(
    records: Sequence[Dict[str, Any]],
    work_items: Sequence[Dict[str, Any]],
    translated: Dict[int, str],
) -> tuple[int, int]:
    updated_fields = 0
    failed_fields = 0

    for item in work_items:
        item_id = int(item["id"])
        source = _normalize_text(item.get("text"))
        target = _normalize_text(translated.get(item_id))
        if not target or target == source or not _contains_han(target):
            failed_fields += 1
            continue
        index = int(item["index"])
        field = str(item["field"])
        record = records[index]
        if _normalize_text(record.get(field)) != target:
            record[field] = target
            updated_fields += 1
    return updated_fields, failed_fields


def _collect_residual_samples(
    records: Sequence[Dict[str, Any]],
    *,
    target: str,
    limit: int = 8,
) -> tuple[int, List[Dict[str, str]]]:
    specs = TARGET_FIELD_SPECS[target]
    total = 0
    samples: List[Dict[str, str]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        name = _normalize_text(record.get("name"))
        for field, _ in specs:
            value = _normalize_text(record.get(field))
            if not value:
                continue
            if not _needs_zh_translation(value):
                continue
            total += 1
            if len(samples) < limit:
                samples.append({"name": name or "<unnamed>", "field": field, "text": value[:140]})
    return total, samples


def _process_target(
    *,
    target: str,
    input_path: str,
    provider: str,
    client: Any,
    batch_size: int,
    dry_run: bool,
    residual_limit: int,
    overwrite_en: bool,
) -> Dict[str, Any]:
    payload = _load_json(input_path, [])
    if not isinstance(payload, list):
        print(f"✗ {target}: invalid root in {input_path} (expected JSON array)")
        return {"target": target, "error": "invalid_json_root"}

    records = [item for item in payload if isinstance(item, dict)]
    work_items, preserved_en, skipped_fields, scanned_fields = _collect_work_items(
        records,
        target=target,
        overwrite_en=overwrite_en,
    )

    print(f"\n[{target}] file={input_path}")
    print(
        f"  records={len(records)}, scanned_fields={scanned_fields}, "
        f"candidates={len(work_items)}, preserved_en={preserved_en}, skipped={skipped_fields}"
    )

    if dry_run:
        residual_count, residual_samples = _collect_residual_samples(records, target=target, limit=residual_limit)
        print("  dry-run: no translation calls and no writes")
        print(f"  residual_non_zh={residual_count}")
        for sample in residual_samples:
            print(f"    - {sample['name']} [{sample['field']}] {sample['text']}")
        return {
            "target": target,
            "records": len(records),
            "scanned_fields": scanned_fields,
            "candidate_fields": len(work_items),
            "preserved_en": preserved_en,
            "translated_fields": 0,
            "failed_fields": 0,
            "residual_non_zh": residual_count,
            "saved": False,
        }

    translated_fields = 0
    failed_fields = 0
    local_cache: Dict[str, str] = {}
    total_batches = (len(work_items) + batch_size - 1) // batch_size if work_items else 0

    for batch_idx, batch in enumerate(_chunked(work_items, max(1, batch_size)), start=1):
        print(f"  … batch {batch_idx}/{total_batches}: {len(batch)} items")
        translated_map = _translate_batch(provider, client, batch, target=target, local_cache=local_cache)
        updated, failed = _apply_translations(records, batch, translated_map)
        translated_fields += updated
        failed_fields += failed
        print(f"    ✓ updated={updated}, failed={failed}")

    should_save = bool(preserved_en or translated_fields)
    if should_save:
        _save_json(input_path, payload)
        print("  saved: yes")
    else:
        print("  saved: no changes")

    residual_count, residual_samples = _collect_residual_samples(records, target=target, limit=residual_limit)
    print(f"  residual_non_zh={residual_count}")
    for sample in residual_samples:
        print(f"    - {sample['name']} [{sample['field']}] {sample['text']}")

    return {
        "target": target,
        "records": len(records),
        "scanned_fields": scanned_fields,
        "candidate_fields": len(work_items),
        "preserved_en": preserved_en,
        "translated_fields": translated_fields,
        "failed_fields": failed_fields,
        "residual_non_zh": residual_count,
        "saved": should_save,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill zh primary fields for products/blogs JSON data")
    parser.add_argument(
        "--targets",
        default="products,blogs",
        help="Comma-separated targets: products,blogs,all",
    )
    parser.add_argument(
        "--provider",
        choices=["local", "auto", "glm", "perplexity"],
        default="auto",
        help="Translation provider (auto falls back to local public translate)",
    )
    parser.add_argument("--products-input", default=PRODUCTS_FILE, help="products_featured.json path")
    parser.add_argument("--blogs-input", default=BLOGS_FILE, help="blogs_news.json path")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size for translation requests")
    parser.add_argument("--residual-limit", type=int, default=8, help="Max residual non-zh samples to print")
    parser.add_argument("--overwrite-en", action="store_true", help="Overwrite existing *_en with source text")
    parser.add_argument("--dry-run", action="store_true", help="Preview only; do not call provider or write files")
    args = parser.parse_args()

    _load_env()

    targets = _parse_targets(args.targets)
    provider = _pick_available_provider(args.provider)
    client = _create_client(provider)
    if provider != "local" and client is None:
        provider = "local"
        client = _create_client(provider)

    print(
        f"provider={provider}, targets={','.join(targets)}, dry_run={bool(args.dry_run)}, "
        f"timestamp={datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')}"
    )

    overall: Dict[str, int] = {
        "records": 0,
        "scanned_fields": 0,
        "candidate_fields": 0,
        "preserved_en": 0,
        "translated_fields": 0,
        "failed_fields": 0,
        "residual_non_zh": 0,
    }

    for target in targets:
        input_path = args.products_input if target == "products" else args.blogs_input
        result = _process_target(
            target=target,
            input_path=input_path,
            provider=provider,
            client=client,
            batch_size=max(1, int(args.batch_size or 1)),
            dry_run=bool(args.dry_run),
            residual_limit=max(1, int(args.residual_limit or 1)),
            overwrite_en=bool(args.overwrite_en),
        )
        if result.get("error"):
            return 1
        for key in overall:
            overall[key] += int(result.get(key, 0))

    print("\nSummary:")
    print(
        "  "
        + ", ".join(
            [
                f"records={overall['records']}",
                f"scanned_fields={overall['scanned_fields']}",
                f"candidates={overall['candidate_fields']}",
                f"preserved_en={overall['preserved_en']}",
                f"translated={overall['translated_fields']}",
                f"failed={overall['failed_fields']}",
                f"residual_non_zh={overall['residual_non_zh']}",
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
