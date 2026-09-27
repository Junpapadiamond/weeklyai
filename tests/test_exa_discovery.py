from datetime import datetime, timezone

import pytest
import requests

from utils.exa_client import ExaError, search_articles


def test_search_enforces_publication_window_and_bounds(monkeypatch):
    monkeypatch.setenv("EXA_API_KEY", "private-test-key")
    def post(url, **kwargs):
        assert url == "https://api.exa.ai/search"
        assert kwargs["json"]["numResults"] == 10
        assert kwargs["json"]["startPublishedDate"].startswith("2026-09-12")
        assert kwargs["allow_redirects"] is False
        items = [{"url": "https://news.example/" + date, "title": "AI launch", "text": "Article evidence",
                  "publishedDate": date} for date in ["2026-09-25T00:00:00Z", "2026-10-01", "2025-09-01", ""]]
        return type("Response", (), {"status_code": 200, "json": lambda self: {"results": items}})()
    monkeypatch.setattr(requests, "post", post)
    results = search_articles("AI", limit=100, now=datetime(2026, 9, 26, tzinfo=timezone.utc))
    assert len(results) == 1
    assert results[0]["source"] == "Exa"
    assert "links" not in results[0]  # Original article retrieval is still required.


def test_search_errors_do_not_leak_credentials_or_provider_body(monkeypatch):
    monkeypatch.setenv("EXA_API_KEY", "private-test-key")
    monkeypatch.setattr(requests, "post", lambda *a, **k: type("Response", (), {"status_code": 401, "text": "private-test-key"})())
    with pytest.raises(ExaError, match="HTTP 401") as error:
        search_articles("AI")
    assert "private-test-key" not in str(error.value)
    monkeypatch.delenv("EXA_API_KEY")
    with pytest.raises(ExaError, match="missing"):
        search_articles("AI")
