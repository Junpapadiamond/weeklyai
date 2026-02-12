"""
Tests for Weekly Dark Horses freshness rule.

Goal:
- When there are fresh candidates within DARK_HORSE_FRESH_DAYS, never backfill older products
  just to reach `limit` (otherwise "本周黑马" shows non-week items).
- Only when there are zero fresh candidates, fallback to top scored candidates.

Run:
  cd <project-root>
  python -m pytest tests/test_darkhorse_freshness.py -v
"""

import os
import sys
from datetime import datetime, timedelta
from unittest import mock

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))


def _make_product(name: str, days_ago: int, score: int = 4, funding: str = "$0M"):
    dt = datetime.now() - timedelta(days=days_ago)
    return {
        "_id": name,
        "name": name,
        "website": f"https://{name.lower()}.example",
        "dark_horse_index": score,
        "funding_total": funding,
        "discovered_at": dt.strftime("%Y-%m-%d"),
        "is_hardware": False,
        "source": "test",
        "why_matters": "test",
    }


class TestDarkHorseFreshness:
    def test_does_not_backfill_old_products_when_some_fresh_exist(self):
        """
        If there is at least one fresh candidate (within FRESH_DAYS),
        results should only contain fresh candidates (and optional top sticky),
        not older products.
        """
        from app.services.product_service import ProductService

        fresh = _make_product("FreshOne", days_ago=1, score=5, funding="$100M")
        old = _make_product("OldOne", days_ago=30, score=5, funding="$500M")

        with mock.patch.object(ProductService, "_load_products", return_value=[fresh, old]):
            # Freeze config to a known value for this test
            with mock.patch("app.services.product_service.Config.DARK_HORSE_FRESH_DAYS", 5), \
                 mock.patch("app.services.product_service.Config.DARK_HORSE_STICKY_DAYS", 10):
                res = ProductService.get_dark_horse_products(limit=10, min_index=4)

        names = {p["name"] for p in res}
        assert "FreshOne" in names
        # Old should NOT be backfilled to reach limit
        assert "OldOne" not in names

    def test_fallback_kicks_in_only_when_no_fresh_candidates(self):
        """
        If there are zero fresh candidates, fallback can return older top scored items.
        """
        from app.services.product_service import ProductService

        old_a = _make_product("OldA", days_ago=30, score=5, funding="$500M")
        old_b = _make_product("OldB", days_ago=40, score=4, funding="$10M")

        with mock.patch.object(ProductService, "_load_products", return_value=[old_a, old_b]):
            with mock.patch("app.services.product_service.Config.DARK_HORSE_FRESH_DAYS", 5), \
                 mock.patch("app.services.product_service.Config.DARK_HORSE_STICKY_DAYS", 10):
                res = ProductService.get_dark_horse_products(limit=2, min_index=4)

        names = [p["name"] for p in res]
        assert "OldA" in names
        assert "OldB" in names
