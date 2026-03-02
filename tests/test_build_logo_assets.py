"""Integration-style tests for crawler.tools.build_logo_assets."""

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from crawler.tools import build_logo_assets as logo_builder


class _DummyUploader:
    def __init__(self):
        self.uploaded = []

    def upload(self, object_key: str, payload: bytes) -> None:
        self.uploaded.append((object_key, payload))


def _make_config(tmp_path: Path, mode: str = "backfill") -> logo_builder.Config:
    return logo_builder.Config(
        mode=mode,
        write=True,
        input_path=tmp_path / "products_featured.json",
        cache_path=tmp_path / "logo_cache.json",
        report_path=tmp_path / "logo_coverage_report.json",
        backup_dir=tmp_path,
        min_ok_rate=0.5,
        fetch_timeout=5,
        recheck_days=7,
        failure_retry_threshold=3,
        failure_slow_retry_days=7,
        storage_provider="local",
        cdn_base_url="https://cdn.weeklyai.test",
        s3_bucket="",
        s3_region="",
        s3_endpoint="",
        s3_access_key_id="",
        s3_secret_access_key="",
        user_agent="WeeklyAI-Test",
    )


def test_load_logo_cache_migrates_legacy_values(tmp_path):
    cache_path = tmp_path / "logo_cache.json"
    cache_path.write_text(
        json.dumps(
            {
                "example.com": "https://cdn.weeklyai.test/logos/products/example.com/abc.png",
                "foo.com": {
                    "cdn_url": "",
                    "status": "failed",
                    "checked_at": "2026-03-01T00:00:00Z",
                    "fail_count": 4,
                    "last_error": "timeout",
                },
            }
        ),
        encoding="utf-8",
    )

    cache = logo_builder.load_logo_cache(cache_path)

    assert cache["example.com"]["status"] == "ok"
    assert cache["example.com"]["source"] == "manual"
    assert cache["foo.com"]["status"] == "failed"
    assert cache["foo.com"]["fail_count"] == 4


def test_run_updates_logo_status_and_cache(tmp_path, monkeypatch):
    products = [
        {
            "name": "Success",
            "website": "https://success.example.com",
            "description": "ok",
            "why_matters": "ok",
        },
        {
            "name": "Failure",
            "website": "https://failed.example.com",
            "description": "bad",
            "why_matters": "bad",
        },
        {
            "name": "MissingWebsite",
            "website": "unknown",
            "description": "missing",
            "why_matters": "missing",
        },
    ]

    cfg = _make_config(tmp_path)
    cfg.input_path.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
    cfg.cache_path.write_text("{}", encoding="utf-8")

    uploader = _DummyUploader()

    def fake_resolve_logo_asset(session, website, domain, cfg_obj):
        if domain == "success.example.com":
            return b"png-bytes", "site_icon", ""
        return None, "", "timeout"

    monkeypatch.setattr(logo_builder, "uploader_for", lambda _cfg: uploader)
    monkeypatch.setattr(logo_builder, "resolve_logo_asset", fake_resolve_logo_asset)
    monkeypatch.setattr(
        logo_builder,
        "object_key_for",
        lambda domain, payload: (f"logos/products/{domain}/hash.png", "hash"),
    )

    code = logo_builder.run(cfg)
    assert code == 0

    updated_products = json.loads(cfg.input_path.read_text(encoding="utf-8"))
    updated_by_name = {item["name"]: item for item in updated_products}

    success = updated_by_name["Success"]
    assert success["logo_status"] == "ok"
    assert success["logo_url"].startswith("https://cdn.weeklyai.test/logos/products/success.example.com/")

    failure = updated_by_name["Failure"]
    assert failure["logo_status"] == "failed"
    assert failure["logo_url"] == ""
    assert "logo_error_reason" in failure

    missing = updated_by_name["MissingWebsite"]
    assert missing["logo_status"] == "missing"

    cache = json.loads(cfg.cache_path.read_text(encoding="utf-8"))
    assert cache["success.example.com"]["status"] == "ok"
    assert cache["failed.example.com"]["status"] == "failed"

    report = json.loads(cfg.report_path.read_text(encoding="utf-8"))
    assert report["metrics"]["total"] == 3
    assert report["metrics"]["logo_ok"] == 1
    assert report["metrics"]["logo_failed"] == 1
    assert report["metrics"]["logo_missing"] == 1
    assert uploader.uploaded
