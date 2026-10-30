from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'crawler'))
from tools import refresh_news as news

NOW = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)


def article(source='reddit', url='https://reddit.com/r/LocalLLaMA/comments/abc/launch', **kwargs):
    extra = kwargs.pop('extra', {})
    extra = dict({'evidence_kind': 'feed_excerpt', 'feed_url': 'https://reddit.com/r/LocalLLaMA/new/.rss',
                  'outbound_urls': ['https://github.com/example/model']}, **extra)
    return dict(name='New AI agent release', description='A source-backed AI update', source=source,
                website=url, published_at=(NOW - timedelta(hours=1)).isoformat(), extra=extra, **kwargs)


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
    fresh = [dict(article('hackernews', f'https://news.ycombinator.com/item?id={i}', extra={'evidence_kind': 'platform_api'}), name=f'New AI model release {i}') for i in range(100)]
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
    saved = article('youtube', 'https://youtube.com/watch?v=abc')
    news.atomic_json(tmp_path / 'blogs_news.json', [saved])
    def fail():
        raise TimeoutError('not included in report')
    monkeypatch.setattr(news, 'direct_jobs', lambda *_: [
        ('reddit', 'rss', lambda: [article()], ()), ('youtube', 'rss', fail, ())])
    monkeypatch.setattr(news, 'search_items', lambda *_: [])
    merged, report = news.run(tmp_path, ('reddit', 'youtube'), NOW)
    assert {i['source'] for i in merged} == {'reddit', 'youtube'}
    assert report['sources']['reddit']['status'] == 'direct'
    assert report['sources']['youtube']['status'] == 'retained'
    assert report['sources']['youtube']['fresh_count'] == 0
    assert json.loads((tmp_path / 'blogs_news.json').read_text(encoding='utf-8')) == merged
    assert 'not included in report' not in json.dumps(report)


def test_search_only_runs_for_empty_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(news, 'direct_jobs', lambda *_: [('reddit', 'rss', lambda: [article()], ())])
    calls = []
    monkeypatch.setattr(news, 'search_items', lambda source, _: calls.append(source) or [])
    news.run(tmp_path, ('reddit', 'x'), NOW)
    assert calls == ['x']


def test_reddit_watchlist_uses_one_combined_request(monkeypatch):
    monkeypatch.setattr(news, 'load_reddit_subreddits', lambda: ['LocalLLaMA', 'artificial', '../bad'])
    jobs = news.direct_jobs(NOW, ('reddit',))
    assert len(jobs) == 1
    assert '/r/LocalLLaMA+artificial/new/.rss' in jobs[0][3][1]


def test_rss_requires_real_date_and_ai_content(monkeypatch):
    class Response:
        content = b'''<rss version="2.0"><channel><title>Feed</title>
        <item><title>AI agent release</title><link>https://example.com/ok</link><pubDate>Thu, 29 Oct 2026 10:00:00 GMT</pubDate></item>
        <item><title>AI agent undated</title><link>https://example.com/missing</link></item>
        <item><title>Airline retail discount</title><link>https://example.com/no</link><pubDate>Thu, 29 Oct 2026 10:00:00 GMT</pubDate></item>
        </channel></rss>'''
    monkeypatch.setattr(news, 'get', lambda *_: Response())
    items = news.feed_items('tech_news', 'https://example.com/feed', NOW)
    assert [i['website'] for i in items if not news.rejection_reason(i, NOW)] == ['https://example.com/ok']


def test_rejected_direct_content_triggers_fallback_and_is_reported(tmp_path, monkeypatch):
    bad = dict(article(), name='Help: Claude unable to write to the table')
    monkeypatch.setattr(news, 'direct_jobs', lambda *_: [('reddit', 'rss', lambda: [bad], ())])
    calls = []
    monkeypatch.setattr(news, 'search_items', lambda source, _: calls.append(source) or [article()])
    merged, report = news.run(tmp_path, ('reddit',), NOW)
    assert calls == ['reddit']
    assert len(merged) == 1
    assert report['sources']['reddit']['status'] == 'search_fallback'
    assert report['sources']['reddit']['rejection_reasons'] == {'personal_help_or_chatter': 1}


def test_old_baseline_is_rechecked_and_exact_headlines_deduplicated():
    old_bad = dict(article(), name='Prime numbers explained', source='youtube', website='https://youtube.com/watch?v=bad',
                   description='Sponsor: ChatGPT makes everything easier')
    duplicate = dict(article(), website='https://reddit.com/r/artificial/comments/def/launch')
    audit = {}
    merged = news.merge_news([old_bad, duplicate], [article()], NOW, diagnostics=audit)
    assert len(merged) == 1
    assert audit == {'off_topic': 1, 'duplicate_headline': 1}


def test_rss_excerpt_preserves_entity_encoded_code_and_strips_footer():
    assert news.excerpt('<p>Use &lt;model&gt; API.</p> submitted by /u/a <a href="https://reddit.com/r/a">[comments]</a>') == 'Use <model> API.'


def test_reddit_extracts_evidence_links_without_navigation():
    links = news.outbound_urls('<a href="https://github.com/a/b">code</a><a href="https://reddit.com/u/a">author</a><a href="javascript:alert(1)">bad</a>', 'reddit')
    assert links == ['https://github.com/a/b']


def test_x_discards_reply_and_login_fragments_from_search_body():
    stamp = (int(NOW.timestamp() * 1000) - 1288834974657) << 22
    row = {'url': f'https://x.com/OpenAI/status/{stamp}',
           'title': 'OpenAI on X: "We released an open-source AI model evaluation toolkit." / X',
           'summary': 'Log inSign up @Someone: unrelated claims about a future model'}
    result = news.search_item('x', row, NOW, 'Tavily')
    assert result['name'] == 'We released an open-source AI model evaluation toolkit.'
    assert result['description'] == result['name']
    assert result['extra']['excerpt_basis'] == 'indexed_post_title'
    assert news.rejection_reason(result, NOW) is None
