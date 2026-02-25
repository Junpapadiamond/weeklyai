"""
Social signals tests (unittest, no network).

Run:
  python3 tests/test_social_signals.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
import sys
import unittest
from unittest.mock import patch


def _ensure_import_paths() -> None:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    crawler_root = os.path.join(repo_root, "crawler")
    if crawler_root not in sys.path:
        sys.path.insert(0, crawler_root)


class TestXUrlParsing(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def test_is_status_url_variants(self) -> None:
        from spiders.x_spider import XSpider

        ok = [
            "https://x.com/someone/status/1234567890",
            "https://twitter.com/someone/status/1234567890",
            "https://mobile.twitter.com/someone/status/1234567890",
            "https://twitter.com/i/web/status/1234567890",
            "https://x.com/i/web/status/1234567890",
            "https://twitter.com/i/status/1234567890",
        ]
        bad = [
            "https://x.com/home",
            "https://x.com/someone",
            "https://example.com/someone/status/1234567890",
            "https://twitter.com/search?q=ai",
            "https://twitter.com/someone/status/notanumber",
        ]
        for url in ok:
            with self.subTest(url=url):
                self.assertTrue(XSpider._is_status_url(url))
        for url in bad:
            with self.subTest(url=url):
                self.assertFalse(XSpider._is_status_url(url))

    def test_extract_handle_and_id(self) -> None:
        from spiders.x_spider import _extract_handle_and_id

        handle, tid = _extract_handle_and_id("https://x.com/abc/status/111")
        self.assertEqual(handle, "abc")
        self.assertEqual(tid, "111")

        handle, tid = _extract_handle_and_id("https://twitter.com/i/web/status/222")
        self.assertEqual(handle, "")
        self.assertEqual(tid, "222")

        handle, tid = _extract_handle_and_id("https://twitter.com/i/status/333")
        self.assertEqual(handle, "")
        self.assertEqual(tid, "333")


class TestXPrimaryScheduling(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def test_primary_schedule_interval_and_streak(self) -> None:
        from spiders.x_spider import _should_run_primary

        now = datetime(2026, 2, 25, 3, 0, tzinfo=timezone.utc)
        run, reason = _should_run_primary(
            {"last_primary_run_at": "", "consecutive_fallback_empty_days": 0},
            mode="hybrid",
            now=now,
            interval_days=3,
        )
        self.assertTrue(run)
        self.assertEqual(reason, "no_previous_primary")

        run2, reason2 = _should_run_primary(
            {"last_primary_run_at": "2026-02-24T01:00:00Z", "consecutive_fallback_empty_days": 0},
            mode="hybrid",
            now=now,
            interval_days=3,
        )
        self.assertFalse(run2)
        self.assertEqual(reason2, "interval_not_elapsed")

        run3, reason3 = _should_run_primary(
            {"last_primary_run_at": "2026-02-24T01:00:00Z", "consecutive_fallback_empty_days": 2},
            mode="hybrid",
            now=now,
            interval_days=3,
        )
        self.assertTrue(run3)
        self.assertEqual(reason3, "fallback_empty_streak")

        old_time = (now - timedelta(days=4)).isoformat().replace("+00:00", "Z")
        run4, reason4 = _should_run_primary(
            {"last_primary_run_at": old_time, "consecutive_fallback_empty_days": 0},
            mode="hybrid",
            now=now,
            interval_days=3,
        )
        self.assertTrue(run4)
        self.assertEqual(reason4, "interval_elapsed")


class TestSocialSourceConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def test_youtube_env_overrides_watchlist(self) -> None:
        from utils import social_sources as ss

        with (
            patch.dict(os.environ, {"YOUTUBE_CHANNEL_IDS": "UCENV1,UCENV2"}, clear=False),
            patch.object(ss, "_load_watchlist_file", return_value={"youtube_channel_ids": ["UCFILE"]}),
        ):
            ids, source = ss.load_youtube_channel_ids_with_source()

        self.assertEqual(ids, ["UCENV1", "UCENV2"])
        self.assertEqual(source, "env:YOUTUBE_CHANNEL_IDS")

    def test_x_accounts_file_used_when_env_missing(self) -> None:
        from utils import social_sources as ss

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("X_ACCOUNTS", None)
            with patch.object(ss, "_load_watchlist_file", return_value={"x_accounts": ["@OpenAI", "xai"]}):
                accounts, source = ss.load_x_accounts_with_source()

        self.assertEqual(accounts, ["OpenAI", "xai"])
        self.assertTrue(source.startswith("file:"))

    def test_x_fallback_env_overrides_file(self) -> None:
        from utils import social_sources as ss

        with (
            patch.dict(
                os.environ,
                {
                    "X_FALLBACK_MAX_STATUS_PER_ACCOUNT": "7",
                    "X_FALLBACK_TIMEOUT": "33",
                },
                clear=False,
            ),
            patch.object(
                ss,
                "_load_watchlist_file",
                return_value={
                    "x_fallback": {
                        "max_status_per_account": 3,
                        "request_timeout_seconds": 10,
                    }
                },
            ),
        ):
            cfg = ss.load_x_fallback_config()

        self.assertEqual(cfg["max_status_per_account"], 7)
        self.assertEqual(cfg["request_timeout_seconds"], 33)


class TestXFallbackPath(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def test_extract_status_urls_from_timeline(self) -> None:
        from spiders.x_spider import XSpider

        text = """
        https://x.com/OpenAI/status/111
        https://twitter.com/OpenAI/status/111
        https://x.com/OpenAI/status/222
        https://x.com/Other/status/333
        """
        urls = XSpider._extract_status_urls_from_timeline(text, account="OpenAI", max_items=5)
        self.assertEqual(
            urls,
            [
                "https://x.com/OpenAI/status/111",
                "https://x.com/OpenAI/status/222",
            ],
        )

    def test_fallback_path_builds_x_item(self) -> None:
        from spiders.x_spider import XSpider

        payload = {
            "text": "We launched an AI agent that reached 100k users in one week.",
            "created_at": "2026-02-08T10:00:00.000Z",
            "user": {"screen_name": "OpenAI"},
        }

        with (
            patch.dict(
                os.environ,
                {
                    "X_SOURCE_MODE": "fallback_only",
                    "SOCIAL_HOURS": "1000",
                    "CONTENT_YEAR": "2026",
                },
                clear=False,
            ),
            patch("spiders.x_spider.load_x_accounts_with_source", return_value=(["OpenAI"], "test")),
            patch(
                "spiders.x_spider.load_x_fallback_config",
                return_value={
                    "timeline_provider": "r_jina",
                    "tweet_provider": "x_syndication",
                    "max_status_per_account": 3,
                    "request_timeout_seconds": 10,
                },
            ),
            patch.object(
                XSpider,
                "_fetch_account_timeline_markdown",
                return_value="https://x.com/OpenAI/status/2019513755621843450",
            ),
            patch.object(XSpider, "_fetch_tweet_payload", return_value=payload),
        ):
            items = XSpider().crawl()

        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item.get("source"), "x")
        self.assertEqual(item.get("website"), "https://x.com/OpenAI/status/2019513755621843450")
        self.assertEqual(item.get("published_at"), "2026-02-08T10:00:00Z")
        extra = item.get("extra") or {}
        self.assertEqual(extra.get("query"), "account_fallback:OpenAI")
        self.assertEqual(extra.get("author_handle"), "OpenAI")
        self.assertEqual(extra.get("tweet_id"), "2019513755621843450")


class TestRssToProductsEnrichOrder(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def test_enrich_happens_before_duplicate_skip(self) -> None:
        import tools.rss_to_products as r2p

        featured = [
            {
                "name": "Rabbit r1",
                "website": "https://rabbit.tech",
                "extra": {},
                "trending_score": 80,
            }
        ]
        featured_index = r2p.build_featured_index(featured)
        self.assertIn("rabbit.tech", featured_index)

        articles = [
            {
                "title": "Some X post about Rabbit r1",
                "summary": "demo",
                "link": "https://x.com/i/web/status/123",
                "source": "x",
                "published_at": "2026-02-05T00:00:00Z",
                "extra": {"author_handle": "someone", "query": "q"},
            }
        ]

        validated = {
            "name": "Rabbit r1",
            "website": "https://rabbit.tech",
            "description": "A product description that is long enough.",
            "category": "hardware",
            "categories": ["hardware"],
            "is_hardware": True,
            "dark_horse_index": 4,
            "why_matters": "具体：已发布 demo，有 10 万用户。",
        }

        with (
            patch.object(r2p, "extract_products_with_llm", return_value=[{"name": "Rabbit r1"}]),
            patch.object(r2p, "validate_product", return_value=validated),
            patch.object(r2p, "is_duplicate", return_value=True),
            patch.object(r2p.time, "sleep", return_value=None),
        ):
            result = r2p.process_articles(
                articles,
                llm_type="perplexity",
                llm_client=object(),
                existing_products=[validated],
                featured_index=featured_index,
                enrich_featured=True,
                processed_cache=set(),
                dry_run=False,
            )

        self.assertEqual(int(result.get("enriched_count") or 0), 1)
        enriched = featured[0]
        self.assertTrue(enriched.get("latest_news"))
        self.assertTrue(enriched.get("news_updated_at"))
        self.assertIsInstance((enriched.get("extra") or {}).get("signals"), list)


class TestRssToProductsIndustryLeaders(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def test_industry_leader_blocked_unless_featured_hit(self) -> None:
        import tools.rss_to_products as r2p

        product = {
            "name": "Cursor",
            "website": "https://cursor.com",
            "description": "AI code editor with robust product context and collaboration workflows.",
            "category": "coding",
            "dark_horse_score": 4,
            "why_matters": "ARR exceeded $10M with strong PMF in AI-native coding workflows.",
            "score_reason": "增长快",
        }
        article = {
            "title": "X signal",
            "source": "x",
            "link": "https://x.com/i/web/status/123",
            "published_at": "2026-02-05T00:00:00Z",
        }

        with patch.object(r2p, "load_industry_leader_index", return_value=({"cursor"}, {"cursor.com"})):
            blocked = r2p.validate_product(
                dict(product),
                dict(article),
                llm_client=None,
                featured_index={},
                enrich_featured=True,
            )
            allowed = r2p.validate_product(
                dict(product),
                dict(article),
                llm_client=None,
                featured_index={"cursor.com": {"name": "Cursor", "website": "https://cursor.com"}},
                enrich_featured=True,
            )

        self.assertIsNone(blocked)
        self.assertIsNotNone(allowed)


if __name__ == "__main__":
    unittest.main()
