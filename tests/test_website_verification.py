"""
Website verification tests (unittest, no network).

Run:
  PYTHONPATH=backend:crawler python -m pytest tests/test_website_verification.py -v
"""

from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch


def _ensure_import_paths() -> None:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    crawler_root = os.path.join(repo_root, "crawler")
    if crawler_root not in sys.path:
        sys.path.insert(0, crawler_root)


class _FakeResponse:
    def __init__(self, html: str, content_type: str = "text/html; charset=utf-8") -> None:
        self.headers = {"Content-Type": content_type}
        self.text = html


def _html_page(body: str) -> str:
    filler = "Signal " * 40
    return f"<html><body><p>{filler}</p>{body}<p>{filler}</p></body></html>"


class TestWebsiteResolver(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    @patch("utils.website_resolver.requests.get")
    def test_rejects_article_links_on_unrelated_domains(self, mock_get) -> None:
        from utils.website_resolver import extract_official_website_from_source

        mock_get.return_value = _FakeResponse(
            _html_page(
                """
            <html><body>
              <a href="https://www.indexventures.com/perspectives/life-the-universe-and-simile-leading-similes-series-a/">
                Learn about Simile
              </a>
            </body></html>
            """
            )
        )

        resolved = extract_official_website_from_source(
            "https://techcrunch.com/2026/02/17/example",
            "Simile",
            aggressive=True,
        )

        self.assertEqual(resolved, "")

    @patch("utils.website_resolver.requests.get")
    def test_accepts_root_domain_match(self, mock_get) -> None:
        from utils.website_resolver import extract_official_website_from_source

        mock_get.return_value = _FakeResponse(
            _html_page(
                """
            <html><body>
              <a href="https://simile.ai/">Simile</a>
            </body></html>
            """
            )
        )

        resolved = extract_official_website_from_source(
            "https://techcrunch.com/2026/02/17/example",
            "Simile",
            aggressive=True,
        )

        self.assertEqual(resolved, "https://simile.ai/")

    @patch("utils.website_resolver.requests.get")
    def test_rejects_tracking_links_even_with_official_hint(self, mock_get) -> None:
        from utils.website_resolver import extract_official_website_from_source

        mock_get.return_value = _FakeResponse(
            _html_page(
                """
            <html><body>
              <a href="https://qs.dfcfw.com/1608">访问官网</a>
            </body></html>
            """
            )
        )

        resolved = extract_official_website_from_source(
            "https://biz.eastmoney.com/a/202601053608853826.html",
            "雷鸟X3 Pro Project eSIM",
            aggressive=True,
        )

        self.assertEqual(resolved, "")


class TestValidateWebsitesHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def test_mark_verified_clears_pending_state_and_reason(self) -> None:
        from tools.validate_websites import _mark_verified

        item = {
            "website": "https://example.com",
            "needs_verification": True,
            "website_check_reason": "status:200",
        }

        _mark_verified(item)

        self.assertFalse(item["needs_verification"])
        self.assertNotIn("website_check_reason", item)


if __name__ == "__main__":
    unittest.main()
