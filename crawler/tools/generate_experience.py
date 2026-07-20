#!/usr/bin/env python3
"""
为 products_featured.json 中的产品生成「体验配置」(breakdown + experience)。

每个产品在 extra.breakdown 和 extra.experience 写入结构化数据，供
「每日一品」页面渲染「产品洞察」卡片组和「Try it now」交互区。

Usage:
  python tools/generate_experience.py --dry-run           # 预览不写入
  python tools/generate_experience.py --new-only          # 只处理未生成的产品
  python tools/generate_experience.py --all               # 全量重新生成
  python tools/generate_experience.py --id "Lovable"     # 单产品
  python tools/generate_experience.py --limit 10         # 处理前 N 个
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products_featured.json")
sys.path.insert(0, PROJECT_ROOT)

PERPLEXITY_API_KEY = ""
ZHIPU_API_KEY = ""
USE_GLM_FOR_CN = True


def _load_env() -> None:
    global PERPLEXITY_API_KEY, ZHIPU_API_KEY, USE_GLM_FOR_CN
    env_files = [os.path.join(REPO_ROOT, ".env"), os.path.join(PROJECT_ROOT, ".env")]
    if load_dotenv is not None:
        for f in env_files:
            load_dotenv(f)
    else:
        for f in env_files:
            _load_env_fallback(f)
    PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
    ZHIPU_API_KEY = os.environ.get("ZHIPU_API_KEY", "")
    USE_GLM_FOR_CN = os.environ.get("USE_GLM_FOR_CN", "true").lower() == "true"


def _load_env_fallback(path: str) -> None:
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        pass


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def _get_region(product: dict) -> str:
    region = str(product.get("region") or product.get("source_region") or "").strip()
    if "🇨🇳" in region or "cn" in region.lower():
        return "cn"
    return "us"


def _get_client(region: str):
    """Return perplexity or GLM client based on region, same routing as auto_discover."""
    if region == "cn" and USE_GLM_FOR_CN and ZHIPU_API_KEY:
        try:
            from utils.glm_client import GLMClient
            return GLMClient(api_key=ZHIPU_API_KEY), "glm"
        except ImportError:
            pass
    if PERPLEXITY_API_KEY:
        try:
            from utils.perplexity_client import PerplexityClient
            return PerplexityClient(api_key=PERPLEXITY_API_KEY), "perplexity"
        except ImportError:
            pass
    return None, "none"


def _needs_generation(product: dict) -> bool:
    extra = product.get("extra") or {}
    return not (extra.get("breakdown") and extra.get("experience"))


def _generate_for_product(product: dict, dry_run: bool = False) -> dict | None:
    """Call LLM to generate breakdown + experience config. Returns the raw dict or None."""
    from prompts.analysis_prompts import get_experience_config_prompt

    region = _get_region(product)
    client, provider = _get_client(region)
    if client is None:
        print(f"  ⚠️  No LLM client available (region={region}), skipping")
        return None

    prompt = get_experience_config_prompt(product)

    if dry_run:
        print(f"  [dry-run] Would call {provider} for {product.get('name')!r}")
        print(f"  [dry-run] Prompt length: {len(prompt)} chars")
        return {"_dry_run": True}

    try:
        result = client.analyze(prompt, temperature=0.4, max_tokens=1024)
    except Exception as exc:
        print(f"  ❌  LLM error: {exc}")
        return None

    if not isinstance(result, dict):
        print(f"  ❌  Unexpected LLM output type: {type(result)}")
        return None

    return result


def _apply_result(product: dict, result: dict) -> dict:
    """Merge LLM result into product.extra."""
    extra = product.setdefault("extra", {})
    breakdown = result.get("breakdown")
    experience = result.get("experience")

    if isinstance(breakdown, dict) and breakdown:
        extra["breakdown"] = breakdown
    if isinstance(experience, dict) and experience:
        extra["experience"] = experience

    extra["experience_generated_at"] = datetime.now(timezone.utc).isoformat()
    return product


def run(
    products_file: str = PRODUCTS_FILE,
    new_only: bool = True,
    target_id: str | None = None,
    limit: int | None = None,
    dry_run: bool = False,
) -> None:
    _load_env()

    print(f"Loading products from {products_file}")
    products: list[dict] = _load_json(products_file)
    print(f"  Total products: {len(products)}")

    # Filter which products to process
    candidates: list[tuple[int, dict]] = []
    for idx, p in enumerate(products):
        name = p.get("name", "")
        if target_id and name.lower() != target_id.lower():
            continue
        if new_only and not _needs_generation(p):
            continue
        candidates.append((idx, p))
        if limit and len(candidates) >= limit:
            break

    print(f"  To process: {len(candidates)}")
    if not candidates:
        print("Nothing to do.")
        return

    updated = 0
    skipped = 0
    for i, (idx, product) in enumerate(candidates, 1):
        name = product.get("name", f"product_{idx}")
        print(f"\n[{i}/{len(candidates)}] {name}")

        result = _generate_for_product(product, dry_run=dry_run)
        if result is None:
            skipped += 1
            continue

        if dry_run:
            print(f"  ✅ [dry-run] Would write breakdown + experience")
            continue

        _apply_result(product, result)
        products[idx] = product
        updated += 1
        print(f"  ✅ Written: breakdown={bool(product.get('extra', {}).get('breakdown'))}, "
              f"experience={bool(product.get('extra', {}).get('experience'))}")

        # Rate-limit guard: 1 second between calls
        if i < len(candidates):
            time.sleep(1)

    if not dry_run and updated > 0:
        _save_json(products_file, products)
        print(f"\n✅ Saved {products_file} ({updated} updated, {skipped} skipped)")
    elif dry_run:
        print(f"\n[dry-run] Would have updated {len(candidates)} products")
    else:
        print(f"\nNothing saved ({skipped} skipped).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate experience config for WeeklyAI products")
    parser.add_argument("--all", action="store_true", help="Regenerate all products (overwrite existing)")
    parser.add_argument("--new-only", action="store_true", default=False, help="Only products missing experience config")
    parser.add_argument("--id", dest="target_id", default=None, help="Process a single product by name")
    parser.add_argument("--limit", type=int, default=None, help="Max products to process")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--file", default=PRODUCTS_FILE, help="Path to products JSON file")
    args = parser.parse_args()

    new_only = not args.all
    if args.target_id:
        new_only = False  # For a specific ID always regenerate

    run(
        products_file=args.file,
        new_only=new_only,
        target_id=args.target_id,
        limit=args.limit,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
