from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
import requests
from bs4 import BeautifulSoup

from utils.tavily_client import TavilyError, search_articles
from utils.rss_health import inspect_feed
from tools import claude_discover as discovery

NOW = datetime(2026, 9, 27, tzinfo=timezone.utc)


def test_tavily_bounds_dates_auth_and_never_uses_generated_answer(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "private-test-key")
    def post(url, **kwargs):
        assert url == "https://api.tavily.com/search"
        assert kwargs["headers"]["Authorization"] == "Bearer private-test-key"
        body = kwargs["json"]
        assert body["max_results"] == 10 and body["search_depth"] == "basic"
        assert body["start_date"] == "2026-09-13" and body["end_date"] == "2026-09-28"
        assert body["filter_by_published_date"] and not body["include_answer"] and not body["auto_parameters"]
        assert not kwargs["allow_redirects"] and kwargs["timeout"] == (5, 25)
        rows = [{"url": "https://news.test/" + str(i), "title": "AI startup", "content": "Evidence", "published_date": date}
                for i, date in enumerate(["Sat, 26 Sep 2026 12:00:00 GMT", "2026-09-25T10:00:00Z", "2026-10-01", "2025-01-01", None, "broken"])]
        return SimpleNamespace(status_code=200, json=lambda: {"results": rows + [rows[0]], "answer": "Invented company"})
    monkeypatch.setattr(requests, "post", post)
    results = search_articles("AI", limit=100, now=NOW)
    assert len(results) == 2
    assert all(r["source"] == "Tavily" and "links" not in r for r in results)


@pytest.mark.parametrize("failure", [401, 429, "network", "json", "envelope"])
def test_tavily_failure_hides_key_and_response(monkeypatch, failure):
    monkeypatch.setenv("TAVILY_API_KEY", "private-test-key")
    def post(*args, **kwargs):
        if failure == "network":
            raise requests.ConnectionError("private-test-key")
        def body():
            if failure == "json":
                raise ValueError("private-test-key")
            return []
        return SimpleNamespace(status_code=failure if isinstance(failure, int) else 200, json=body, text="private-test-key")
    monkeypatch.setattr(requests, "post", post)
    with pytest.raises(TavilyError) as error:
        search_articles("AI", now=NOW)
    assert "private-test-key" not in str(error.value)


