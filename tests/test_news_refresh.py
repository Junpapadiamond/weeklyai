from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'crawler'))
from tools import refresh_news as news

NOW = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)


def article(source='reddit', url='https://reddit.com/r/LocalLLaMA/comments/abc/launch', **kwargs):
    return dict(name='New AI agent release', description='A source-backed AI update', source=source,
                website=url, published_at=(NOW - timedelta(hours=1)).isoformat(), **kwargs)


def test_missing_future_and_old_dates_are_not_freshened():
    for date in (None, '', (NOW + timedelta(days=1)).isoformat(), (NOW - timedelta(days=91)).isoformat()):
        item = article()
        item['published_at'] = date
        item['discovered_at'] = NOW.isoformat()
        assert news.normalize(item, NOW) is None


def test_url_identity_preserves_hn_and_video_but_removes_tracking():
    assert news.canonical_url('https://www.youtube.com/watch?v=abc&utm_source=feed') == 'https://youtube.com/watch?v=abc'
    assert news.canonical_url('https://news.ycombinator.com/item?id=123') != news.canonical_url('https://news.ycombinator.com/item?id=456')
    assert news.canonical_url('javascript:alert(1)') == ''
    assert news.canonical_url('https://user:password@x.com/a') == ''


def test_noisy_platform_does_not_evict_retained_platform_and_fresh_wins():
    saved = article(extra={'evidence_kind': 'feed_excerpt'})
    fresh = [article('hackernews', f'https://news.ycombinator.com/item?id={i}') for i in range(100)]
    result = news.merge_news([saved], fresh, NOW, per_source=10)
    assert len(result) == 11
    assert saved['published_at'] == next(i for i in result if i['source'] == 'reddit')['published_at']
    replacement = dict(saved, description='Updated excerpt')
    assert news.merge_news([saved], [replacement], NOW)[0]['description'] == 'Updated excerpt'


def test_search_is_host_and_post_scoped_and_labelled():
    row = dict(url=article()['website'], title='AI release', summary='AI model release', published_at=NOW.isoformat())
    result = news.search_item('reddit', row, NOW, 'Tavily')
    assert result['extra']['evidence_kind'] == 'search_excerpt'
    assert news.search_item('reddit', dict(row, url='https://reddit.com.evil.test/r/a/comments/b'), NOW, 'Tavily') is None
    assert news.search_item('reddit', dict(row, url='https://reddit.com/r/LocalLLaMA'), NOW, 'Tavily') is None
    assert news.search_item('reddit', dict(row, published_at=''), NOW, 'Tavily') is None


def test_x_timestamp_comes_from_post_id_not_index_date():
    posted = NOW - timedelta(days=2)
    snowflake = (int(posted.timestamp() * 1000) - 1288834974657) << 22
    row = dict(url=f'https://twitter.com/Example/status/{snowflake}', title='AI model release', summary='AI release', published_at=NOW.isoformat())
    result = news.search_item('x', row, NOW, 'Tavily')
    assert result['published_at'] == posted.isoformat()
    assert result['extra']['publication_basis'] == 'x_snowflake'
    assert news.search_item('x', dict(row, url=row['url'] + '/garbage'), NOW, 'Tavily') is None


def test_failure_keeps_other_results_and_retained_dates(tmp_path, monkeypatch):
    saved = article('x', 'https://x.com/a/status/1234567890123456789')
    news.atomic_json(tmp_path / 'blogs_news.json', [saved])
    def fail():
        raise TimeoutError('not included in report')
    monkeypatch.setattr(news, 'direct_jobs', lambda *_: [
        ('reddit', 'rss', lambda: [article()], ()), ('x', 'rss', fail, ())])
    monkeypatch.setattr(news, 'search_items', lambda *_: [])
    merged, report = news.run(tmp_path, ('reddit', 'x'), NOW)
    assert {i['source'] for i in merged} == {'reddit', 'x'}
    assert report['sources']['reddit']['status'] == 'direct'
    assert report['sources']['x']['status'] == 'retained'
    assert report['sources']['x']['fresh_count'] == 0
    assert json.loads((tmp_path / 'blogs_news.json').read_text(encoding='utf-8')) == merged
    assert 'not included in report' not in json.dumps(report)


def test_search_only_runs_for_empty_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(news, 'direct_jobs', lambda *_: [('reddit', 'rss', lambda: [article()], ())])
    calls = []
    monkeypatch.setattr(news, 'search_items', lambda source, _: calls.append(source) or [])
    news.run(tmp_path, ('reddit', 'x'), NOW)
    assert calls == ['x']


def test_rss_requires_real_date_and_ai_content(monkeypatch):
    class Response:
        content = b'''<rss version="2.0"><channel><title>Feed</title>
        <item><title>AI agent release</title><link>https://example.com/ok</link><pubDate>Thu, 29 Oct 2026 10:00:00 GMT</pubDate></item>
        <item><title>AI agent undated</title><link>https://example.com/missing</link></item>
        <item><title>Airline retail discount</title><link>https://example.com/no</link><pubDate>Thu, 29 Oct 2026 10:00:00 GMT</pubDate></item>
        </channel></rss>'''
    monkeypatch.setattr(news, 'get', lambda *_: Response())
    items = news.feed_items('tech_news', 'https://example.com/feed', NOW)
    assert [i['website'] for i in items] == ['https://example.com/ok']
