"""Publication survival, budget limits and long-tail regional coverage."""
import copy
from datetime import datetime, timedelta, timezone
import json
from types import SimpleNamespace

import pytest

from tools import claude_discover as discovery
from utils.claude_client import ClaudeError
from utils.discovery_plan import balanced_articles, search_plan, markets_for


def source(index, market='us'):
    name = f'Example{index}'
    return {'title': f'{name} launches niche AI product', 'url': f'https://news.test/{index}',
            'content': f'{name} provides offline transcription for endangered local languages. ' * 4,
            'source': 'Tavily', 'search_region': market, 'search_lane': 'niche',
            'published_at': datetime.now(timezone.utc).isoformat(),
            'links': [{'text': name, 'url': f'https://product{index}.test'}]}


def candidate(index, country='US'):
    article = source(index)
    return {'name': f'Example{index}', 'website': f'https://product{index}.test', 'source_url': article['url'],
            'category': 'voice', 'dark_horse_index': 3, 'confidence': 0.9, 'company_country': country,
            'description': '面向小语种研究人员的离线语音转写工具，可以在本地设备中识别语言。',
            'why_matters': '针对濒危小语种的离线转写工具，在本地设备完成语音识别，适合不能上传录音的田野调查。',
            'criteria_met': ['category_innovation'], 'evidence': [
                {'criterion': 'category_innovation', 'quote': article['content'].split('. ')[0] + '.'}]}


@pytest.fixture
def setup_run(tmp_path, monkeypatch):
    monkeypatch.setenv('CLAUDE_DISCOVERY_MAX_CALLS', '4')
    monkeypatch.setenv('CLAUDE_DISCOVERY_MAX_ARTICLES', '6')
    data = tmp_path / 'data'
    data.mkdir()
    featured = data / 'products_featured.json'
    featured.write_text('[]', encoding='utf-8')
    outcomes = []
    calls = []
    class Client:
        model = 'test'
        usage = {}
        def extract(self, prompt):
            calls.append(prompt)
            outcome = outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return copy.deepcopy(outcome)
    monkeypatch.setattr(discovery, 'ClaudeClient', Client)
    monkeypatch.setattr(discovery, 'fetch_public', lambda url: (
        f'<html>Example{url.split("product")[1].split(".")[0]}</html>'.encode(), url))
    def collect(*args, **kwargs):
        return [source(i) for i in range(6) if source(i)['url'] not in kwargs.get('seen_urls', ())], []
    monkeypatch.setattr(discovery, 'collect_articles', collect)
    def save(product):
        products = json.loads(featured.read_text())
        products.append(product)
        featured.write_text(json.dumps(products), encoding='utf-8')
    from tools.auto_discover import validate_product
    engine = SimpleNamespace(PROJECT_ROOT=str(tmp_path), DARK_HORSES_DIR=str(data / 'dark'),
                             RISING_STARS_DIR=str(data / 'rising'), get_current_week=lambda: '2026_40',
                             load_existing_domains=lambda: set(), validate_product=validate_product, save_product=save)
    return engine, outcomes, calls, featured


def test_later_bad_json_cannot_discard_earlier_saved_product(setup_run):
    engine, outcomes, calls, featured = setup_run
    outcomes.extend([[candidate(0)], ClaudeError('invalid product JSON'), [candidate(4)], ClaudeError('invalid product JSON')])
    report = discovery.run_discovery(engine)
    assert report['saved'] == ['Example0', 'Example4']
    assert len(json.loads(featured.read_text())) == 2
    assert report['status'] == 'partial' and len(calls) == 4
    cache = discovery.load_seen(featured.parent / 'discovery_state.json', datetime.now(timezone.utc))
    assert source(0)['url'] in cache and source(2)['url'] not in cache


