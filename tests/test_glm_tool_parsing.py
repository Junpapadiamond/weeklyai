"""
GLM tool parsing + hardware validation tests (unittest, no network).

Run:
  python3 tests/test_glm_tool_parsing.py
"""

from __future__ import annotations

import os
import sys
import unittest


def _ensure_import_paths() -> None:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    crawler_root = os.path.join(repo_root, "crawler")
    if crawler_root not in sys.path:
        sys.path.insert(0, crawler_root)


class TestGLMToolParsing(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def _client(self):
        from utils.glm_client import GLMClient

        # Bypass __init__ (no API key / no SDK calls needed for parsing helpers).
        return GLMClient.__new__(GLMClient)

    def test_extract_search_items_from_search_result_list(self) -> None:
        client = self._client()
        message = {
            "tool_calls": [
                {
                    "search_result": [
                        {"title": "A", "link": "https://a.example", "content": "aaa"},
                        {"title": "B", "url": "https://b.example", "snippet": "bbb"},
                    ]
                }
            ]
        }
        items = client._extract_tool_search_items(message)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["title"], "A")
        self.assertEqual(items[0]["link"], "https://a.example")

    def test_extract_search_items_from_nested_web_search(self) -> None:
        client = self._client()
        message = {
            "tool_calls": [
                {
                    "web_search": {
                        "results": [
                            {"title": "C", "url": "https://c.example", "content": "ccc"},
                        ]
                    }
                }
            ]
        }
        items = client._extract_tool_search_items(message)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://c.example")

    def test_extract_search_items_from_function_arguments(self) -> None:
        client = self._client()
        message = {
            "tool_calls": [
                {
                    "function": {
                        "arguments": '{"search_result":[{"title":"D","link":"https://d.example","content":"ddd"}]}'
                    }
                }
            ]
        }
        items = client._extract_tool_search_items(message)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["link"], "https://d.example")

    def test_dedupe_by_url(self) -> None:
        client = self._client()
        message = {
            "tool_calls": [
                {"search_result": [{"title": "E", "url": "https://e.example", "content": "1"}]},
                {"search_result": [{"title": "E2", "url": "https://e.example", "content": "2"}]},
            ]
        }
        items = client._extract_tool_search_items(message)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://e.example")


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
        self.assertEqual(product.get("dark_horse_index"), 3)
        self.assertEqual((product.get("extra") or {}).get("downgrade_reason"), "missing_official_website")


if __name__ == "__main__":
    unittest.main()

