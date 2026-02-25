"""
auto_discover budgeting helper tests (unittest, no network).

Run:
  /usr/bin/python3 tests/test_auto_discover_budgeting.py
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


class TestAutoDiscoverBudgetHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def test_apply_keyword_limit_cn_and_default(self) -> None:
        import tools.auto_discover as ad

        with (
            patch.object(ad, "MAX_KEYWORDS_CN", 2),
            patch.object(ad, "MAX_KEYWORDS_DEFAULT", 3),
        ):
            self.assertEqual(
                ad.apply_keyword_limit("cn", ["k1", "k2", "k3", "k4"]),
                ["k1", "k2"],
            )
            self.assertEqual(
                ad.apply_keyword_limit("us", ["k1", "k2", "k3", "k4"]),
                ["k1", "k2", "k3"],
            )

    def test_should_analyze_gate_rules(self) -> None:
        import tools.auto_discover as ad

        ok, reason = ad.should_analyze_search_results(
            [{"title": "a", "url": "https://a.com/1", "content": "raised funding"}],
            "ai startup",
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "too_few_results")

        one_domain_results = [
            {"title": "A raised", "url": "https://same.com/1", "content": "raised series a"},
            {"title": "B launch", "url": "https://same.com/2", "content": "launch update"},
            {"title": "C release", "url": "https://same.com/3", "content": "released beta"},
        ]
        ok2, reason2 = ad.should_analyze_search_results(one_domain_results, "ai startup")
        self.assertFalse(ok2)
        self.assertEqual(reason2, "too_few_domains")

        no_signal_results = [
            {"title": "A roadmap", "url": "https://a.com/1", "content": "product roadmap details"},
            {"title": "B update", "url": "https://b.com/2", "content": "community update and docs"},
            {"title": "C post", "url": "https://c.com/3", "content": "tool usage tips"},
        ]
        ok3, reason3 = ad.should_analyze_search_results(no_signal_results, "ai startup")
        self.assertFalse(ok3)
        self.assertEqual(reason3, "missing_signal_terms")

        signal_results = [
            {"title": "A raised Series A", "url": "https://a.com/1", "content": "A raised funding"},
            {"title": "B launch", "url": "https://b.com/2", "content": "B launched beta"},
            {"title": "C release", "url": "https://c.com/3", "content": "C released assistant"},
        ]
        ok4, reason4 = ad.should_analyze_search_results(signal_results, "ai startup")
        self.assertTrue(ok4)
        self.assertEqual(reason4, "signal_ok")

        ok5, reason5 = ad.should_analyze_search_results([], "site:techcrunch.com ai startup")
        self.assertTrue(ok5)
        self.assertEqual(reason5, "site_query_bypass")

    def test_build_search_text_keeps_date_and_snippet_limit(self) -> None:
        import tools.auto_discover as ad

        out = ad.build_search_text(
            [
                {
                    "title": "Demo Product",
                    "url": "https://example.com/post",
                    "date": "2026-02-20",
                    "content": "abcdefghijklmno",
                }
            ],
            snippet_limit=10,
        )
        self.assertIn("### Demo Product", out)
        self.assertIn("URL: https://example.com/post", out)
        self.assertIn("Date: 2026-02-20", out)
        self.assertIn("abcdefghij", out)
        self.assertNotIn("abcdefghijk", out)


if __name__ == "__main__":
    unittest.main()