def test_retries_follow_other_markets_and_share_request_budget(setup_run):
    engine, outcomes, calls, _ = setup_run
    outcomes.extend([ClaudeError('timeout'), [candidate(2)], [], [candidate(0)]])
    report = discovery.run_discovery(engine, dry_run=True)
    assert len(calls) == report['model_requests'] == 4
    assert [b['batch'] for b in report['batches']] == [1, 2, 3, 1]
    assert [p['name'] for p in report['accepted']] == ['Example2', 'Example0']
    assert report['saved'] == []
    assert not (discovery.Path(engine.PROJECT_ROOT) / 'data/discovery_state.json').exists()


def test_all_failed_batches_fail_loudly_without_poisoning_cache(setup_run):
    engine, outcomes, calls, featured = setup_run
    outcomes.extend([ClaudeError('HTTP 503')] * 4)
    with pytest.raises(ClaudeError, match='No analysis batch succeeded'):
        discovery.run_discovery(engine)
    assert len(calls) == 4
    assert json.loads(featured.read_text()) == []
    assert not (featured.parent / 'discovery_state.json').exists()


def test_auth_error_stops_retrying_but_preserves_verified_products(setup_run):
    engine, outcomes, calls, featured = setup_run
    outcomes.extend([[candidate(0)], ClaudeError('HTTP 401', retryable=False)])
    report = discovery.run_discovery(engine)
    assert report['saved'] == ['Example0'] and len(calls) == 2
    assert report['status'] == 'partial'


def test_current_day_market_quota_and_country_filter(setup_run):
    engine, outcomes, calls, featured = setup_run
    featured.write_text(json.dumps([dict(candidate(i + 20), discovered_at=datetime.now(timezone.utc).date().isoformat())
                                    for i in range(6)]))
    outcomes.extend([[candidate(0), candidate(1, 'JP')], [], []])
    report = discovery.run_discovery(engine, dry_run=True)
    assert [p['name'] for p in report['accepted']] == ['Example1']
    assert report['rejected'][0]['reason'] == 'daily market quota; deferred'
    outcomes.extend([[candidate(0, 'US'), candidate(1, 'KR')], [], []])
    report = discovery.run_discovery(engine, region='jp', dry_run=True)
    assert [p['name'] for p in report['accepted']] == ['Example1']


def test_hardware_filter_is_enforced_outside_model(setup_run):
    engine, outcomes, _, _ = setup_run
    outcomes.extend([[candidate(0)], [], []])
    report = discovery.run_discovery(engine, product_type='hardware', dry_run=True)
    assert not report['accepted']
    assert report['rejected'][0]['reason'] == 'outside requested product type'


def test_cache_expiry_and_all_cached_scan_skips_model(setup_run, monkeypatch):
    engine, outcomes, calls, featured = setup_run
    now = datetime.now(timezone.utc)
    state = featured.parent / 'discovery_state.json'
    discovery.write_state(state, {'https://old.test': (now - timedelta(hours=1)).isoformat(),
                                'https://fresh.test': (now + timedelta(days=1)).isoformat()})
    assert set(discovery.load_seen(state, now)) == {'https://fresh.test'}
    monkeypatch.setattr(discovery, 'collect_articles', lambda *a, **kw: ([], [
        {'source': 'Tavily', 'status': 'ok', 'cached_articles': 1}]))
    report = discovery.run_discovery(engine)
    assert report['status'] == 'no_new_articles' and calls == []


def test_native_niche_searches_cover_every_market_and_rotate():
    today = datetime(2026, 10, 3, tzinfo=timezone.utc)
    plan = search_plan(now=today)
    assert len(plan) == 14
    for market in markets_for('all'):
        assert {p['lane'] for p in plan if p['region'] == market} == {'launch', 'niche'}
    for market, phrase in [('cn', '小众'), ('jp', 'ニッチ'), ('kr', '소규모')]:
        assert any(phrase in p['query'] for p in plan if p['region'] == market)
    assert {p['region'] for p in search_plan('jp')} == {'jp', 'kr'}
    assert plan != search_plan(now=today + timedelta(days=1))


