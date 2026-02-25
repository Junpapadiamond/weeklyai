"""
Tests for CN news merge strategy in cn_news_only.py.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "crawler"))

from tools import cn_news_only as cn_news  # noqa: E402


def _blog(name: str, *, source: str, website: str, market: str = "", published_at: str = "2026-02-25T00:00:00Z"):
    item = {
        "name": name,
        "source": source,
        "website": website,
        "published_at": published_at,
        "description": name,
        "extra": {},
    }
    if market:
        item["market"] = market
        item["extra"]["news_market"] = market
    return cn_news._with_market_meta(item)


def test_merge_cn_blogs_prefers_fresh_cn_slice():
    existing = [
        _blog("us-item", source="hackernews", website="https://us.example.com"),
        _blog("cn-old", source="cn_news", website="https://cn-old.example.com"),
    ]
    baseline = [_blog("cn-base", source="cn_news", website="https://cn-base.example.com")]
    fresh_cn = [_blog("cn-fresh", source="cn_news", website="https://cn-fresh.example.com")]

    merged, strategy = cn_news.merge_cn_blogs(
        existing,
        fresh_cn,
        baseline_blogs=baseline,
        allowed_year=2026,
    )

    names = {item["name"] for item in merged}
    assert strategy == "fresh"
    assert names == {"us-item", "cn-fresh"}
    assert cn_news.count_market(merged, "cn") == 1


def test_merge_cn_blogs_uses_baseline_when_fresh_cn_is_empty():
    existing = [
        _blog("us-item", source="hackernews", website="https://us.example.com"),
        _blog("cn-old", source="cn_news", website="https://cn-old.example.com"),
    ]
    baseline = [_blog("cn-base", source="cn_news", website="https://cn-base.example.com")]

    merged, strategy = cn_news.merge_cn_blogs(
        existing,
        [],
        baseline_blogs=baseline,
        allowed_year=2026,
    )

    names = {item["name"] for item in merged}
    assert strategy == "baseline"
    assert names == {"us-item", "cn-base"}
    assert cn_news.count_market(merged, "cn") == 1


def test_merge_cn_blogs_falls_back_to_existing_cn_when_no_baseline():
    existing = [
        _blog("us-item", source="hackernews", website="https://us.example.com"),
        _blog("cn-old", source="cn_news", website="https://cn-old.example.com"),
    ]

    merged, strategy = cn_news.merge_cn_blogs(
        existing,
        [],
        baseline_blogs=[],
        allowed_year=2026,
    )

    names = {item["name"] for item in merged}
    assert strategy == "existing"
    assert names == {"us-item", "cn-old"}
    assert cn_news.count_market(merged, "cn") == 1
