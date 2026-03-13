"""Tests for tools/auto_publish.py field preservation."""

from __future__ import annotations

from tools import auto_publish


def test_build_featured_product_keeps_en_localized_fields():
    raw = {
        "name": "AgentMail",
        "website": "https://agentmail.to",
        "description": "面向 AI Agent 的邮件基础设施平台。",
        "description_en": "Email infrastructure platform designed for AI agents.",
        "why_matters": "获 General Catalyst 领投 $6M seed。",
        "why_matters_en": "Raised a $6M seed round led by General Catalyst.",
        "latest_news": "2026-03 完成种子轮融资",
        "latest_news_en": "2026-03: Closed seed financing.",
        "dark_horse_index": 3,
        "category": "agent",
    }

    product = auto_publish.build_featured_product(raw)

    assert product["description_en"] == raw["description_en"]
    assert product["why_matters_en"] == raw["why_matters_en"]
    assert product["latest_news_en"] == raw["latest_news_en"]