def test_high_volume_us_sources_cannot_crowd_out_small_markets():
    articles = [source(i) for i in range(100)]
    articles += [source(100 + i, market) for i, market in enumerate(markets_for('all')[1:])]
    selected = balanced_articles(articles, 7)
    assert {a['search_region'] for a in selected} == set(markets_for('all'))
    assert len({a['url'] for a in balanced_articles(articles * 2, 40)}) == 40


def test_niche_product_needs_evidence_without_forced_funding_metrics():
    from tools.auto_discover import validate_product
    niche = candidate(0)
    assert not validate_product(niche)[0]
    assert discovery.validate_evidence(niche, [source(0)])[0]
    assert validate_product(niche, evidence_backed=True)[0]
    niche['evidence'][0]['quote'] = 'invented proof not in the source'
    assert not discovery.validate_evidence(niche, [source(0)])[0]


def test_missing_article_link_requires_retrieved_homepage_identity(setup_run, monkeypatch):
    engine, outcomes, _, _ = setup_run
    monkeypatch.setenv('TAVILY_API_KEY', 'test-key')
    unknown = candidate(0)
    unknown['website'] = ''
    monkeypatch.setattr('utils.tavily_client.search_official_sites', lambda *a: [
        {'url': 'https://wrong.test/', 'title': 'Example0', 'content': 'directory'},
        {'url': 'https://product0.test/about', 'title': 'Example0 official', 'content': 'AI product'}])
    def fetch(url):
        title = 'Directory of startups' if 'wrong' in url else 'Example0'
        return f'<html><title>{title}</title><body>{title} AI offline transcription for endangered languages</body></html>'.encode(), url
    monkeypatch.setattr(discovery, 'fetch_public', fetch)
    outcomes.extend([[unknown], [], []])
    report = discovery.run_discovery(engine, dry_run=True)
    assert report['accepted'][0]['website'] == 'https://product0.test/'
    proof = report['accepted'][0]['extra']['website_verification']
    assert proof['search_result_url'] == 'https://product0.test/about'
    assert len(report['website_lookups']) == 1


def test_website_lookup_does_not_rescue_invented_article_evidence(setup_run, monkeypatch):
    engine, outcomes, _, _ = setup_run
    monkeypatch.setenv('TAVILY_API_KEY', 'test-key')
    invalid = candidate(0)
    invalid['website'] = ''
    invalid['evidence'][0]['quote'] = 'Invented quote with no support whatsoever'
    monkeypatch.setattr(discovery, 'resolve_official_site', lambda *a: pytest.fail('Validate evidence before paid lookup'))
    outcomes.extend([[invalid], [], []])
    report = discovery.run_discovery(engine, dry_run=True)
    assert not report['accepted'] and not report['website_lookups']


def test_same_name_artist_or_generic_ai_site_is_not_the_product():
    product = candidate(0)
    assert not discovery.website_use_case_matches(product, 'Example0 singer-songwriter with mesmerizing vocals and storytelling')
    assert not discovery.website_use_case_matches(product, 'Example0 AI company platform product technology investment')
    assert discovery.website_use_case_matches(product, 'Example0 AI offline transcription for endangered languages')


def test_website_lookup_has_a_hard_request_limit(setup_run, monkeypatch):
    engine, outcomes, _, _ = setup_run
    monkeypatch.setenv('TAVILY_API_KEY', 'test-key')
    sources = [source(i) for i in range(12)]
    monkeypatch.setattr(discovery, 'collect_articles', lambda *a, **kw: (sources, []))
    monkeypatch.setenv('CLAUDE_DISCOVERY_MAX_ARTICLES', '12')
    monkeypatch.setenv('CLAUDE_DISCOVERY_MAX_CALLS', '6')
    candidates = [dict(candidate(i), website='') for i in range(12)]
    outcomes.extend([candidates[i:i + 2] for i in range(0, 12, 2)])
    lookups = []
    monkeypatch.setattr(discovery, 'resolve_official_site', lambda *a: lookups.append(a))
    report = discovery.run_discovery(engine, dry_run=True)
    assert len(lookups) == len(report['website_lookups']) == 8
    assert not report['accepted']
