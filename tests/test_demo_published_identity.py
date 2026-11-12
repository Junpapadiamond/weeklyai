"""Catalog normalization must retain the reviewed generated artifact on public reads."""
from pathlib import Path

import pytest

from app import create_app, rate_limiter
from app.routes import demos
from app.services import demo_experiences as service, product_repository
from app.services.demo_contract import cache_key, compatible_cache_keys, fingerprint
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
