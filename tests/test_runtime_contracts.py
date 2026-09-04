"""Regression coverage for the production audit, without external services."""
import os
import subprocess
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


@pytest.fixture
def client():
    from app import create_app, rate_limiter
    from app.routes.chat import _chat_rate_tracker
    rate_limiter.requests.clear()
    _chat_rate_tracker.clear()
    return create_app().test_client()


@pytest.mark.parametrize('body', [[], ['hello'], 12, {'message': 12}, {'message': None}, {'message': 'hi', 'history': 'bad'}])
def test_chat_rejects_nonconforming_json(client, body):
    assert client.post('/api/v1/chat', json=body).status_code == 400


def test_chat_reports_missing_key_as_unavailable(client, monkeypatch):
    monkeypatch.delenv('PERPLEXITY_API_KEY', raising=False)
    response = client.post('/api/v1/chat', json={'message': 'Recommend an agent', 'locale': 'en'})
    assert response.status_code == 503
    assert response.json['error'] == 'NOT_CONFIGURED'


def test_upstream_error_is_safe_and_actionable(monkeypatch):
    from app.services.chat_service import get_chat_response
    monkeypatch.setenv('PERPLEXITY_API_KEY', 'test-key')
    response = Mock(status_code=401, text='private provider debug payload')
    with patch('app.services.chat_service.requests.post', return_value=response), patch('app.services.chat_service._build_product_context', return_value=''):
        result = get_chat_response('Recommend a product', 'en')
    assert result['error'] == 'PROVIDER_UNAVAILABLE'
    assert 'private' not in result['content']
    response.close.assert_called_once()


def test_mongo_uri_without_database_uses_weeklyai(monkeypatch):
    from app.services import product_repository as repo
    monkeypatch.setenv('MONGO_URI', 'mongodb://db.example')
    monkeypatch.setattr(repo, '_mongo_db', None)
    monkeypatch.setattr(repo, '_mongo_fail_until', None)
    connection = Mock()
    with patch.object(repo, 'MongoClient', return_value=connection):
        assert repo.get_mongo_db() is connection.get_default_database.return_value
    connection.get_default_database.assert_called_once_with('weeklyai')


def test_missing_snapshots_never_show_sample_inventory(monkeypatch):
    from app.services.product_repository import ProductRepository as repo
    monkeypatch.delenv('MONGO_URI', raising=False)
    repo.refresh_cache()
    with patch.object(repo, '_load_from_crawler_file', return_value=[]), patch.object(repo, '_load_curated_dark_horses', return_value=[]):
        assert repo.load_products() == []
    repo.refresh_cache()


@pytest.mark.parametrize('value,expected', [('$23.38B市值', 0), ('$10.2B valuation', 0), ('900亿韩元 Series A', 0), ('$1,700M', 1700), ('$500M (valuation $4B)', 500), ('$5M', 5)])
def test_only_comparable_funding_influences_ranking(value, expected):
    from app.services.product_sorting import parse_funding
    assert parse_funding(value) == expected


def test_established_products_cannot_reenter_discovery_on_update():
    from app.services.product_filters import is_well_known
    assert is_well_known({'name': 'Databricks', 'website': 'https://databricks.com', 'description': 'New release'})
    assert is_well_known({'name': 'Oura Ring 3', 'website': 'https://ouraring.com', 'description': 'New release'})
    assert is_well_known({'name': 'Fitbit Air', 'website': 'https://store.google.com', 'description': 'New release'})
    assert is_well_known({'name': 'Apptronik', 'website': 'https://apptronik.com', 'description': 'New release'})
    assert not is_well_known({'name': 'CopilotKit', 'website': 'https://copilotkit.ai', 'description': 'Agent UI toolkit'})


def test_fundraising_vehicles_are_not_products():
    from app.services.product_filters import is_non_product
    assert is_non_product({'name': 'Air Street Capital Fund III', 'description_en': 'Venture firm backing AI startups'})
    assert not is_non_product({'name': 'Deal research', 'description_en': 'A software platform for venture capital firms'})


def test_chat_success_preserves_history_and_retrieves_relevant_product(monkeypatch):
    from app.services.chat_service import get_chat_response
    monkeypatch.setenv('PERPLEXITY_API_KEY', 'test-key')
    products = [{'name': f'Unrelated {i}', 'website': f'https://other{i}.test'} for i in range(20)]
    products.append({'name': 'Needle', 'description_en': 'Audio transcription for interviews',
                     'source_url': 'https://needle.test/release', 'discovered_at': '2025-01-01'})
    response = Mock(status_code=200)
    response.json.return_value = {'choices': [{'message': {'content': 'Needle supports transcription.'}}]}
    history = [{'role': 'user', 'content': 'I transcribe customer interviews'}, {'role': 'assistant', 'content': 'What format?'}]
    with patch('app.services.product_service.ProductService.get_discovery_products', return_value=products), patch('app.services.chat_service.requests.post', return_value=response) as post:
        result = get_chat_response('Tell me about Needle', 'en', history)
    assert result['success'] is True
    assert post.call_count == 1
    payload = post.call_args.kwargs['json']
    assert 'https://needle.test/release' in payload['messages'][0]['content']
    assert payload['messages'][1:3] == history
    assert payload['disable_search'] is True
    response.close.assert_called_once()


def test_public_ids_survive_reordering_and_storage_switch():
    from app.services.product_repository import ProductRepository as repo
    a = {'name': 'Cradle', 'website': 'https://cradle.bio'}
    b = {'name': 'New product', 'website': 'https://new-product.test'}
    first = {p['name']: p['_id'] for p in repo._dedupe_products([a.copy(), b.copy()])}
    second = {p['name']: p['_id'] for p in repo._dedupe_products([b.copy(), a.copy()])}
    assert first == second
    assert first['Cradle'] == repo._legacy_ids()['cradle.bio']
    assert first['New product'].startswith('p_')
    assert '/' not in first['New product']


def test_provider_preflight_fails_without_global_key(monkeypatch):
    from tools.check_providers import check_providers
    monkeypatch.delenv('PERPLEXITY_API_KEY', raising=False)
    assert check_providers() is False


def test_vercel_entrypoint_can_load_as_app_module():
    """Vercel names backend/app.py ``app``; it must not shadow app/."""
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
    code = """
import importlib.util, pathlib, sys
path = pathlib.Path('app.py').resolve()
spec = importlib.util.spec_from_file_location('app', path)
module = importlib.util.module_from_spec(spec)
sys.modules['app'] = module
spec.loader.exec_module(module)
assert module.app is not None
"""
    result = subprocess.run(
        [sys.executable, '-c', code],
        cwd=backend_dir,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
