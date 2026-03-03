"""Search regression tests for keyword recall and basic filtering behavior."""

import os

import pytest

# Use local JSON fallback in tests to avoid flaky network dependency.
os.environ.setdefault("MONGO_URI", "")

from app.services.product_service import ProductService


KEYWORD_MATRIX = [
    "融资",  # 中文功能词
    "硬件",  # 中文分类词
    "视频生成",  # 中文能力词
    "ai agent",  # 英文功能词
    "Databricks",  # 品牌词
    "Mem0",  # 品牌词
    "智能眼镜",  # 中文品类词
    "coinbase",  # why_matters 内品牌词
    "startups raised",  # source_title 英文词
    "AI创业公司 A轮 B轮",  # search_keyword 中英文词
]


@pytest.mark.parametrize("keyword", KEYWORD_MATRIX)
def test_search_keyword_matrix_returns_results(keyword: str):
    result = ProductService.search_products(keyword=keyword, page=1, limit=20)
    assert result["total"] > 0, f"Expected non-empty results for keyword: {keyword}"


def test_search_matches_why_matters_content():
    result = ProductService.search_products(keyword="coinbase", page=1, limit=20)
    names = {item.get("name", "") for item in result["products"]}
    assert "Modveon" in names


def test_search_matches_source_title_content():
    result = ProductService.search_products(keyword="startups raised", page=1, limit=20)
    names = {item.get("name", "") for item in result["products"]}
    assert {"Abridge", "Harvey", "Hippocratic AI"} & names


def test_search_matches_search_keyword_content():
    result = ProductService.search_products(keyword="AI创业公司 A轮 B轮", page=1, limit=20)
    names = {item.get("name", "") for item in result["products"]}
    assert "Mem0" in names


def test_hardware_type_filter_uses_inferred_hardware_logic():
    result = ProductService.search_products(keyword="AI", product_type="hardware", page=1, limit=40)
    assert result["total"] > 0
    assert all(ProductService._is_hardware(item) for item in result["products"])


def test_search_matches_english_localized_fields(monkeypatch):
    sample = [
        {
            "name": "本地化样本",
            "description": "中文描述",
            "description_en": "Agentic workflow builder for AI teams",
            "why_matters": "中文理由",
            "why_matters_en": "Raised $20M seed and shipped in 4 months",
            "category": "agent",
            "website": "https://example.com",
        },
        {
            "name": "仅中文样本",
            "description": "只有中文内容",
            "why_matters": "没有英文字段",
            "category": "other",
            "website": "https://example.org",
        },
    ]

    monkeypatch.setattr(ProductService, "_load_products", lambda: sample)

    by_description = ProductService.search_products(keyword="workflow builder", page=1, limit=20)
    assert by_description["total"] == 1
    assert by_description["products"][0]["name"] == "本地化样本"

    by_why = ProductService.search_products(keyword="20m seed", page=1, limit=20)
    assert by_why["total"] == 1
    assert by_why["products"][0]["name"] == "本地化样本"


def test_search_remains_compatible_when_en_fields_missing(monkeypatch):
    sample = [
        {
            "name": "兼容样本",
            "description": "中文功能描述",
            "why_matters": "支持旧数据结构",
            "category": "other",
            "website": "https://legacy.example.com",
        }
    ]

    monkeypatch.setattr(ProductService, "_load_products", lambda: sample)

    result = ProductService.search_products(keyword="功能描述", page=1, limit=20)
    assert result["total"] == 1
    assert result["products"][0]["name"] == "兼容样本"
