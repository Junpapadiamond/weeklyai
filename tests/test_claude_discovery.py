import copy
from datetime import datetime, timezone
import json
from types import SimpleNamespace

import pytest

from tools.claude_discover import parse_feed, validate_evidence, public_url, run_discovery, resolve_profile_links, website_identity_matches, normalize_category
from utils.claude_client import ClaudeClient, ClaudeError


def article():
    return {'title': 'ExampleAI raises seed funding', 'url': 'https://news.test/article',
            'content': 'ExampleAI raised $40 million. Its founders previously built robot systems at Acme.',
            'links': [{'url': 'https://exampleai.test', 'text': 'ExampleAI'}]}


def product():
    return {'name': 'ExampleAI', 'source_url': 'https://news.test/article', 'website': 'https://exampleai.test',
            'dark_horse_index': 4, 'confidence': 0.9,
            'criteria_met': ['funding_signal', 'founder_background'],
            'evidence': [{'criterion': 'funding_signal', 'quote': 'ExampleAI raised $40 million.'},
                         {'criterion': 'founder_background', 'quote': 'Its founders previously built robot systems at Acme.'}]}


def test_evidence_requires_collected_source_name_link_and_quotes():
    assert validate_evidence(product(), [article()])[0]
    for field, value in [('source_url', 'https://invented.test'), ('website', 'https://invented.test'), ('name', 'InventedAI'),
                         ('evidence', [{'criterion': 'funding_signal', 'quote': 'They raised $100 million.'}]), ('confidence', 'invalid')]:
        candidate = product()
        candidate[field] = value
        assert not validate_evidence(candidate, [article()])[0], field


def test_two_distinct_evidenced_signals_required_for_dark_horse():
    candidate = product()
    candidate['criteria_met'] = ['funding_signal', 'funding_signal']
    assert not validate_evidence(candidate, [article()])[0]
    candidate['dark_horse_index'] = 3
    assert validate_evidence(candidate, [article()])[0]


def test_feeds_skip_old_future_undated_and_external_entries():
    entries = []
    for label, date, host in [('fresh', '13 Sep', 'news.test'), ('old', '01 Aug', 'news.test'),
                              ('future', '20 Sep', 'news.test'), ('external', '13 Sep', 'elsewhere.test'), ('undated', None, 'news.test')]:
        pub = f'<pubDate>{date} 2026 00:00:00 GMT</pubDate>' if date else ''
        entries.append(f'<item><title>AI startup launch {label}</title><link>https://{host}/{label}</link>{pub}</item>')
    feed = '<rss version="2.0"><channel>' + ''.join(entries) + '</channel></rss>'
    got = parse_feed(feed, 'News', 'https://news.test/rss', datetime(2026, 9, 14, tzinfo=timezone.utc), 14)
    assert [item['url'] for item in got] == ['https://news.test/fresh']


def test_public_fetch_rejects_local_credentials_and_private_dns(monkeypatch):
    monkeypatch.setattr('socket.getaddrinfo', lambda *a, **k: [(2, 1, 6, '', ('127.0.0.1', 443))])
    for url in ['https://localhost', 'http://10.0.0.1', 'https://user:pass@example.com', 'file:///etc/passwd', 'https://example.com:8080']:
        assert not public_url(url)


def test_claude_messages_transport_and_usage(monkeypatch):
    monkeypatch.setenv('CLAUDE_API_KEY', 'private-test-key')
    monkeypatch.setenv('CLAUDE_API_BASE_URL', 'https://relay.test/v1')
    def post(url, **kwargs):
        assert url == 'https://relay.test/v1/messages'
        assert kwargs['headers']['x-api-key'] == 'private-test-key'
        assert kwargs['allow_redirects'] is False
        return type('Response', (), {'status_code': 200, 'json': lambda self: {
            'content': [{'type': 'text', 'text': '```json\n[]\n```'}], 'stop_reason': 'end_turn',
            'usage': {'input_tokens': 12, 'output_tokens': 3}}})()
    monkeypatch.setattr('requests.post', post)
    client = ClaudeClient()
    assert client.extract('test') == []
    assert client.usage == {'requests': 1, 'input_tokens': 12, 'output_tokens': 3}


def test_claude_errors_do_not_expose_key_or_response(monkeypatch):
    monkeypatch.setenv('CLAUDE_API_KEY', 'private-test-key')
    monkeypatch.setattr('requests.post', lambda *a, **k: type('Response', (), {'status_code': 401, 'text': 'private-test-key'})())
    with pytest.raises(ClaudeError, match='HTTP 401') as exc:
        ClaudeClient().complete('test')
    assert 'private-test-key' not in str(exc.value)


