"""
Regression checks for CN market preservation during blog merge.
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


def test_cn_slice_is_preserved_from_baseline_when_current_news_is_non_cn_only():
    existing = [
        _blog("us-1", source="hackernews", website="https://us-1.example.com"),
        _blog("us-2", source="reddit", website="https://us-2.example.com"),
    ]
    baseline = [
        _blog("cn-keep", source="cn_news", website="https://cn-keep.example.com"),
    ]

    merged, strategy = cn_news.merge_cn_blogs(
        existing,
        [],
        baseline_blogs=baseline,
        allowed_year=2026,
    )

    assert strategy == "baseline"
    assert cn_news.count_market(merged, "cn") == 1
    assert cn_news.count_market(merged, "us") == 2


def test_cn_slice_can_be_zero_when_no_baseline_and_no_existing_cn():
    existing = [
        _blog("us-1", source="hackernews", website="https://us-1.example.com"),
    ]

    merged, strategy = cn_news.merge_cn_blogs(
        existing,
        [],
        baseline_blogs=[],
        allowed_year=2026,
    )

    assert strategy == "existing"
    assert cn_news.count_market(merged, "cn") == 0
    assert cn_news.count_market(merged, "us") == 1
