"""
Logo cleanup tests (unittest, no network).

Run:
  PYTHONPATH=backend:crawler python -m pytest tests/test_fix_logos.py -v
"""

from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch


def _ensure_import_paths() -> None:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    crawler_root = os.path.join(repo_root, "crawler")
    if crawler_root not in sys.path:
        sys.path.insert(0, crawler_root)


class TestFixLogosHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def test_sanitize_clears_bad_logo_field_but_keeps_valid_logo_url(self) -> None:
        from tools.fix_logos import _sanitize_logo_fields

        item = {
            "logo": "https://www.google.com/s2/favicons?domain=anduril.com&sz=128",
            "logo_url": "https://www.anduril.com/assets/favicon/favicon.xxWKiVhdqu.ico",
            "logo_source": "google",
        }

        changed = _sanitize_logo_fields(item)

        self.assertTrue(changed)
        self.assertEqual(item["logo"], "")
        self.assertEqual(item["logo_url"], "https://www.anduril.com/assets/favicon/favicon.xxWKiVhdqu.ico")
        self.assertEqual(item["logo_source"], "")

    @patch("tools.fix_logos.get_logo_url")
    def test_process_product_keeps_valid_logo_after_sanitizing_stale_fields(self, mock_get_logo_url) -> None:
        from tools.fix_logos import process_product

        item = {
            "name": "Anduril",
            "website": "https://www.anduril.com",
            "logo": "https://www.google.com/s2/favicons?domain=anduril.com&sz=128",
            "logo_url": "https://www.anduril.com/assets/favicon/favicon.xxWKiVhdqu.ico",
            "logo_source": "google",
        }

        result = process_product(item)

        mock_get_logo_url.assert_not_called()
        self.assertEqual(result["logo"], "")
        self.assertEqual(result["logo_url"], "https://www.anduril.com/assets/favicon/favicon.xxWKiVhdqu.ico")
        self.assertEqual(result["logo_source"], "")

    @patch("tools.fix_logos.get_logo_url", return_value=(None, None))
    def test_process_product_clears_low_confidence_logo_when_replacement_missing(self, _mock_get_logo_url) -> None:
        from tools.fix_logos import process_product

        item = {
            "name": "Dreame Pilot 20",
            "website": "https://global.dreame.com",
            "logo_url": "https://favicon.bing.com/favicon.ico?url=global.dreame.com&size=128",
            "logo_source": "bing",
        }

        result = process_product(item)

        self.assertEqual(result["logo_url"], "")
        self.assertEqual(result["logo_source"], "")

    def test_low_confidence_detector_checks_legacy_logo_field(self) -> None:
        from tools.fix_logos import _is_low_confidence_logo

        item = {
            "logo": "https://www.google.com/s2/favicons?domain=lmarena.ai&sz=128",
            "logo_url": "https://logo.clearbit.com/lmarena.ai",
            "logo_source": "clearbit",
        }

        self.assertTrue(_is_low_confidence_logo(item))

    def test_should_fix_product_only_missing_respects_existing_logo(self) -> None:
        from tools.fix_logos import _should_fix_product

        self.assertTrue(
            _should_fix_product({"logo_url": "", "logo": ""}, only_missing=True)
        )
        self.assertFalse(
            _should_fix_product(
                {"logo_url": "https://cursor.com/favicon.ico", "logo": ""},
                only_missing=True,
            )
        )

    def test_should_fix_product_default_still_flags_low_confidence_logo(self) -> None:
        from tools.fix_logos import _should_fix_product

        item = {
            "logo_url": "https://favicon.bing.com/favicon.ico?url=global.dreame.com&size=128",
            "logo_source": "bing",
            "website": "https://global.dreame.com",
        }

        self.assertTrue(_should_fix_product(item, only_missing=False))


if __name__ == "__main__":
    unittest.main()
