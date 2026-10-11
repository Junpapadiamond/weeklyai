"""Claude research chat uses the discovery provider's Messages API contract."""
import json
import os
import sys
from unittest.mock import Mock

import pytest
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import create_app, rate_limiter
from app.routes.chat import _chat_rate_tracker
from app.services import chat_service as chat


@pytest.fixture(autouse=True)
def configure_claude(monkeypatch):
    for key in tuple(os.environ):
        if key.startswith(('CHAT_', 'CLAUDE_', 'PERPLEXITY_', 'DEMO_')):
            monkeypatch.delenv(key)
    monkeypatch.setenv('CLAUDE_API_KEY', 'private-claude-key')
    monkeypatch.setenv('CLAUDE_API_BASE_URL', '"https://relay.test/v1/"')
    monkeypatch.setenv('CLAUDE_MODEL', 'claude-sonnet-5')
    monkeypatch.setattr(chat, '_build_product_context', lambda *args: '[{"name":"Needle","source_url":"https://needle.test/release"}]')
    rate_limiter.requests.clear()
    _chat_rate_tracker.clear()


def response(body=None, status=200):
    result = Mock(status_code=status)
    result.json.return_value = body if body is not None else {
        'content': [{'type': 'text', 'text': 'Try Needle: https://needle.test/release'}],
        'stop_reason': 'end_turn',
    }
    return result


def test_claude_reuses_discovery_settings_and_preserves_conversation(monkeypatch):
    # Env sanitization strips surrounding quotes and escaped newlines separately.
    monkeypatch.setenv('CLAUDE_API_BASE_URL', ' https://relay.test/v1/\\n ')
    monkeypatch.setenv('PERPLEXITY_API_KEY', 'old-perplexity-key')
    upstream = response({'content': [
        {'type': 'thinking', 'thinking': 'private reasoning'},
        {'type': 'text', 'text': 'Try Needle [1].'},
        {'type': 'text', 'text': 'Source: https://needle.test/release'},
    ], 'stop_reason': 'end_turn'})
    post = Mock(return_value=upstream)
    monkeypatch.setattr(chat.requests, 'post', post)
    history = [{'role': 'user', 'content': 'Interview tools?'}, {'role': 'assistant', 'content': 'Needle.'}]
    result = create_app().test_client().post('/api/v1/chat', json={
        'message': 'What can it do?', 'locale': 'en-US', 'history': history,
    })
    assert result.status_code == 200
    assert result.json == {'success': True, 'content': 'Try Needle .\nSource: https://needle.test/release'}
    post.assert_called_once()
    assert post.call_args.args == ('https://relay.test/v1/messages',)
    sent = post.call_args.kwargs
    assert sent['headers']['x-api-key'] == 'private-claude-key'
    assert sent['headers']['anthropic-version'] == '2023-06-01'
    assert 'Authorization' not in sent['headers']
    assert sent['allow_redirects'] is False
    assert sum(sent['timeout']) <= 35
    payload = sent['json']
    assert payload['model'] == 'claude-sonnet-5'
    assert payload['messages'] == history + [{'role': 'user', 'content': 'What can it do?'}]
    assert 'English' in payload['system']
    assert 'https://needle.test/release' in payload['system']
    assert 'untrusted source data' in payload['system']
    assert 'temperature' not in payload
    assert 'disable_search' not in payload
    assert payload['max_tokens'] >= 4096
    upstream.close.assert_called_once()


def test_claude_status_and_health_agree_without_perplexity(monkeypatch):
    from app.services.product_repository import ProductRepository
    monkeypatch.setattr(ProductRepository, 'load_products', lambda: [{'name': 'Needle'}])
    monkeypatch.setattr(ProductRepository, 'get_last_updated', lambda: {
        'storage': 'json', 'product_last_updated': None, 'product_hours_ago': None,
    })
    client = create_app().test_client()
    status = client.get('/api/v1/chat/status').json
    assert status['provider'] == 'claude'
    assert status['model'] == 'claude-sonnet-5'
    assert status['has_api_key'] is True
    assert status['fallback_provider'] is None
    assert 'private-claude-key' not in json.dumps(status)
    assert client.get('/api/v1/health').json['chat_configured'] is True


@pytest.mark.parametrize('body', [None, [], {}, {'content': None}, {'content': 'bad'},
    {'content': [{'type': 'thinking', 'thinking': 'private'}]},
    {'content': [{'type': 'text', 'text': 123}]},
    {'content': [{'type': 'text', 'text': '  '}]},
    {'content': [{'type': 'text', 'text': 'unfinished'}], 'stop_reason': 'max_tokens'},
])
def test_bad_claude_responses_are_safe_errors(monkeypatch, body):
    upstream = response()
    upstream.json.return_value = body
    monkeypatch.setattr(chat.requests, 'post', Mock(return_value=upstream))
    result = create_app().test_client().post('/api/v1/chat', json={'message': '推荐产品'})
    assert result.status_code == 502
    assert result.json['error'] == 'INVALID_RESPONSE'
    assert 'private' not in result.json['content']
    upstream.close.assert_called_once()


