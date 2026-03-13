"""
Data verifier tests (unittest, no network).

Run:
  python3 tests/test_data_verifier.py
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


class TestRegionBucketization(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def test_bucketize_eu_country_flag(self) -> None:
        from utils.data_verifier import bucketize_region

        self.assertEqual(bucketize_region("🇩🇪"), "🇪🇺")

    def test_bucketize_jp_flag(self) -> None:
        from utils.data_verifier import bucketize_region

        self.assertEqual(bucketize_region("🇯🇵"), "🇯🇵🇰🇷")

    def test_bucketize_empty(self) -> None:
        from utils.data_verifier import bucketize_region

        self.assertIsNone(bucketize_region(""))


class TestRegionInference(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def test_infer_from_tld_cn(self) -> None:
        from utils.data_verifier import infer_region_bucket

        bucket, reason = infer_region_bucket(website="https://foo.cn", description="", why_matters="")
        self.assertEqual(bucket, "🇨🇳")
        self.assertIn("domain_tld", reason)

    def test_infer_from_tld_jp(self) -> None:
        from utils.data_verifier import infer_region_bucket

        bucket, reason = infer_region_bucket(website="https://example.co.jp", description="", why_matters="")
        self.assertEqual(bucket, "🇯🇵🇰🇷")
        self.assertIn("domain_tld", reason)

    def test_infer_from_text_korea(self) -> None:
        from utils.data_verifier import infer_region_bucket

        bucket, reason = infer_region_bucket(website="", description="韩国生成式AI独角兽", why_matters="")
        self.assertEqual(bucket, "🇯🇵🇰🇷")
        self.assertTrue(reason.startswith("text"))


class TestValidationRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def test_placeholder_website_is_error(self) -> None:
        from utils.data_verifier import validate_item_heuristic

        item = {
            "name": "Example",
            "website": "https://example.com",
            "description": "This description is long enough to pass.",
            "logo_url": "https://www.google.com/s2/favicons?domain=example.com&sz=128",
            "region": "🇺🇸",
        }
        issues = validate_item_heuristic(item, file_path="x.json", index=0, check_network="none")
        codes = {i.code for i in issues if i.severity == "ERROR"}
        self.assertIn("website_placeholder", codes)

    def test_missing_logo_is_warn(self) -> None:
        from utils.data_verifier import validate_item_heuristic

        item = {
            "name": "NoLogo",
            "website": "https://nol.ogo",
            "description": "This description is long enough to pass.",
            "region": "🇺🇸",
        }
        issues = validate_item_heuristic(item, file_path="x.json", index=0, check_network="none")
        codes = {i.code for i in issues if i.severity == "WARN"}
        self.assertIn("logo_missing", codes)

    def test_region_mismatch_is_warn(self) -> None:
        from utils.data_verifier import validate_item_heuristic

        item = {
            "name": "Upstage",
            "website": "https://upstage.ai",
            "description": "韩国生成式AI独角兽，提供Solar LLM。",
            "logo_url": "https://www.google.com/s2/favicons?domain=upstage.ai&sz=128",
            "region": "🇺🇸",
            "why_matters": "韩国本土市场验证。",
        }
        issues = validate_item_heuristic(item, file_path="x.json", index=0, check_network="none")
        mismatch = [i for i in issues if i.code == "region_mismatch"]
        self.assertTrue(mismatch)
        self.assertEqual(mismatch[0].severity, "WARN")
        self.assertEqual(mismatch[0].suggestion, "🇯🇵🇰🇷")

    def test_product_non_zh_primary_fields_are_errors(self) -> None:
        from utils.data_verifier import validate_item_heuristic

        item = {
            "name": "AgentMail",
            "website": "https://agentmail.to",
            "description": "Email infrastructure platform for AI agents.",
            "why_matters": "Raised $6M seed led by General Catalyst.",
            "latest_news": "2026-03 closed seed financing.",
            "region": "🇺🇸",
        }
        issues = validate_item_heuristic(item, file_path="products_featured.json", index=0, check_network="none")
        by_code = {i.code: i for i in issues}
        self.assertEqual(by_code["description_non_zh"].severity, "ERROR")
        self.assertEqual(by_code["why_matters_non_zh"].severity, "ERROR")
        self.assertEqual(by_code["latest_news_non_zh"].severity, "ERROR")

    def test_blog_non_zh_primary_fields_are_warn_by_default(self) -> None:
        from utils.data_verifier import validate_item_heuristic

        item = {
            "name": "Kotlin creator's new language",
            "website": "https://example.org/post",
            "description": "A new formal language to talk to LLMs.",
            "region": "🌍",
        }
        issues = validate_item_heuristic(item, file_path="blogs_news.json", index=0, check_network="none")
        by_code = {i.code: i for i in issues}
        self.assertEqual(by_code["name_non_zh"].severity, "WARN")
        self.assertEqual(by_code["description_non_zh"].severity, "WARN")

    def test_product_unknown_latest_news_not_flagged_as_non_zh(self) -> None:
        from utils.data_verifier import validate_item_heuristic

        item = {
            "name": "Sample Product",
            "website": "https://example.com",
            "description": "这是一个用于企业自动化流程的中文产品说明，超过二十个字符。",
            "why_matters": "帮助团队把流程执行时间缩短 35%，并提升准确率。",
            "latest_news": "unknown",
            "region": "🇺🇸",
        }
        issues = validate_item_heuristic(item, file_path="products_featured.json", index=0, check_network="none")
        codes = {i.code for i in issues}
        self.assertNotIn("latest_news_non_zh", codes)


class TestReportRendering(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_import_paths()

    def test_md_contains_sections_and_sorted(self) -> None:
        from utils.data_verifier import Issue, Report, render_report_md

        report = Report(
            generated_at="2026-02-10T00:00:00Z",
            mode="heuristic",
            check_network="none",
            files_scanned=1,
            items_scanned=1,
            error_count=1,
            warn_count=1,
            issues=[
                Issue(severity="WARN", code="logo_missing", message="missing logo_url", file="a.json", index=0, name="A"),
                Issue(severity="ERROR", code="missing_name", message="missing name", file="a.json", index=0, name=""),
            ],
        )
        md = render_report_md(report, max_per_severity=10)
        self.assertIn("# WeeklyAI Data Verification Report", md)
        self.assertIn("## Errors (1)", md)
        self.assertIn("## Warnings (1)", md)
        # ERROR should appear before WARN.
        self.assertLess(md.find("missing name"), md.find("missing logo_url"))


if __name__ == "__main__":
    unittest.main()
