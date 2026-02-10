"""
Tests for MongoDB migration: sync merge/dedupe + backend loading preference.

Run:
    cd <project-root>
    python -m pytest tests/test_mongo_migration.py -v
"""

import json
import os
import sys
import tempfile
from unittest import mock

import pytest

# ---------------------------------------------------------------------------
# Ensure project paths are importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'crawler'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'backend'))


# ===================================================================
# Part 1 — Sync tool: merge_products / build_sync_key / dedupe
# ===================================================================
from tools.sync_to_mongodb import (  # noqa: E402
    build_sync_key,
    load_dark_horses,
    merge_products,
    _normalize_curated_product,
)


class TestBuildSyncKey:
    """Verify _sync_key generation matches backend's build_product_key."""

    def test_simple_url(self):
        assert build_sync_key({'website': 'https://example.com'}) == 'example.com'

    def test_strips_www(self):
        assert build_sync_key({'website': 'https://www.example.com'}) == 'example.com'

    def test_keeps_first_path_segment(self):
        assert build_sync_key({'website': 'https://example.com/product'}) == 'example.com/product'

    def test_ignores_single_char_path(self):
        # Path segment len <= 1 → domain only
        assert build_sync_key({'website': 'https://example.com/a'}) == 'example.com'

    def test_name_fallback(self):
        key = build_sync_key({'name': 'My Cool App'})
        assert key == 'mycoolapp'

    def test_empty_returns_empty(self):
        assert build_sync_key({}) == ''

    def test_url_without_scheme(self):
        assert build_sync_key({'website': 'example.com'}) == 'example.com'

    def test_strips_port(self):
        assert build_sync_key({'website': 'https://example.com:8080'}) == 'example.com'


class TestMergeProducts:
    """Verify featured + dark-horse merge and deduplication."""

    def _make_product(self, name, website, score=3, **kw):
        p = {
            'name': name,
            'website': website,
            'final_score': score,
            'source': 'curated',
        }
        p.update(kw)
        return p

    def test_no_dark_horses(self):
        featured = [self._make_product('A', 'https://a.com')]
        merged = merge_products(featured, [])
        assert len(merged) == 1

    def test_dark_horse_added_when_new(self):
        featured = [self._make_product('A', 'https://a.com')]
        dark = [self._make_product('B', 'https://b.com', score=5)]
        merged = merge_products(featured, dark)
        assert len(merged) == 2
        names = {p['name'] for p in merged}
        assert names == {'A', 'B'}

    def test_dark_horse_merges_on_same_website(self):
        featured = [self._make_product('A', 'https://a.com', score=3)]
        dark = [self._make_product('A Renamed', 'https://a.com', score=5,
                                   why_matters='Important!')]
        merged = merge_products(featured, dark)
        assert len(merged) == 1
        # Score should be max
        assert merged[0]['final_score'] == 5
        # why_matters filled in
        assert merged[0]['why_matters'] == 'Important!'

    def test_dark_horse_merges_on_www_variant(self):
        featured = [self._make_product('A', 'https://www.a.com', score=3)]
        dark = [self._make_product('A', 'https://a.com', score=5)]
        merged = merge_products(featured, dark)
        assert len(merged) == 1
        assert merged[0]['final_score'] == 5

    def test_dedup_by_name_when_no_website(self):
        featured = [self._make_product('Foo Bar', '', score=3)]
        dark = [self._make_product('Foo Bar', '', score=5)]
        merged = merge_products(featured, dark)
        assert len(merged) == 1
        assert merged[0]['final_score'] == 5

    def test_multiple_dark_horse_files_combined(self):
        """Simulate what load_dark_horses does with multiple week files."""
        featured = [self._make_product('A', 'https://a.com')]
        dark = [
            self._make_product('B', 'https://b.com', score=4),
            self._make_product('C', 'https://c.com', score=5),
            self._make_product('A', 'https://a.com', score=5),  # dup of featured
        ]
        merged = merge_products(featured, dark)
        assert len(merged) == 3
        a = next(p for p in merged if p['name'] == 'A')
        assert a['final_score'] == 5


class TestNormalizeCuratedProduct:
    """Verify curated product field normalization."""

    def test_adds_source(self):
        p = _normalize_curated_product({'name': 'X'})
        assert p['source'] == 'curated'

    def test_preserves_existing_source(self):
        p = _normalize_curated_product({'name': 'X', 'source': 'manual'})
        assert p['source'] == 'manual'

    def test_maps_logo(self):
        p = _normalize_curated_product({'name': 'X', 'logo': 'http://img.png'})
        assert p['logo_url'] == 'http://img.png'

    def test_maps_category_to_categories(self):
        p = _normalize_curated_product({'name': 'X', 'category': 'coding'})
        assert p['categories'] == ['coding']

    def test_none_input(self):
        assert _normalize_curated_product(None) is None

    def test_is_hardware_default(self):
        p = _normalize_curated_product({'name': 'X'})
        assert p['is_hardware'] is False