@pytest.mark.parametrize('status', [301, 401, 402, 429, 500])
def test_claude_failure_does_not_retry_old_perplexity_or_leak_body(monkeypatch, status):
    monkeypatch.setenv('PERPLEXITY_API_KEY', 'old-perplexity-key')
    upstream = response({'error': 'private provider debug payload'}, status)
    post = Mock(return_value=upstream)
    monkeypatch.setattr(chat.requests, 'post', post)
    result = create_app().test_client().post('/api/v1/chat', json={'message': '推荐产品'})
    assert result.status_code == 503
    assert result.json['error'] == 'PROVIDER_UNAVAILABLE'
    assert 'private' not in result.json['content']
    post.assert_called_once()
    upstream.close.assert_called_once()


def test_claude_timeout_is_504(monkeypatch):
    monkeypatch.setattr(chat.requests, 'post', Mock(side_effect=requests.Timeout('private connection details')))
    result = create_app().test_client().post('/api/v1/chat', json={'message': '推荐产品'})
    assert result.status_code == 504
    assert result.json['error'] == 'TIMEOUT'


def test_explicit_fallback_uses_its_own_auth_and_protocol(monkeypatch):
    monkeypatch.setenv('PERPLEXITY_API_KEY', 'perplexity-key')
    monkeypatch.setenv('CHAT_FALLBACK_TO_PERPLEXITY', 'true')
    post = Mock(side_effect=[response(status=503), response({'choices': [{'message': {'content': 'Fallback answer'}}]})])
    monkeypatch.setattr(chat.requests, 'post', post)
    assert chat.get_chat_response('推荐产品')['success'] is True
    fallback = post.call_args_list[1]
    assert fallback.args == ('https://api.perplexity.ai/chat/completions',)
    assert fallback.kwargs['headers']['Authorization'] == 'Bearer perplexity-key'
    assert 'x-api-key' not in fallback.kwargs['headers']
    assert fallback.kwargs['json']['disable_search'] is True


def test_explicit_chat_config_overrides_shared_claude(monkeypatch):
    monkeypatch.setenv('CHAT_API_BASE_URL', 'https://other.test/v1')
    monkeypatch.setenv('CHAT_API_KEY', 'chat-key')
    monkeypatch.setenv('CHAT_MODEL', 'claude-compatible-model')
    monkeypatch.setenv('CHAT_API_PROTOCOL', 'openai')
    post = Mock(return_value=response({'choices': [{'message': {'content': 'Override answer'}}]}))
    monkeypatch.setattr(chat.requests, 'post', post)
    assert chat.get_chat_response('推荐产品')['success'] is True
    assert post.call_args.args == ('https://other.test/v1/chat/completions',)
    assert post.call_args.kwargs['headers']['Authorization'] == 'Bearer chat-key'


def test_claude_sse_contract(monkeypatch):
    monkeypatch.setattr(chat.requests, 'post', Mock(return_value=response()))
    result = create_app().test_client().post('/api/v1/chat?stream=1', json={'message': '推荐产品'})
    events = [json.loads(line[6:]) for line in result.text.splitlines() if line.startswith('data: ')]
    assert events[0]['type'] == 'text'
    assert events[0]['content'].startswith('Try Needle')
    assert events[-1] == {'type': 'done'}


@pytest.mark.parametrize('value', ['50', '1000', 'nan', 'inf', '-1', '0', 'invalid'])
def test_timeout_budget_stays_below_browser_timeout(monkeypatch, value):
    monkeypatch.setenv('CHAT_TIMEOUT_TOTAL', value)
    assert 5 < chat._timeout_budget() <= 40


def test_exhausted_budget_skips_fallback(monkeypatch):
    monkeypatch.setenv('PERPLEXITY_API_KEY', 'perplexity-key')
    monkeypatch.setenv('CHAT_FALLBACK_TO_PERPLEXITY', 'true')
    monkeypatch.setattr(chat.time, 'monotonic', Mock(side_effect=[0, 0, 36]))
    post = Mock(return_value=response(status=503))
    monkeypatch.setattr(chat.requests, 'post', post)
    assert chat.get_chat_response('推荐产品')['error'] == 'TIMEOUT'
    post.assert_called_once()
