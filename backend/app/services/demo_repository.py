"""Storage for generated demos.

Same shape as ProductRepository: MongoDB when MONGO_URI is configured, JSON
files otherwise. Seeded demos are committed to the repo and are always readable;
demos generated on demand need somewhere to live, and on a read-only serverless
filesystem that can only be Mongo or process memory. Both are wired here so a
deployment without Mongo still works - it just loses on-demand demos on cold
start, which is a cache miss rather than a failure.
"""
from __future__ import annotations

import json
import os
import threading
import time
from typing import Any

from app.services.demo_spec import SpecError, validate_spec

try:
    from app.services.product_repository import CRAWLER_DATA_DIR, get_mongo_db
except ImportError:  # pragma: no cover - product repo is always present in practice
    CRAWLER_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "crawler", "data")

    def get_mongo_db():
        return None


DEMOS_DIR = os.path.join(CRAWLER_DATA_DIR, "demos", "published")
COLLECTION = "demos"
MEMORY_TTL_SECONDS = 60 * 60 * 6

# Process-local cache. Survives warm invocations, not cold starts.
_memory: dict[str, tuple[float, dict[str, Any]]] = {}
_memory_lock = threading.Lock()


def _slugify(value: str) -> str:
    """Stable, filesystem- and URL-safe key for a product."""
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in str(value or "").strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-")[:120]


def _memory_get(slug: str) -> dict[str, Any] | None:
    with _memory_lock:
        entry = _memory.get(slug)
        if not entry:
            return None
        stored_at, spec = entry
        if time.time() - stored_at > MEMORY_TTL_SECONDS:
            _memory.pop(slug, None)
            return None
        return spec


def _memory_put(slug: str, spec: dict[str, Any]) -> None:
    with _memory_lock:
        if len(_memory) > 200:
            oldest = sorted(_memory.items(), key=lambda kv: kv[1][0])[:50]
            for key, _ in oldest:
                _memory.pop(key, None)
        _memory[slug] = (time.time(), spec)


def _read_json_file(slug: str) -> dict[str, Any] | None:
    path = os.path.join(DEMOS_DIR, f"{slug}.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


class DemoRepository:
    """Read and write DemoSpecs. Every read is validated before it is served."""

    @staticmethod
    def slug_for(product: dict[str, Any]) -> str:
        """Derived from the product name only.

        The browser never receives a product's `slug` field, so keying on
        anything else would make the client compute a different slug than the
        one demos are stored under, and every demo would look missing.
        Mirrored by demoSlug() in frontend-next/src/lib/demo-client.ts.
        """
        return _slugify(product.get("name") or "")

    @staticmethod
    def get(slug: str) -> dict[str, Any] | None:
        slug = _slugify(slug)
        if not slug:
            return None

        cached = _memory_get(slug)
        if cached:
            return cached

        raw: Any = None
        db = get_mongo_db()
        if db is not None:
            try:
                raw = db[COLLECTION].find_one({"_sync_key": slug}, {"_id": 0, "_sync_key": 0})
            except Exception:  # noqa: BLE001 - storage must never take down a read
                raw = None
        if raw is None:
            raw = _read_json_file(slug)
        if raw is None:
            return None

        try:
            # A stored spec is validated on the way out too. A demo that no
            # longer satisfies the invariants must not render just because it
            # was written when the rules were looser.
            spec = validate_spec(raw)
        except SpecError:
            return None
        _memory_put(slug, spec)
        return spec

    @staticmethod
    def save(spec: dict[str, Any]) -> dict[str, Any]:
        """Persist a validated spec. Always caches in memory so the generating
        request can serve it even when no durable store is configured."""
        slug = _slugify(spec.get("product_slug", ""))
        if not slug:
            raise SpecError("product_slug: cannot be empty")
        _memory_put(slug, spec)

        db = get_mongo_db()
        if db is not None:
            try:
                db[COLLECTION].update_one(
                    {"_sync_key": slug},
                    {"$set": {**spec, "_sync_key": slug}},
                    upsert=True,
                )
            except Exception:  # noqa: BLE001 - a failed write is a cache miss, not an error
                pass
        return spec

    @staticmethod
    def list_slugs() -> list[str]:
        """Every demo we can serve right now, from all layers."""
        slugs: set[str] = set()
        db = get_mongo_db()
        if db is not None:
            try:
                slugs.update(str(doc["_sync_key"]) for doc in db[COLLECTION].find({}, {"_sync_key": 1}))
            except Exception:  # noqa: BLE001
                pass
        if os.path.isdir(DEMOS_DIR):
            slugs.update(name[:-5] for name in os.listdir(DEMOS_DIR) if name.endswith(".json"))
        with _memory_lock:
            slugs.update(_memory.keys())
        return sorted(s for s in slugs if s)

    @staticmethod
    def clear_memory_cache() -> None:
        """Test seam."""
        with _memory_lock:
            _memory.clear()