def test_truncated_output_is_not_accepted(monkeypatch):
    monkeypatch.setenv('CLAUDE_API_KEY', 'private-test-key')
    monkeypatch.setattr('requests.post', lambda *a, **k: type('Response', (), {'status_code': 200, 'json': lambda self: {
        'stop_reason': 'max_tokens', 'content': [{'type': 'text', 'text': '[]'}]}})())
    with pytest.raises(ClaudeError, match='truncated'):
        ClaudeClient().extract('test')


def test_claude_preflight_does_not_require_perplexity(monkeypatch):
    from tools.check_providers import check_providers
    monkeypatch.setenv('DISCOVERY_PROVIDER', 'claude')
    monkeypatch.setenv('CLAUDE_API_KEY', 'private-test-key')
    monkeypatch.delenv('PERPLEXITY_API_KEY', raising=False)
    assert check_providers()
    monkeypatch.delenv('CLAUDE_API_KEY')
    assert not check_providers()


def test_bounded_dry_run_keeps_product_files_unchanged(tmp_path, monkeypatch):
    monkeypatch.setenv('CLAUDE_DISCOVERY_MAX_CALLS', '1')
    monkeypatch.setenv('CLAUDE_DISCOVERY_MAX_ARTICLES', '100')
    source = article()
    source['published_at'] = '2026-09-13T00:00:00+00:00'
    monkeypatch.setattr('tools.claude_discover.collect_articles', lambda *a: ([source] * 9, []))
    calls = []
    class Client:
        model = 'test'
        usage = {}
        def extract(self, prompt):
            calls.append(prompt)
            return [product(), product()]
    monkeypatch.setattr('tools.claude_discover.ClaudeClient', Client)
    monkeypatch.setattr('tools.claude_discover.fetch_public', lambda url: (b'<title>ExampleAI</title>', url))
    engine = SimpleNamespace(PROJECT_ROOT=str(tmp_path), load_existing_domains=lambda: set(),
                             validate_product=lambda p: (True, 'ok'),
                             save_product=lambda p: pytest.fail('dry run must not save'))
    result = run_discovery(engine, dry_run=True)
    assert len(calls) == 1
    assert len(result['accepted']) == 1
    assert not result['saved']
    assert result['rejected'][0]['reason'] == 'already in catalog'
    assert not (tmp_path / 'data').exists()
    assert len(list((tmp_path / 'logs/discovery').glob('*.json'))) == 1


def test_single_process_lock_blocks_concurrent_writer(tmp_path):
    from tools.auto_discover import acquire_process_lock
    path = str(tmp_path / 'discovery.lock')
    first, acquired = acquire_process_lock(path)
    assert acquired
    try:
        second, acquired = acquire_process_lock(path)
        assert not acquired and second is None
    finally:
        first.close()
    third, acquired = acquire_process_lock(path)
    assert acquired
    third.close()


def test_yc_json_company_website_is_resolved_with_provenance(monkeypatch):
    profile = 'https://www.ycombinator.com/launches/test'
    payload = json.dumps({'url': profile, 'company': {'name': 'ExampleAI', 'url': 'https://exampleai.test'}}).encode()
    monkeypatch.setattr('tools.claude_discover.fetch_public', lambda url: (payload, url))
    assert resolve_profile_links([{'text': 'ExampleAI', 'url': profile}]) == [
        {'text': 'ExampleAI', 'url': 'https://exampleai.test', 'via': profile}]


def test_official_identity_accepts_brand_suffix_but_not_unrelated_site():
    assert website_identity_matches('Praxis AI', 'Praxis Robotics')
    assert not website_identity_matches('Praxis AI', 'A generic AI startup')
    assert not website_identity_matches('AI Labs', 'unrelated')


def test_categories_use_existing_frontend_filters():
    candidate = {'category': 'AI芯片/硬件'}
    normalize_category(candidate)
    assert candidate['category'] == 'hardware'
    assert candidate['categories'] == ['hardware']


def test_real_usage_numbers_are_specific_even_without_funding():
    from tools.auto_discover import validate_product
    candidate = product()
    candidate.update({'description': '为机器人训练收集真实业务场景的视频数据，帮助企业构建数据集。',
                      'why_matters': '已经与上市公司开展合作，采集覆盖超过150种环境的视频，为机器人训练提供真实业务场景数据。'})
    assert validate_product(candidate)[0]
