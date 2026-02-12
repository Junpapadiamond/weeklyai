"""
Demand signal tests (unittest, no external network).

Run:
  python3 tests/test_demand_signals.py
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from unittest.mock import patch


def _ensure_import_paths() -> None:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    crawler_root = os.path.join(repo_root, "crawler")
    if crawler_root not in sys.path:
        sys.path.insert(0, crawler_root)


class _FakeSearchResult:
    def __init__(self, url: str):
        self.url = url


class _FakePerplexityClient:
    def __init__(self, urls):
        self.urls = urls
        self.last_query = ""

    def search(self, **kwargs):
        self.last_query = kwargs.get("query", "")
        return [_FakeSearchResult(url=u) for u in self.urls]


class TestHNSignals(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def test_hn_depth_ratio_handles_zero_points(self) -> None:
        from utils.demand_signals import compute_hn_engagement_depth, is_hn_controversial

        ratio = compute_hn_engagement_depth(points=0, comments=12)
        self.assertEqual(ratio, 12.0)
        self.assertFalse(is_hn_controversial(points=0, comments=12, ratio=ratio))

        ratio2 = compute_hn_engagement_depth(points=10, comments=20)
        self.assertEqual(ratio2, 2.0)
        self.assertTrue(is_hn_controversial(points=10, comments=20, ratio=ratio2))

    def test_hn_summary_is_three_sentences_and_sentiment_enum(self) -> None:
        from utils.demand_signals import summarize_hn_comments

        comments = [
            "Great product, onboarding is clean and useful.",
            "I worry about retention and long-term moat.",
            "Execution speed is impressive, but pricing is unclear.",
        ]
        verdict = summarize_hn_comments(comments, llm_client=None)

        summary = verdict.get("summary", "")
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)

        sentence_markers = summary.count("。") + summary.count(".")
        self.assertGreaterEqual(sentence_markers, 3)

        self.assertIn(verdict.get("sentiment"), {"positive", "mixed", "negative", "neutral"})


class TestXSignals(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def test_x_strict_non_official_filtering(self) -> None:
        from utils.demand_signals import collect_x_non_official_signal

        client = _FakePerplexityClient(
            urls=[
                "https://x.com/official_account/status/111",
                "https://x.com/some_dev/status/222",
                "https://twitter.com/other_user/status/333",
                "https://x.com/some_dev/status/222",  # duplicate
                "https://x.com/i/web/status/444",
            ]
        )

        signal = collect_x_non_official_signal(
            product_name="Example Product",
            website="https://example.com",
            official_handle="official_account",
            window_days=7,
            perplexity_client=client,
            strict_official=True,
        )

        self.assertEqual(signal.get("status"), "ok")
        self.assertEqual(signal.get("official_handle"), "official_account")
        self.assertEqual(signal.get("non_official_mentions_7d"), 3)
        self.assertEqual(signal.get("unique_authors_7d"), 2)
        self.assertIn("-from:official_account", signal.get("query", ""))

    def test_x_strict_missing_mapping_skips(self) -> None:
        from utils.demand_signals import collect_x_non_official_signal

        signal = collect_x_non_official_signal(
            product_name="No Map Product",
            website="https://nomap.ai",
            official_handle="",
            window_days=7,
            perplexity_client=None,
            strict_official=True,
        )

        self.assertEqual(signal.get("status"), "skipped")
        self.assertEqual(signal.get("skipped_reason"), "official_handle_missing")


class TestGuardrail(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def test_guardrail_boundaries(self) -> None:
        from utils.demand_signals import apply_demand_guardrail

        upgraded_payload = {
            "demand_score_raw": 0.81,
            "hn": {"status": "ok", "story_count": 1},
            "x": {"status": "ok", "non_official_mentions_7d": 12},
        }
        score, applied, _ = apply_demand_guardrail(
            llm_score=3,
            demand_payload=upgraded_payload,
            has_strong_supply_signal=False,
            mode="medium",
        )
        self.assertEqual(score, 4)
        self.assertEqual(applied, "upgraded")

        downgraded_payload = {
            "demand_score_raw": 0.12,
            "hn": {"status": "ok", "story_count": 1},
            "x": {"status": "ok", "non_official_mentions_7d": 0},
        }
        score2, applied2, _ = apply_demand_guardrail(
            llm_score=5,
            demand_payload=downgraded_payload,
            has_strong_supply_signal=False,
            mode="medium",
        )
        self.assertEqual(score2, 4)
        self.assertEqual(applied2, "downgraded")

        no_downgrade_payload = {
            "demand_score_raw": 0.1,
            "hn": {"status": "ok", "story_count": 1},
            "x": {"status": "skipped", "non_official_mentions_7d": 0},
        }
        score3, applied3, _ = apply_demand_guardrail(
            llm_score=5,
            demand_payload=no_downgrade_payload,
            has_strong_supply_signal=False,
            mode="medium",
        )
        self.assertEqual(score3, 5)
        self.assertEqual(applied3, "none")


class TestDemandSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def test_schema_serializable_and_contains_required_fields(self) -> None:
        from utils.demand_signals import DemandSignalEngine

        fake_hn = {
            "story_count": 2,
            "top_story_id": "123",
            "points": 80,
            "comments": 90,
            "engagement_depth_ratio": 1.125,
            "is_controversial": True,
            "top_comments_sample": ["c1", "c2"],
            "status": "ok",
            "window_days": 7,
        }
        fake_verdict = {
            "source": "hackernews",
            "window_days": 7,
            "summary": "一句。 二句。 三句。",
            "sentiment": "mixed",
            "confidence": 0.7,
        }
        fake_x = {
            "official_handle": "example",
            "non_official_mentions_7d": 15,
            "unique_authors_7d": 9,
            "status_urls_sample": ["https://x.com/a/status/1"],
            "query": "q",
            "status": "ok",
            "window_days": 7,
        }

        with (
            patch("utils.demand_signals.collect_hn_signal", return_value=(fake_hn, fake_verdict)),
            patch("utils.demand_signals.collect_x_non_official_signal", return_value=fake_x),
        ):
            engine = DemandSignalEngine(
                window_days=7,
                strict_x_official=True,
                official_handles_path="/tmp/non-exist.json",
                perplexity_api_key="",
            )
            # Inject mapping so strict-x path can proceed in collect_for_product.
            engine.official_mapping = {
                "by_domain": {"example.com": "example"},
                "by_name": {},
            }
            result = engine.collect_for_product({"name": "Example", "website": "https://example.com"})

        demand = result.get("demand") or {}
        self.assertEqual(demand.get("version"), "v1")
        self.assertIn("computed_at", demand)
        self.assertEqual(demand.get("window_days"), 7)
        self.assertIn("hn", demand)
        self.assertIn("x", demand)
        self.assertIn("demand_score_raw", demand)
        self.assertIn("demand_tier", demand)
        self.assertIn("guardrail_applied", demand)
        self.assertIn("guardrail_reason", demand)

        # Must be JSON serializable
        json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
