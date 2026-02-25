"""
Tests for blog market inference and filtering.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend", "app", "services"))

import product_filters as filters  # noqa: E402


def test_infer_blog_market_handles_source_extra_market_and_region():
    assert filters.infer_blog_market({"source": "cn_news"}) == "cn"
    assert filters.infer_blog_market({"source": "hackernews"}) == "us"
    assert filters.infer_blog_market({"extra": {"news_market": "cn"}}) == "cn"
    assert filters.infer_blog_market({"market": "us"}) == "us"
    assert filters.infer_blog_market({"region": "中国"}) == "cn"
    assert filters.infer_blog_market({"region": "🇺🇸"}) == "us"
    assert filters.infer_blog_market({}) == "global"


def test_filter_blogs_by_market_cn_us_and_hybrid_behaves_as_expected():
    blogs = [
        {"name": "cn-by-source", "source": "cn_news"},
        {"name": "cn-by-extra", "extra": {"news_market": "cn"}},
        {"name": "us-by-source", "source": "reddit"},
        {"name": "global-default"},
    ]

    cn_blogs = filters.filter_blogs_by_market(blogs, "cn")
    us_blogs = filters.filter_blogs_by_market(blogs, "us")
    hybrid_blogs = filters.filter_blogs_by_market(blogs, "hybrid")
    unknown_blogs = filters.filter_blogs_by_market(blogs, "unknown")

    assert [b["name"] for b in cn_blogs] == ["cn-by-source", "cn-by-extra"]
    assert [b["name"] for b in us_blogs] == ["us-by-source"]
    assert hybrid_blogs == blogs
    assert unknown_blogs == blogs


def test_resolve_company_country_does_not_use_discovery_region_fallback():
    product = {
        "name": "Databricks",
        "website": "https://www.databricks.com",
        "region": "🇨🇳",
        "source_region": "🇨🇳",
        "source": "163.com",
    }

    code, source = filters._resolve_company_country(product)
    assert code == ""
    assert source == "unknown"


def test_resolve_company_country_skips_legacy_region_derived_country_fields():
    product = {
        "name": "Wrongly tagged",
        "website": "https://example.com",
        "region": "🇨🇳",
        "source_region": "🇨🇳",
        "source": "cn_news",
        "country_code": "CN",
        "country_name": "China",
        "country_source": "region:search_fallback",
    }

    code, source = filters._resolve_company_country(product)
    assert code == ""
    assert source == "unknown"


def test_resolve_company_country_prefers_explicit_country_field():
    product = {
        "name": "Databricks",
        "website": "https://www.databricks.com",
        "region": "🇨🇳",
        "source_region": "🇨🇳",
        "source": "163.com",
        "company_country": "United States",
    }

    code, source = filters._resolve_company_country(product)
    assert code == "US"
    assert source == "explicit:company_country"
