"""
GLM Web Search API + hardware validation tests (unittest, no network).

Run:
  python3 tests/test_glm_tool_parsing.py
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch


def _ensure_import_paths() -> None:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    crawler_root = os.path.join(repo_root, "crawler")
    if crawler_root not in sys.path:
        sys.path.insert(0, crawler_root)


class TestGLMWebSearchAPI(unittest.TestCase):
    """Tests for the direct Web Search API integration in GLMClient.search()."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def _make_client(self):
        """Create a GLMClient with a mock search session (no real API key needed)."""
        from utils.glm_client import GLMClient

        client = GLMClient.__new__(GLMClient)
        client.api_key = "fake-key"
        client.model = "glm-4.7"
        client.search_engine = "search_pro"
        client._client = None
        client._search_session = MagicMock()
        return client

    def _mock_response(self, search_results: list[dict], status_code: int = 200):
        """Build a mock requests.Response."""
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = {"search_result": search_results}
        mock_resp.raise_for_status.return_value = None
        return mock_resp

    def test_basic_field_mapping(self) -> None:
        """API response fields are mapped correctly to SearchResult."""
        client = self._make_client()
        client._search_session.post.return_value = self._mock_response([
            {
                "title": "AI融资新闻",
                "link": "https://36kr.com/p/123",
                "content": "某AI公司完成A轮融资5000万美元",
                "media": "36氪",
                "publish_date": "2026-02-10",
            },
            {
                "title": "机器人创业",
                "link": "https://jiqizhixin.com/articles/456",
                "content": "人形机器人赛道获得新一轮投资",
                "media": "机器之心",
                "publish_date": "2026-02-09",
            },
        ])

        results = client.search("AI融资 2026", max_results=10)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].title, "AI融资新闻")
        self.assertEqual(results[0].url, "https://36kr.com/p/123")
        self.assertEqual(results[0].snippet, "某AI公司完成A轮融资5000万美元")
        self.assertEqual(results[0].source, "36氪")
        self.assertEqual(results[0].date, "2026-02-10")

        self.assertEqual(results[1].url, "https://jiqizhixin.com/articles/456")
        self.assertEqual(results[1].source, "机器之心")

    def test_max_results_limit(self) -> None:
        """Results are truncated to max_results."""
        client = self._make_client()
        items = [
            {"title": f"Result {i}", "link": f"https://example{i}.com", "content": f"content {i}"}
            for i in range(20)
        ]
        client._search_session.post.return_value = self._mock_response(items)

        results = client.search("test", max_results=5)
        self.assertEqual(len(results), 5)

    def test_skips_items_without_url_or_title(self) -> None:
        """Items missing link or title are filtered out."""
        client = self._make_client()
        client._search_session.post.return_value = self._mock_response([
            {"title": "", "link": "https://a.com", "content": "no title"},
            {"title": "No URL", "link": "", "content": "no url"},
            {"title": "Valid", "link": "https://b.com", "content": "ok"},
        ])

        results = client.search("test")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Valid")

    def test_to_dict_format(self) -> None:
        """SearchResult.to_dict() produces the expected dict keys for downstream consumers."""
        client = self._make_client()
        client._search_session.post.return_value = self._mock_response([
            {
                "title": "Test",
                "link": "https://test.com",
                "content": "snippet",
                "media": "TestMedia",
                "publish_date": "2026-01-01",
            }
        ])

        results = client.search("test")
        d = results[0].to_dict()
        self.assertEqual(d["title"], "Test")
        self.assertEqual(d["url"], "https://test.com")
        self.assertEqual(d["content"], "snippet")
        self.assertEqual(d["source"], "TestMedia")
        self.assertEqual(d["date"], "2026-01-01")

    def test_empty_response(self) -> None:
        """Empty search_result returns empty list."""
        client = self._make_client()
        client._search_session.post.return_value = self._mock_response([])

        results = client.search("nonexistent query")
        self.assertEqual(results, [])

    def test_no_session_returns_empty(self) -> None:
        """If _search_session is None, search() returns [] immediately."""
        client = self._make_client()
        client._search_session = None

        results = client.search("test")
        self.assertEqual(results, [])

    def test_payload_uses_correct_engine(self) -> None:
        """Verify the POST payload includes the specified search engine."""
        client = self._make_client()
        client._search_session.post.return_value = self._mock_response([])

        client.search("AI test", search_engine="search_pro_sogou")

        call_args = client._search_session.post.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        self.assertEqual(payload["search_engine"], "search_pro_sogou")
        self.assertEqual(payload["search_intent"], False)
        self.assertEqual(payload["content_size"], "medium")
        self.assertEqual(payload["search_recency_filter"], "oneWeek")


class TestHardwareValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def test_reject_headline_like_name(self) -> None:
        from prompts.analysis_prompts import validate_hardware_product

        ok, reason = validate_hardware_product(
            {
                "name": "朱啸虎投资的AI眼镜",
                "website": "unknown",
                "description": "在 2025 CES 上亮相并创下近 400 万美金众筹记录的 AI 眼镜。",
                "why_matters": "投资新闻标题，非明确品牌与官网，容易误提取。",
                "category": "hardware",
                "is_hardware": True,
                "dark_horse_index": 4,
                "criteria_met": ["media_coverage"],
            }
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "name looks like news headline")

    def test_downgrade_high_score_unknown_website(self) -> None:
        from prompts.analysis_prompts import validate_hardware_product

        product = {
            "name": "SomeWearable",
            "website": "unknown",
            "description": "A wearable AI device with a clear single use case and early buzz.",
            "why_matters": "形态创新 + 场景清晰，但官网缺失需要人工验证。",
            "category": "hardware",
            "is_hardware": True,
            "dark_horse_index": 4,
            "criteria_met": ["form_innovation", "use_case_clear"],
        }
        ok, reason = validate_hardware_product(product)
        self.assertTrue(ok)
        self.assertEqual(reason, "passed")
        # Unknown website should be allowed (with manual verification), without mutating score.
        self.assertEqual(product.get("dark_horse_index"), 4)
        self.assertTrue(product.get("needs_verification"))


if __name__ == "__main__":
    unittest.main()
