"""Regression coverage for bounded discovery and shared freshness caching."""
from unittest.mock import patch

import pytest
from flask import Flask
from app.routes.products import products_bp
from app.services import product_filters, product_sorting
from app.services.product_repository import ProductRepository
from app.services.product_service import ProductService


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(products_bp, url_prefix='/api/v1/products')
    return app.test_client()


def test_discovery_pages_cover_catalog_without_repeating_ties(client):
    products = [{'_id': str(i), 'name': f'Product {i}', 'dark_horse_index': 3,
                 'discovered_at': '2026-10-10', 'hot_score': 10} for i in range(79)]
    seen = []
    with patch.object(ProductService, 'get_discovery_products', side_effect=[products, products[::-1], products]):
        for offset in (0, 36, 72):
            response = client.get(f'/api/v1/products/discovery-feed?offset={offset}').json
            assert response['pagination']['total'] == 79
            assert response['pagination']['has_more'] == (offset < 72)
            assert len(response['data']) <= 36
            seen.extend(p['_id'] for p in response['data'])
    assert len(seen) == len(set(seen)) == 79


@pytest.mark.parametrize('query,offset,limit', [
    ('offset=-5&limit=99999', 0, 60), ('offset=bad&limit=bad', 0, 36),
    ('offset=9999&limit=0', 9999, 1),
])
def test_discovery_clamps_requests(client, query, offset, limit):
    with patch.object(ProductService, 'get_weekly_top_products', return_value=[]):
        response = client.get(f'/api/v1/products/discovery-feed?{query}')
    assert response.status_code == 200
    assert response.json['pagination'] == {'offset': offset, 'limit': limit, 'total': 0, 'has_more': False}


def test_recency_ties_are_independent_of_database_order():
    products = [{'_id': 'a'}, {'_id': 'b'}, {'_id': 'c'}]
    assert product_sorting.sort_by_recency(products) == product_sorting.sort_by_recency(products[::-1])


def test_freshness_reuses_the_normalized_product_cache(monkeypatch):
    monkeypatch.delenv('MONGO_URI', raising=False)
    ProductRepository.refresh_cache()
    try:
        with patch.object(ProductRepository, '_load_from_crawler_file', return_value=[] ) as load, \
             patch.object(ProductRepository, '_load_curated_dark_horses', return_value=[]):
            ProductRepository.load_products(filters_module=product_filters)
            ProductRepository.get_last_updated()
            ProductRepository.load_products(filters_module=product_filters)
        assert load.call_count == 1
    finally:
        ProductRepository.refresh_cache()
