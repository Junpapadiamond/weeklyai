#!/usr/bin/env python3
"""
Backfill demand signals (HN depth + X non-official mentions) for product datasets.

Targets:
- crawler/data/dark_horses/*.json (latest N weeks)
- crawler/data/rising_stars/*.json (latest N weeks)
- crawler/data/products_featured.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils.demand_signals import DemandSignalEngine, apply_demand_guardrail  # noqa: E402


DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DARK_HORSES_DIR = os.path.join(DATA_DIR, "dark_horses")
RISING_STARS_DIR = os.path.join(DATA_DIR, "rising_stars")
FEATURED_FILE = os.path.join(DATA_DIR, "products_featured.json")

DEFAULT_OFFICIAL_HANDLES_FILE = os.path.join(DATA_DIR, "product_official_handles.json")


def _load_env() -> None:
    repo_root = os.path.dirname(PROJECT_ROOT)
    load_dotenv(os.path.join(repo_root, ".env"))
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def _safe_load_json(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _safe_save_json(path: str, payload: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _extract_week_number(filename: str) -> int:
    match = re.search(r"(\d{4})_(\d{1,2})", filename)
    if not match:
        return -1
    year = int(match.group(1))
    week = int(match.group(2))
    return year * 100 + week


def _latest_week_files(directory: str, weeks: int) -> Tuple[List[str], int]:
    if not os.path.isdir(directory):
        return [], 0
    files = [f for f in os.listdir(directory) if f.endswith(".json") and f != "template.json"]
    files = sorted(files, key=_extract_week_number, reverse=True)
    return [os.path.join(directory, f) for f in files[:weeks]], len(files)


def _parse_date(value: str) -> Optional[datetime]:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        pass
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _coerce_score(value: Any, default: int = 2) -> int:
    try:
        score = int(float(str(value)))
    except Exception:
        score = default
    return max(1, min(5, score))


def _parse_funding_amount_musd(text: str) -> float:
    match = re.search(r"\$?\s*([\d,.]+)\s*([BMK]?)", str(text or ""), re.IGNORECASE)
    if not match:
        return 0.0
    try:
        amount = float(match.group(1).replace(",", ""))
    except Exception:
        return 0.0
    unit = (match.group(2) or "").upper()
    if unit == "B":
        amount *= 1000.0
    elif unit == "K":
        amount /= 1000.0
    return amount


def _has_strong_supply_signal(product: Dict[str, Any]) -> bool:
    funding = _parse_funding_amount_musd(product.get("funding_total", ""))
    if funding >= 30.0:
        return True

    criteria = product.get("criteria_met") or []
    if not isinstance(criteria, list):
        criteria = [criteria]
    criteria = [str(c).lower() for c in criteria]
    if any(k in criteria for k in ["funding_signal", "top_vc_backing", "founder_background", "category_creator"]):
        return True

    why = str(product.get("why_matters", "")).lower()
    return any(k in why for k in ["sequoia", "a16z", "benchmark", "accel", "yc", "y combinator"])


def _needs_backfill(product: Dict[str, Any], force: bool) -> bool:
    if force:
        return True
    extra = product.get("extra") if isinstance(product.get("extra"), dict) else {}
    demand = extra.get("demand") if isinstance(extra, dict) else None
    if not isinstance(demand, dict):
        return True
    return str(demand.get("version") or "") != "v1"


def _add_criteria_tag(product: Dict[str, Any], tag: str) -> None:
    tag = str(tag or "").strip()
    if not tag:
        return
    criteria = product.get("criteria_met") or []
    if not isinstance(criteria, list):
        criteria = [criteria]
    criteria = [str(c).strip() for c in criteria if str(c).strip()]
    if tag not in criteria:
        criteria.append(tag)
    product["criteria_met"] = criteria


def _apply_to_product(
    product: Dict[str, Any],
    engine: DemandSignalEngine,
    *,
    override_mode: str,
    apply_guardrail: bool,
) -> Tuple[bool, str]:
    result = engine.collect_for_product(product)
    demand_payload = result.get("demand") or {}
    community_verdict = result.get("community_verdict")
    tags = result.get("criteria_tags") or []

    changed = False
    extra = product.get("extra") if isinstance(product.get("extra"), dict) else {}
    if extra.get("demand") != demand_payload:
        extra["demand"] = demand_payload
        product["extra"] = extra
        changed = True

    if isinstance(community_verdict, dict) and product.get("community_verdict") != community_verdict:
        product["community_verdict"] = community_verdict
        changed = True

    for tag in tags:
        before = list(product.get("criteria_met") or []) if isinstance(product.get("criteria_met"), list) else []
        _add_criteria_tag(product, tag)
        after = product.get("criteria_met") if isinstance(product.get("criteria_met"), list) else []
        if before != after:
            changed = True

    guardrail_applied = "none"
    if apply_guardrail:
        old_score = _coerce_score(product.get("dark_horse_index"), default=2)
        new_score, guardrail_applied, reason = apply_demand_guardrail(
            llm_score=old_score,
            demand_payload=demand_payload,
            has_strong_supply_signal=_has_strong_supply_signal(product),
            mode=override_mode,
        )
        demand_payload["guardrail_applied"] = guardrail_applied
        demand_payload["guardrail_reason"] = reason
        extra["demand"] = demand_payload
        product["extra"] = extra

        if new_score != old_score:
            product["dark_horse_index"] = new_score
            changed = True
            if guardrail_applied == "upgraded":
                _add_criteria_tag(product, "demand_guardrail_upgraded")
            elif guardrail_applied == "downgraded":
                _add_criteria_tag(product, "demand_guardrail_downgraded")

    return changed, guardrail_applied


def _process_file(
    path: str,
    engine: DemandSignalEngine,
    *,
    force: bool,
    dry_run: bool,
    max_products_left: int,
    override_mode: str,
    apply_guardrail: bool,
) -> Dict[str, int]:
    payload = _safe_load_json(path, [])
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        return {"processed": 0, "updated": 0, "guardrail_up": 0, "guardrail_down": 0}

    processed = 0
    updated = 0
    guardrail_up = 0
    guardrail_down = 0

    for item in payload:
        if max_products_left >= 0 and processed >= max_products_left:
            break
        if not isinstance(item, dict):
            continue
        if not _needs_backfill(item, force=force):
            continue

        changed, guardrail = _apply_to_product(
            item,
            engine,
            override_mode=override_mode,
            apply_guardrail=apply_guardrail,
        )
        processed += 1

        if changed:
            updated += 1
        if guardrail == "upgraded":
            guardrail_up += 1
        elif guardrail == "downgraded":
            guardrail_down += 1

    if updated > 0 and not dry_run:
        _safe_save_json(path, payload)

    return {
        "processed": processed,
        "updated": updated,
        "guardrail_up": guardrail_up,
        "guardrail_down": guardrail_down,
    }


def _filter_featured_recent(items: List[Dict[str, Any]], weeks: int) -> List[Dict[str, Any]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, weeks) * 7)
    out = []
    for p in items:
        dt = _parse_date(p.get("discovered_at") or p.get("first_seen") or p.get("published_at") or "")
        if dt and dt >= cutoff:
            out.append(p)
    return out


def main() -> None:
    _load_env()

    parser = argparse.ArgumentParser(description="Backfill demand signals for WeeklyAI products")
    parser.add_argument("--weeks", type=int, default=8, help="Max recent week files to process per pool")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")
    parser.add_argument("--force", action="store_true", help="Recompute even when demand.version=v1")
    parser.add_argument("--max-products", type=int, default=120, help="Global max products to process (-1 unlimited)")
    parser.add_argument("--apply-guardrail", action="store_true", help="Also update dark_horse_index with demand guardrail")
    args = parser.parse_args()

    weeks = max(1, args.weeks)
    max_products = args.max_products if args.max_products >= 0 else -1

    official_handles_file = os.getenv("PRODUCT_OFFICIAL_HANDLES_FILE", DEFAULT_OFFICIAL_HANDLES_FILE)
    override_mode = os.getenv("DEMAND_OVERRIDE_MODE", "medium").strip().lower()
    window_days = int(os.getenv("DEMAND_WINDOW_DAYS", "7"))
    pplx_key = os.getenv("PERPLEXITY_API_KEY", "")

    engine = DemandSignalEngine(
        window_days=window_days,
        strict_x_official=True,
        official_handles_path=official_handles_file,
        perplexity_api_key=pplx_key,
    )

    dark_files, dark_total = _latest_week_files(DARK_HORSES_DIR, weeks)
    rising_files, rising_total = _latest_week_files(RISING_STARS_DIR, weeks)

    print("=" * 72)
    print("Demand Backfill Report (V1)")
    print("=" * 72)
    print(f"weeks requested: {weeks}")
    print(f"dark_horses files selected: {len(dark_files)} / available {dark_total}")
    print(f"rising_stars files selected: {len(rising_files)} / available {rising_total}")
    if dark_total < weeks or rising_total < weeks:
        print("⚠ available week files are fewer than requested; processing all available files.")
    print(f"official handle map: {official_handles_file}")
    print(f"guardrail mode: {'enabled' if args.apply_guardrail else 'disabled'} ({override_mode})")
    print(f"dry run: {args.dry_run}")

    totals = {
        "processed": 0,
        "updated": 0,
        "guardrail_up": 0,
        "guardrail_down": 0,
    }

    file_sequence = dark_files + rising_files

    for path in file_sequence:
        left = -1 if max_products < 0 else max(0, max_products - totals["processed"])
        if left == 0:
            break
        stats = _process_file(
            path,
            engine,
            force=args.force,
            dry_run=args.dry_run,
            max_products_left=left,
            override_mode=override_mode,
            apply_guardrail=args.apply_guardrail,
        )
        totals["processed"] += stats["processed"]
        totals["updated"] += stats["updated"]
        totals["guardrail_up"] += stats["guardrail_up"]
        totals["guardrail_down"] += stats["guardrail_down"]
        print(f"- {os.path.basename(path)}: processed={stats['processed']}, updated={stats['updated']}")

    # featured: process recent products only for the same week window
    featured = _safe_load_json(FEATURED_FILE, [])
    if isinstance(featured, list):
        recent_featured = _filter_featured_recent(featured, weeks=weeks)
        if recent_featured:
            temp_path = FEATURED_FILE
            left = -1 if max_products < 0 else max(0, max_products - totals["processed"])
            if left != 0:
                if len(recent_featured) != len(featured):
                    # Process on in-memory subset then merge back.
                    subset = recent_featured[:]
                    processed = 0
                    updated = 0
                    up = 0
                    down = 0
                    for item in subset:
                        if left >= 0 and processed >= left:
                            break
                        if not _needs_backfill(item, force=args.force):
                            continue
                        changed, guardrail = _apply_to_product(
                            item,
                            engine,
                            override_mode=override_mode,
                            apply_guardrail=args.apply_guardrail,
                        )
                        processed += 1
                        if changed:
                            updated += 1
                        if guardrail == "upgraded":
                            up += 1
                        elif guardrail == "downgraded":
                            down += 1

                    if updated > 0 and not args.dry_run:
                        _safe_save_json(temp_path, featured)

                    totals["processed"] += processed
                    totals["updated"] += updated
                    totals["guardrail_up"] += up
                    totals["guardrail_down"] += down
                    print(f"- products_featured.json (recent subset): processed={processed}, updated={updated}")
                else:
                    stats = _process_file(
                        temp_path,
                        engine,
                        force=args.force,
                        dry_run=args.dry_run,
                        max_products_left=left,
                        override_mode=override_mode,
                        apply_guardrail=args.apply_guardrail,
                    )
                    totals["processed"] += stats["processed"]
                    totals["updated"] += stats["updated"]
                    totals["guardrail_up"] += stats["guardrail_up"]
                    totals["guardrail_down"] += stats["guardrail_down"]
                    print(f"- products_featured.json: processed={stats['processed']}, updated={stats['updated']}")
        else:
            print("- products_featured.json: no recent products within requested week window")

    print("=" * 72)
    print(
        "Summary: "
        f"processed={totals['processed']}, updated={totals['updated']}, "
        f"guardrail_up={totals['guardrail_up']}, guardrail_down={totals['guardrail_down']}"
    )
    if args.dry_run:
        print("No files were written (dry-run).")
    print("=" * 72)


if __name__ == "__main__":
    main()