def test_tavily_missing_key_makes_no_request(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.setattr(requests, "post", lambda *a, **k: pytest.fail("No key means no request"))
    with pytest.raises(TavilyError, match="missing"):
        search_articles("AI")


def test_general_search_can_collect_undated_candidates_without_inventing_dates(monkeypatch):
    monkeypatch.setenv('TAVILY_API_KEY', 'private-test-key')
    def post(url, **kwargs):
        assert kwargs['json']['topic'] == 'general'
        assert not kwargs['json']['filter_by_published_date']
        return SimpleNamespace(status_code=200, json=lambda: {'results': [
            {'url': 'https://local.test/new-tool', 'title': 'Local AI tool', 'content': 'Source text'}]})
    monkeypatch.setattr(requests, 'post', post)
    articles = search_articles('小众 AI', now=NOW, topic='general')
    assert len(articles) == 1 and articles[0]['published_at'] == ''


def test_preflight_rejects_explicit_search_without_key(monkeypatch):
    from tools.check_providers import check_providers
    monkeypatch.setenv("DISCOVERY_PROVIDER", "claude")
    monkeypatch.setenv("CLAUDE_API_KEY", "private-test-key")
    monkeypatch.setenv("DISCOVERY_SEARCH_PROVIDER", "tavily")
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    assert not check_providers()
    monkeypatch.setenv("DISCOVERY_SEARCH_PROVIDER", "auto")
    assert check_providers()


def feed(count=1, date="Sat, 26 Sep 2026 12:00:00 GMT"):
    return ('<rss version="2.0"><channel>' + ''.join(
        f'<item><title>AI startup funding {i}</title><link>https://rss.test/{i}</link><pubDate>{date}</pubDate></item>'
        for i in range(count)) + '</channel></rss>').encode()


@pytest.mark.parametrize("body,status", [
    (b"<html>Vercel Security Checkpoint</html>", "blocked"),
    ("<html>正在进行安全检测</html>".encode(), "blocked"),
    (b"<html>Data service has moved</html>", "not_feed"),
    (feed(0), "empty"), (feed(1, "Thu, 27 Aug 2026 00:00:00 GMT"), "stale"),
    (feed(1, "Thu, 01 Oct 2026 00:00:00 GMT"), "future_dated"), (feed(), "ok"),
])
def test_rss_health_rejects_html_and_distinguishes_stale(body, status):
    assert inspect_feed(body, NOW, 14)[1]["status"] == status


def setup_sources(monkeypatch):
    monkeypatch.setattr(discovery, "FEEDS", [("RSS", "https://rss.test/feed")])
    monkeypatch.setenv("TAVILY_API_KEY", "private-test-key")
    monkeypatch.setenv("EXA_API_KEY", "unused-exa-key")
    monkeypatch.setenv("DISCOVERY_SEARCH_PROVIDER", "auto")
    monkeypatch.setattr("utils.exa_client.search_articles", lambda *a: pytest.fail("Tavily is preferred"))
    def fetch(url):
        if url.endswith('/feed'):
            return feed(50), url
        date = '2020-01-01' if 'old' in url else '2026-09-25T12:00:00Z'
        html = f'<meta property="article:published_time" content="{date}"><article>' + 'AI startup product launch. ' * 20 + '<a href="https://product.test">Product</a></article>'
        return html.encode(), url
    monkeypatch.setattr(discovery, "fetch_public", fetch)


def test_search_gets_bounded_input_share_and_original_date_is_required(monkeypatch):
    setup_sources(monkeypatch)
    found = [{"url": 'https://search.test/' + name, "title": "Product news", "published_at": NOW.isoformat(),
              "source": "Tavily", "summary": "AI startup"} for name in ['new', 'old']]
    monkeypatch.setattr("utils.tavily_client.search_articles", lambda *a, **kw: found)
    articles, statuses = discovery.collect_articles(14, 6, NOW)
    assert len(articles) == 6
    assert articles[0]["url"] == "https://search.test/new"
    assert articles[0]["published_at"] == "2026-09-25T12:00:00+00:00"
    assert not any(a["url"].endswith('/old') for a in articles)
    assert statuses[-1]["readable_articles"] == statuses[-1]["selected_articles"] == 1


def test_search_outage_preserves_rss_with_visible_failure_status(monkeypatch):
    setup_sources(monkeypatch)
    def fail(*args, **kwargs):
        raise TavilyError("Tavily returned HTTP 429")
    monkeypatch.setattr("utils.tavily_client.search_articles", fail)
    articles, statuses = discovery.collect_articles(14, 2, NOW)
    assert len(articles) == 2 and statuses[-1]["status"] == "unavailable"
    monkeypatch.setenv("DISCOVERY_SEARCH_PROVIDER", "tavily")
    articles, statuses = discovery.collect_articles(14, 2, NOW)
    assert len(articles) == 2 and statuses[-1]['status'] == 'unavailable'
    assert all(q['error'] == 'Tavily returned HTTP 429' for q in statuses[-1]['queries'])
    monkeypatch.setenv("DISCOVERY_SEARCH_PROVIDER", "rss")
    assert len(discovery.collect_articles(14, 2, NOW)[1]) == 1


def test_article_date_uses_publication_not_modified_date():
    assert discovery.article_publication_date(BeautifulSoup('<script type="application/ld+json">{"dateModified":"2026-09-26"}</script>', 'html.parser')) is None
    soup = BeautifulSoup('<script type="application/ld+json">{"@graph":[{"datePublished":"2026-09-25"}]}</script>', 'html.parser')
    assert discovery.article_publication_date(soup).day == 25
