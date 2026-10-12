"""Reviewed product workflows served instantly, independent of model availability."""
import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from app.services.demo_contract import validate_experience

PROFILES = {"higgsfield.ai": "higgsfield.json", "autentic.ai": "autentic.json"}
PROFILE_DATES = {"higgsfield.json": "2026-09-27T00:00:00+00:00", "autentic.json": "2026-10-12T00:00:00+00:00"}


def profile_name(product):
    try:
        host = (urlsplit(product.get("website") or "").hostname or "").lower().removeprefix("www.")
        return PROFILES.get(host) if not product.get("is_hardware") else None
    except (ValueError, TypeError):
        return None


@lru_cache(maxsize=32)
def read_profile(name):
    path = Path(__file__).resolve().parents[2] / "data" / "demo_profiles" / name
    return validate_experience(json.loads(path.read_text(encoding="utf-8")))


def product_profile(product):
    name = profile_name(product)
    return read_profile(name) if name else None


def profile_updated_at(product):
    return PROFILE_DATES[profile_name(product)]
