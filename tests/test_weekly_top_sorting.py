"""
Tests for weekly-top sort modes.
"""

import os
import sys
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend", "app", "services"))

import product_sorting as sorting  # noqa: E402


def _build_product(
    name: str,
    *,
    days_ago: int,
    hot_score: float,
    dark_horse_index: int,
    funding: str,
    hours_ago: int = 0
):
    timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
    return {
        "name": name,
        "dark_horse_index": dark_horse_index,
        "hot_score": hot_score,
        "funding_total": funding,
        "discovered_at": timestamp.isoformat(timespec="seconds"),
    }


def test_weekly_top_sort_modes_are_distinct_and_reasonable():
    products = [
        _build_product(
            "HotOld",
            days_ago=120,
            hot_score=98,
            dark_horse_index=5,
            funding="$1M",
        ),
        _build_product(
            "FreshBalanced",
            days_ago=2,
            hot_score=72,
            dark_horse_index=3,
            funding="$20M",
        ),
        _build_product(
            "FreshLowHeatRich",
            days_ago=0,
            hours_ago=2,
            hot_score=40,
            dark_horse_index=2,
            funding="$1.2B",
        ),
    ]

    trending = sorting.sort_weekly_top(products, sort_by="trending")
    recency = sorting.sort_weekly_top(products, sort_by="recency")
    composite = sorting.sort_weekly_top(products, sort_by="composite")

    assert trending[0]["name"] == "HotOld"
    assert recency[0]["name"] == "FreshLowHeatRich"
    assert composite[0]["name"] == "FreshBalanced"
    assert trending[0]["name"] != recency[0]["name"]
    assert composite[0]["name"] != trending[0]["name"]


def test_weekly_top_sort_mode_keeps_legacy_aliases_compatible():
    assert sorting.resolve_weekly_top_sort("score") == "trending"
    assert sorting.resolve_weekly_top_sort("date") == "recency"
    assert sorting.resolve_weekly_top_sort("funding") == "funding"
    assert sorting.resolve_weekly_top_sort("unknown-mode") == "composite"