class TestLoadDarkHorses:
    """Test dark-horse file loading from directory."""

    def test_loads_from_temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write two week files
            for i, data in enumerate([
                [{'name': f'P{i}', 'website': f'https://p{i}.com', 'dark_horse_index': 4}]
                for i in range(2)
            ]):
                path = os.path.join(tmpdir, f'week_2026_0{i}.json')
                with open(path, 'w') as f:
                    json.dump(data, f)

            # Write template.json — should be skipped
            with open(os.path.join(tmpdir, 'template.json'), 'w') as f:
                json.dump({'name': 'SKIP'}, f)

            # Patch DARK_HORSES_DIR
            with mock.patch('tools.sync_to_mongodb.DARK_HORSES_DIR', tmpdir):
                result = load_dark_horses()

            assert len(result) == 2
            names = {p['name'] for p in result}
            assert 'SKIP' not in names

    def test_missing_dir_returns_empty(self):
        with mock.patch('tools.sync_to_mongodb.DARK_HORSES_DIR', '/nonexistent'):
            assert load_dark_horses() == []


# ===================================================================
# Part 2 — Backend: MongoDB vs JSON fallback
# ===================================================================

class TestProductRepositoryLoadingPreference:
    """Backend should prefer MongoDB when MONGO_URI is set."""

    def setup_method(self):
        """Reset module-level caches before each test."""
        import app.services.product_repository as repo_mod
        repo_mod._mongo_client = None
        repo_mod._mongo_db = None
        from app.services.product_repository import ProductRepository
        ProductRepository.refresh_cache()

    def test_json_fallback_when_no_mongo_uri(self):
        """Without MONGO_URI env, load_products uses JSON files."""
        from app.services.product_repository import ProductRepository

        env = os.environ.copy()
        env.pop('MONGO_URI', None)

        with mock.patch.dict(os.environ, env, clear=True):
            # Patch _load_from_crawler_file to return known data
            fake = [{'name': 'FromJSON', 'website': 'https://json.test', 'final_score': 1}]
            with mock.patch.object(ProductRepository, '_load_from_crawler_file', return_value=fake):
                with mock.patch.object(ProductRepository, '_load_curated_dark_horses', return_value=[]):
                    products = ProductRepository.load_products()
                    assert any(p['name'] == 'FromJSON' for p in products)

    def test_mongo_preferred_when_uri_set(self):
        """With MONGO_URI set and data available, MongoDB data is used."""
        from app.services.product_repository import ProductRepository
        import app.services.product_repository as repo_mod

        mongo_data = [
            {'name': 'FromMongo', 'website': 'https://mongo.test', 'final_score': 5}
        ]

        with mock.patch.dict(os.environ, {'MONGO_URI': 'mongodb://fake:27017/weeklyai'}):
            with mock.patch.object(ProductRepository, 'load_from_mongodb', return_value=mongo_data):
                with mock.patch.object(ProductRepository, '_load_from_crawler_file') as json_mock:
                    products = ProductRepository.load_products()
                    # MongoDB data used
                    assert any(p['name'] == 'FromMongo' for p in products)
                    # JSON loader NOT called
                    json_mock.assert_not_called()

    def test_json_fallback_when_mongo_empty(self):
        """With MONGO_URI set but MongoDB returns empty, falls back to JSON."""
        from app.services.product_repository import ProductRepository

        fake_json = [{'name': 'Fallback', 'website': 'https://fb.test', 'final_score': 2}]

        with mock.patch.dict(os.environ, {'MONGO_URI': 'mongodb://fake:27017/weeklyai'}):
            with mock.patch.object(ProductRepository, 'load_from_mongodb', return_value=[]):
                with mock.patch.object(ProductRepository, '_load_from_crawler_file', return_value=fake_json):
                    with mock.patch.object(ProductRepository, '_load_curated_dark_horses', return_value=[]):
                        products = ProductRepository.load_products()
                        assert any(p['name'] == 'Fallback' for p in products)


class TestBlogLoadingPreference:
    """Blog loading should prefer MongoDB when MONGO_URI is set."""

    def setup_method(self):
        import app.services.product_repository as repo_mod
        repo_mod._mongo_client = None
        repo_mod._mongo_db = None

    def test_json_fallback_when_no_mongo_uri(self):
        from app.services.product_repository import ProductRepository

        env = os.environ.copy()
        env.pop('MONGO_URI', None)

        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch('builtins.open', mock.mock_open(read_data='[]')):
                with mock.patch('os.path.exists', return_value=True):
                    blogs = ProductRepository.load_blogs()
                    assert isinstance(blogs, list)

    def test_mongo_preferred_when_uri_set(self):
        from app.services.product_repository import ProductRepository

        mongo_blogs = [{'title': 'MongoBlog', 'url': 'https://blog.test'}]

        with mock.patch.dict(os.environ, {'MONGO_URI': 'mongodb://fake:27017/weeklyai'}):
            with mock.patch.object(ProductRepository, 'load_blogs_from_mongodb', return_value=mongo_blogs):
                blogs = ProductRepository.load_blogs()
                assert any(b.get('title') == 'MongoBlog' for b in blogs)


class TestMongoUriConfigured:
    """_mongo_uri_configured helper."""

    def test_returns_false_when_not_set(self):
        from app.services.product_repository import _mongo_uri_configured
        env = os.environ.copy()
        env.pop('MONGO_URI', None)
        with mock.patch.dict(os.environ, env, clear=True):
            assert _mongo_uri_configured() is False

    def test_returns_true_when_set(self):
        from app.services.product_repository import _mongo_uri_configured
        with mock.patch.dict(os.environ, {'MONGO_URI': 'mongodb://localhost:27017/weeklyai'}):
            assert _mongo_uri_configured() is True

    def test_returns_false_for_empty_string(self):
        from app.services.product_repository import _mongo_uri_configured
        with mock.patch.dict(os.environ, {'MONGO_URI': ''}):
            assert _mongo_uri_configured() is False
