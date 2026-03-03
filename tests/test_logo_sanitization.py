"""Tests for backend logo sanitization and metadata normalization."""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

from app.services import product_filters


def _base_product(**overrides):
    product = {
        "name": "Logo Gate Test",
        "description": "A product used for logo gate tests.",
        "website": "https://example.com",
        "source": "test",
        "why_matters": "matters",
        "logo_url": "",
    }
    product.update(overrides)
    return product


def test_strict_mode_rejects_non_cdn_logo(monkeypatch):
    monkeypatch.setenv("LOGO_STRICT_MODE", "true")
    monkeypatch.setenv("LOGO_CDN_BASE_URL", "https://cdn.weeklyai.com")

    products = product_filters.normalize_products(
        [_base_product(logo_url="https://example.com/favicon.ico")]
    )

    assert len(products) == 1
    product = products[0]
    assert product["logo_url"] == ""
    assert product["logo_status"] == "failed"
    assert product["logo_error_reason"] == "logo_host_not_allowed"


def test_strict_mode_allows_local_and_cdn_logo(monkeypatch):
    monkeypatch.setenv("LOGO_STRICT_MODE", "true")
    monkeypatch.setenv("LOGO_CDN_BASE_URL", "https://cdn.weeklyai.com")

    local = product_filters.normalize_products([
        _base_product(logo_url="/logos/products/example/hash.png")
    ])[0]
    assert local["logo_url"] == "/logos/products/example/hash.png"
    assert local["logo_status"] == "ok"

    remote = product_filters.normalize_products([
        _base_product(logo_url="https://cdn.weeklyai.com/logos/products/example/hash.png")
    ])[0]
    assert remote["logo_url"] == "https://cdn.weeklyai.com/logos/products/example/hash.png"
    assert remote["logo_status"] == "ok"


def test_non_strict_mode_allows_website_domain_logo(monkeypatch):
    monkeypatch.setenv("LOGO_STRICT_MODE", "false")
    monkeypatch.delenv("LOGO_CDN_BASE_URL", raising=False)

    products = product_filters.normalize_products(
        [_base_product(logo_url="https://assets.example.com/brand/logo.png")]
    )

    assert len(products) == 1
    product = products[0]
    assert product["logo_url"] == "https://assets.example.com/brand/logo.png"
    assert product["logo_status"] == "ok"


def test_missing_logo_gets_missing_status(monkeypatch):
    monkeypatch.setenv("LOGO_STRICT_MODE", "true")
    monkeypatch.setenv("LOGO_CDN_BASE_URL", "https://cdn.weeklyai.com")

    products = product_filters.normalize_products([_base_product()])

    assert len(products) == 1
    product = products[0]
    assert product["logo_url"] == ""
    assert product["logo_status"] == "missing"
    assert "logo_source" not in product
    assert "logo_error_reason" not in product


def test_invalid_logo_source_is_not_emitted(monkeypatch):
    monkeypatch.setenv("LOGO_STRICT_MODE", "true")
    monkeypatch.setenv("LOGO_CDN_BASE_URL", "https://cdn.weeklyai.com")

    products = product_filters.normalize_products(
        [_base_product(logo_url="https://example.com/favicon.ico", logo_source="")]
    )

    assert len(products) == 1
    product = products[0]
    assert product["logo_status"] == "failed"
    assert product["logo_error_reason"] == "logo_host_not_allowed"
    assert "logo_source" not in product
