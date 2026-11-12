"""Catalog normalization must retain the reviewed generated artifact on public reads."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app import create_app, rate_limiter
from app.routes import demos
from app.services import demo_experiences as service, demo_withdrawals, product_repository
from app.services.demo_contract import cache_key, compatible_cache_keys, fingerprint
from app.services.demo_withdrawals import canonical_spec_sha256
from app.services.product_service import ProductService


ROOT = Path(__file__).resolve().parents[1]
SOURCE_KEY = "cc76cd5cb3935b1394d80d88-98e1c153c59ce7bcab85f73d"
NORMALIZED_KEY = "cc76cd5cb3935b1394d80d88-af4b2d833c4ea18f5f34e0bb"


@pytest.mark.parametrize("catalog", ["backend", "crawler"])
def test_normalized_catalog_get_replays_identical_reviewed_spec(catalog, monkeypatch):
    # Load all route modules before patching imported helpers, so legacy routes
    # cannot retain this test's guard after monkeypatch restores the source.
    app = create_app()
    monkeypatch.setattr(product_repository, "_mongo_uri_configured", lambda: False)
    monkeypatch.setattr(product_repository, "PRODUCTS_FEATURED_FILE", str(ROOT / catalog / "data/products_featured.json"))
    monkeypatch.delenv("DEMO_PUBLISHED_PATH", raising=False)
    monkeypatch.setattr(service, "generate_spec", lambda *a, **k: pytest.fail("GET must not generate"))
    monkeypatch.setattr(service.requests, "post", lambda *a, **k: pytest.fail("No provider requests"))
    monkeypatch.setattr(demos, "DemoStore", lambda: pytest.fail("Shipped cache needs no store or quota"))
    monkeypatch.setattr(demos, "_context", lambda: pytest.fail("Prepared GET needs no visitor context"))
    ProductService.refresh_cache()
    try:
        product = ProductService.get_product_by_id("Exa")
        assert product is not None and str(product["_id"]) == "36"
        assert cache_key(product) == NORMALIZED_KEY
        assert SOURCE_KEY not in compatible_cache_keys(product)
        entries = service.published()
        source = entries[SOURCE_KEY]
        canonical = entries[NORMALIZED_KEY]
        assert canonical["spec"] == source["spec"]
        assert canonical["spec"]["interaction"]["kind"] == "records"
        assert canonical["identity_rebinding"]["source_cache_key"] == SOURCE_KEY
        changes = {key for key in canonical if canonical.get(key) != source.get(key)}
        assert changes == {"cache_key", "fingerprint", "product_id", "identity_rebinding"}
        assert canonical["fingerprint"] == fingerprint(product)
        assert canonical["generated_at"] == source["generated_at"]
        assert canonical["model_artifact_sha256"] == source["model_artifact_sha256"]
        assert canonical["review_record"] == source["review_record"]
        for key in (SOURCE_KEY, NORMALIZED_KEY):
            assert (ROOT / "backend/data/demos" / f"{key}.json").read_bytes() == (ROOT / "crawler/data/demos" / f"{key}.json").read_bytes()
        assert service.ready_experience(product) == canonical
        rate_limiter.requests.clear()
        response = app.test_client().get(f"/api/v1/demos/prepared/{product['_id']}")
        assert response.status_code == 200 and response.json["state"] == "ready"
        assert response.json["experience"] == canonical
        assert "Set-Cookie" not in response.headers and "quota" not in response.json
    finally:
        ProductService.refresh_cache()


@pytest.fixture
def production_compatible_entries():
    raw = json.loads((ROOT / "backend/data/products_featured.json").read_text(encoding="utf-8"))
    product = {**next(p for p in raw if p["name"] == "Exa"), "is_hardware": False}
    keys = compatible_cache_keys(product)
    assert keys == ["cc76cd5cb3935b1394d80d88-424a2fa086a1d87c437e0945", SOURCE_KEY]
    entries = {key: json.loads((ROOT / "backend/data/demos" / f"{key}.json").read_text(encoding="utf-8")) for key in keys}
    assert "interaction" not in entries[keys[0]]["spec"]
    assert entries[SOURCE_KEY]["spec"]["interaction"]["kind"] == "records"
    return product, keys, entries


@pytest.mark.parametrize("storage", ["shipped", "store"])
def test_explicit_review_beats_primary_legacy_compatible_key(production_compatible_entries, monkeypatch, storage):
    product, _, entries = production_compatible_entries
    monkeypatch.setattr(service, "published", lambda: entries if storage == "shipped" else {})
    store = SimpleNamespace(get=entries.get) if storage == "store" else None
    result = service.ready_experience(product, store)
    assert result == entries[SOURCE_KEY]


@pytest.mark.parametrize("metadata", [
    {},
    {"reviewed_at": "2026-11-12"},
    {"review_record": "review", "reviewed_at": "not-a-date"},
    {"review_record": "review", "reviewed_at": "2026-02-30"},
    {"review_record": " ", "reviewed_at": "2026-11-12"},
    {"review_record": 7, "reviewed_at": "2026-11-12"},
])
def test_no_valid_review_keeps_compatible_order_despite_generation_time(production_compatible_entries, monkeypatch, metadata):
    product, keys, entries = production_compatible_entries
    entries[SOURCE_KEY].pop("review_record", None)
    entries[SOURCE_KEY].pop("reviewed_at", None)
    entries[SOURCE_KEY].update(metadata, generated_at="2099-01-01T00:00:00+00:00")
    monkeypatch.setattr(service, "published", lambda: entries)
    assert service.ready_experience(product) == entries[keys[0]]


def test_review_date_orders_only_explicitly_reviewed_entries(production_compatible_entries, monkeypatch):
    product, keys, entries = production_compatible_entries
    entries[keys[0]].update(review_record="older-review", reviewed_at="2026-09-27T00:00:00Z", generated_at="2099-01-01")
    monkeypatch.setattr(service, "published", lambda: entries)
    assert service.ready_experience(product) == entries[SOURCE_KEY]


@pytest.mark.parametrize("invalid", ["spec", "withdrawn"])
def test_unusable_reviewed_candidate_falls_back(production_compatible_entries, monkeypatch, tmp_path, invalid):
    product, keys, entries = production_compatible_entries
    if invalid == "spec":
        entries[SOURCE_KEY] = copy.deepcopy(entries[SOURCE_KEY])
        entries[SOURCE_KEY]["spec"]["version"] = 0
    else:
        registry = tmp_path / "withdrawals.json"
        registry.write_text(json.dumps([{"cache_key": SOURCE_KEY,
            "spec_sha256": canonical_spec_sha256(entries[SOURCE_KEY]["spec"]), "reason": "Test reviewed withdrawal"}]), encoding="utf-8")
        monkeypatch.setattr(demo_withdrawals, "REGISTRY_PATH", registry)
    monkeypatch.setattr(service, "published", lambda: entries)
    assert service.ready_experience(product) == entries[keys[0]]
