"""Keep source-verified hosted tools distinct without publishing arbitrary repos."""
import copy
import json
from types import SimpleNamespace

import pytest

from product_identity import (
    catalog_url_key, hosted_project_key, is_verified_hosted_product,
    product_identity_key,
)
from app.services import product_filters as filters
from app.services.product_repository import ProductRepository
from app.services.product_service import ProductService
from tools.auto_publish import merge_featured
from tools.sync_to_mongodb import build_sync_key, merge_products
from utils.dedup import DuplicateChecker, get_domain_key


def hosted_product(name='RPent', website='https://github.com/RLinf/RPent'):
    source = 'https://news.example/article'
    return {
        'name': name, 'website': website, 'source_url': source, 'source': 'github',
        'description': '用于机器人开发的可安装工具，可在本地运行训练和评估任务。',
        'description_en': 'An installable tool for running robot training and evaluation locally.',
        'why_matters': '提供可复现的本地训练和评估流程，便于开发者检查任务结果与模型差异。',
        'why_matters_en': 'Its reproducible local workflow lets developers compare task outcomes and models.',
        'dark_horse_index': 3, 'extra': {'hosted_project_verification': {
            'project_key': hosted_project_key(website), 'source_url': source,
            'usage_quote': 'Developers can install the tool and run local training and evaluation.',
            'verified': True,
        }},
    }


@pytest.mark.parametrize(('url', 'expected'), [
    ('https://GitHub.com/RLinf/RPent/', 'github.com/rlinf/rpent'),
    ('https://github.com/RLinf/RPent.git', 'github.com/rlinf/rpent'),
    ('https://huggingface.co/acme/UsefulTool', 'huggingface.co/acme/UsefulTool'),
    ('https://huggingface.co/spaces/acme/UsefulTool', 'huggingface.co/spaces/acme/UsefulTool'),
])
def test_supported_project_roots(url, expected):
    assert hosted_project_key(url) == expected


@pytest.mark.parametrize('url', [
    'https://github.com/RLinf', 'https://github.com/topics/robotics',
    'https://github.com/features/copilot', 'https://github.com/orgs/rlinf',
    'https://github.com/RLinf/RPent/issues', 'https://github.com/RLinf/RPent/blob/main/README.md',
    'https://github.com/RLinf/RPent/tree/main', 'https://github.com/search?q=robotics',
    'https://github.com/RLinf/%52Pent', 'https://github.com/RLinf/../RPent',
    'https://github.com.evil.example/RLinf/RPent', 'https://github.com:8080/RLinf/RPent',
    'https://user:password@github.com/RLinf/RPent',
    'https://huggingface.co/acme', 'https://huggingface.co/models',
    'https://huggingface.co/docs/transformers', 'https://huggingface.co/datasets/acme/corpus',
    'https://huggingface.co/spaces/acme/Tool/tree/main',
])
def test_profiles_topics_and_other_hosted_pages_are_not_product_roots(url):
    assert hosted_project_key(url) == ''


def test_project_identity_does_not_make_every_repository_an_industry_leader(monkeypatch):
    monkeypatch.setattr(ProductRepository, 'load_industry_leaders', lambda: {
        'categories': {'coding': {'products': [
            {'name': 'GitHub Copilot', 'website': 'https://github.com/features/copilot'},
            {'name': 'KnownTool', 'website': 'https://github.com/acme/KnownTool'},
        ]}}
    })
    assert not filters.is_well_known(hosted_product())
    assert filters.is_well_known({'name': 'Copilot alias', 'website': 'https://github.com/features/copilot'})
    assert filters.is_well_known({'name': 'Renamed tool', 'website': 'https://github.com/acme/knowntool.git'})
    assert product_identity_key('https://github.com/features/copilot') != product_identity_key('https://github.com/RLinf/RPent')


def test_repository_url_alone_does_not_publish_a_research_demo():
    verified = hosted_product()
    unverified = copy.deepcopy(verified)
    unverified.pop('extra')
    assert not filters.is_blocked(verified)
    assert filters.is_blocked(unverified)
    assert ProductService.filter_discovery_products(filters.normalize_products([unverified])) == []
    assert ProductService.filter_discovery_products(filters.normalize_products([verified])) == [verified]


@pytest.mark.parametrize('change', ['key', 'source', 'quote', 'verified', 'profile'])
def test_copied_or_incomplete_provenance_cannot_open_hosted_entry(change):
    product = hosted_product()
    record = product['extra']['hosted_project_verification']
    if change == 'key': record['project_key'] = 'github.com/someone/else'
    if change == 'source': record['source_url'] = 'https://different.example/article'
    if change == 'quote': record['usage_quote'] = 'A repo exists.'
    if change == 'verified': record['verified'] = 'true'
    if change == 'profile': product['website'] = 'https://github.com/RLinf'
    assert not is_verified_hosted_product(product)
    assert filters.is_blocked(product)


def test_same_owner_projects_survive_publication_sync_and_backend_merge():
    first = hosted_product('RLinf', 'https://github.com/RLinf/RLinf')
    second = hosted_product()
    keys = set()
    for product in [first, second]:
        key = catalog_url_key(product['website'])
        assert get_domain_key(product['website']) == key
        assert build_sync_key(product) == key
        assert filters.build_product_key(product) == key
        assert ProductRepository._build_product_key(product) == key
        keys.add(key)
    assert len(keys) == 2
    assert not DuplicateChecker([first]).is_duplicate(second)[0]
    featured = [first]
    assert merge_featured(featured, [second]) == 1
    assert is_verified_hosted_product(featured[1])
    assert len(merge_products(featured, [])) == 2
    assert len(ProductRepository._dedupe_products(featured, filters)) == 2


def test_mongo_parses_provenance_before_hosted_source_filter(monkeypatch):
    verified = hosted_product()
    verified['extra'] = json.dumps(verified['extra'])
    unverified = hosted_product('Research', 'https://github.com/acme/research')
    unverified.pop('extra')
    queries = []
    class Cursor(list):
        def sort(self, *_): return self
    class Collection:
        def find(self, query, projection):
            queries.append(query)
            return Cursor([verified, unverified])
    import app.services.product_repository as repository
    monkeypatch.setattr(repository, 'get_mongo_db', lambda: SimpleNamespace(products=Collection()))
    result = ProductRepository.load_from_mongodb()
    assert [item['name'] for item in result] == ['RPent']
    assert 'source' not in queries[0]


@pytest.mark.parametrize(('url', 'key'), [
    ('https://www.example.com/long/path', 'example.com/long'),
    ('https://example.com/a', 'example.com'),
    ('example.com', 'example.com'),
])
def test_independent_site_catalog_keys_are_unchanged(url, key):
    assert catalog_url_key(url) == key


def test_independent_site_uppercase_path_preserves_each_legacy_key_contract():
    product = {'website': 'https://Example.com/Product/More'}
    assert filters.build_product_key(product) == 'example.com/Product'
    assert build_sync_key(product) == 'example.com/Product'
    assert ProductRepository._build_product_key(product) == 'example.com/product'


def test_social_enrichment_does_not_attach_another_project_on_the_same_host():
    from tools import rss_to_products as enrichment
    first = hosted_product('RLinf', 'https://github.com/RLinf/RLinf')
    second = hosted_product()
    index = enrichment.build_featured_index([first, second])
    assert len(index) == 2
    assert index[enrichment.normalize_domain(second['website'])] is second
