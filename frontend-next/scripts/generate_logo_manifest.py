#!/usr/bin/env python3
"""Generate frontend logo overrides from crawler data."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
GENERATED_PATH = ROOT / "frontend-next" / "src" / "lib" / "generated" / "logo-manifest.json"
DATA_FILES = [
    ROOT / "crawler" / "data" / "products_featured.json",
    *sorted((ROOT / "crawler" / "data" / "dark_horses").glob("week_*.json")),
    *sorted((ROOT / "crawler" / "data" / "rising_stars").glob("global_*.json")),
]
LOW_CONFIDENCE_MARKERS = (
    "favicon.bing.com",
    "google.com/s2/favicons",
    "icons.duckduckgo.com",
    "icon.horse",
    "favicon.yandex.net",
    "api.faviconkit.com",
)
REJECTED_MARKERS = (
    "logo.clearbit.com",
    "/logos/custom/default-ai.svg",
    "/static/pwa-app/logo-default.png",
)
MANUAL_OVERRIDES = {
    "host::armadin.ai": "https://cdn.prod.website-files.com/69831a4454f985916d15832e/69a7f7bc2c1338897be21c26_Armadin_favicon_1024x%201.png",
    "host::armadin.com": "https://cdn.prod.website-files.com/69831a4454f985916d15832e/69a7f7bc2c1338897be21c26_Armadin_favicon_1024x%201.png",
    "name::armadin": "https://cdn.prod.website-files.com/69831a4454f985916d15832e/69a7f7bc2c1338897be21c26_Armadin_favicon_1024x%201.png",
    "host::mindrobotics.com": "https://framerusercontent.com/images/eUIQcAd5dOttMXYqL7SEn8heT2M.png",
    "name::mind robotics": "https://framerusercontent.com/images/eUIQcAd5dOttMXYqL7SEn8heT2M.png",
    "host::global.dreame.com": "https://global.dreametech.com/cdn/shop/files/dreame_favicon_180x180.png?v=1695195563",
    "host::citydetect.ai": "https://framerusercontent.com/images/GLlwL41iXpOOPa1kpgg7xobzluo.png",
    "host::sciencecorp.ai": "https://science.xyz/favicon.svg",
    "host::zeroeval.ai": "https://zeroeval.com/logos/theta.svg",
    "host::reyassurance.com": "https://rey.id/images/rey-logo-200x200.png",
    "host::sribuu.com": "https://sribuu.id/wp-content/uploads/2022/06/Blue-2-1-300x68.png",
    "host::olix.ai": "https://framerusercontent.com/images/3i4Xjk57Cu3LmzjLcgzvlAsBrAs.png",
    "host::diligent.ai": "https://cdn.prod.website-files.com/68bdab1c8fb03044e2c8c8ae/68bdac781023b7fed634401c_diligent-webclip.png",
    "host::tess.ai": "https://tess.im/favicon.ico",
    "host::confido.ai": "https://cdn.prod.website-files.com/6863ce36b3742ef229f42f6a/688b505483a098e4d2312c12_confido_logo_dark%201.svg",
    "host::xiaoyizhou.com": "https://growth-cdn.ticwear.com/ticbuy/img/common-logo.0.svg",
    "name::zeroeval": "https://zeroeval.com/logos/theta.svg",
    "name::science corp.": "https://science.xyz/favicon.svg",
    "name::frankenburg technologies": "https://frankenburg.tech/wp-content/uploads/2026/02/Frankenburg-Tech-Logo-Black_Transparent-163x79.png",
    "name::city detect": "https://framerusercontent.com/images/GLlwL41iXpOOPa1kpgg7xobzluo.png",
    "name::dreame pilot 20": "https://global.dreametech.com/cdn/shop/files/dreame_favicon_180x180.png?v=1695195563",
    "name::sribuu": "https://sribuu.id/wp-content/uploads/2022/06/Blue-2-1-300x68.png",
    "name::rey assurance": "https://rey.id/images/rey-logo-200x200.png",
    "name::出门问问 ticnote pods": "https://growth-cdn.ticwear.com/ticbuy/img/common-logo.0.svg",
}


def normalize_logo_source(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if raw.startswith("//"):
        return f"https:{raw}"
    if raw.startswith("/"):
        return raw
    if re.match(r"^https?://", raw, re.I):
        return raw
    if re.match(r"^[a-z0-9.-]+\.[a-z]{2,}([/:?#]|$)", raw, re.I):
        return f"https://{raw}"
    return ""


def normalize_host(value: object) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    raw = re.sub(r"^https?://", "", raw)
    raw = re.sub(r"/.*$", "", raw)
    raw = re.sub(r":\d+$", "", raw)
    raw = re.sub(r"^www\.", "", raw)
    if not re.match(r"^[a-z0-9.-]+\.[a-z]{2,}$", raw):
        return ""
    return raw


def resolve_logo_host(website: object) -> str:
    normalized = normalize_logo_source(website)
    if not normalized or normalized.startswith("/"):
        return ""
    try:
        return normalize_host(urlparse(normalized).hostname)
    except ValueError:
        return ""


def normalize_name_key(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def is_rejected_logo(value: object) -> bool:
    normalized = normalize_logo_source(value)
    if not normalized:
        return True
    lower = normalized.lower()
    return any(marker in lower for marker in (*LOW_CONFIDENCE_MARKERS, *REJECTED_MARKERS))


def iter_products(path: Path) -> Iterable[dict]:
    payload = json.loads(path.read_text())
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for value in payload.values():
            if isinstance(value, list):
                return value
    return []


def build_manifest() -> dict[str, str]:
    manifest: dict[str, str] = {}
    records: list[dict[str, str]] = []

    for path in DATA_FILES:
        for product in iter_products(path):
            if not isinstance(product, dict):
                continue

            candidate = ""
            for field in ("logo_url", "logo"):
                value = normalize_logo_source(product.get(field))
                if value and not is_rejected_logo(value):
                    candidate = value
                    break
            if not candidate:
                continue

            product_id = str(product.get("_id") or product.get("id") or "").strip()
            host = resolve_logo_host(product.get("website"))
            name = normalize_name_key(product.get("name"))
            records.append({
                "id": product_id,
                "host": host,
                "name": name,
                "candidate": candidate,
            })

    name_candidates: dict[str, set[str]] = defaultdict(set)
    for record in records:
        if record["name"]:
            name_candidates[record["name"]].add(record["candidate"])

    for record in records:
        keys: list[str] = []
        if record["id"]:
            keys.append(f"id::{record['id']}")
        if record["host"] and record["name"]:
            keys.append(f"hn::{record['host']}::{record['name']}")
        if record["host"]:
            keys.append(f"host::{record['host']}")
        if record["name"] and len(name_candidates[record["name"]]) == 1:
            keys.append(f"name::{record['name']}")

        for key in keys:
            manifest.setdefault(key, record["candidate"])

    for key, value in MANUAL_OVERRIDES.items():
        manifest[key] = value

    return manifest


def main() -> None:
    manifest = build_manifest()
    GENERATED_PATH.parent.mkdir(parents=True, exist_ok=True)
    GENERATED_PATH.write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")))
    print(f"wrote {len(manifest)} keys to {GENERATED_PATH}")


if __name__ == "__main__":
    main()
