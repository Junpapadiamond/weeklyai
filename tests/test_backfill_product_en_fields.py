"""Tests for tools/backfill_product_en_fields.py."""

from __future__ import annotations

import json
import os
import sys

from tools import backfill_product_en_fields as backfill


def _write_json(path: str, payload: object) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _read_json(path: str) -> object:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_candidate_fields_respects_only_missing():
    product = {
        "description": "中文描述",
        "description_en": "Existing EN",
        "why_matters": "中文理由",
        "latest_news": "中文动态",
    }

    only_missing = backfill._candidate_fields(product, ["description", "why_matters", "latest_news"], only_missing=True)
    assert only_missing == ["why_matters", "latest_news"]

    overwrite = backfill._candidate_fields(product, ["description", "why_matters", "latest_news"], only_missing=False)
    assert overwrite == ["description", "why_matters", "latest_news"]


def test_dry_run_does_not_modify_file(tmp_path, monkeypatch):
    input_file = tmp_path / "products_featured.json"
    payload = [
        {"name": "A", "description": "中文描述", "why_matters": "中文理由", "latest_news": "中文动态"},
        {"name": "B", "description": "中文描述B", "why_matters": "中文理由B", "latest_news": "中文动态B"},
    ]
    _write_json(str(input_file), payload)
    before = _read_json(str(input_file))

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "backfill_product_en_fields.py",
            "--input",
            str(input_file),
            "--dry-run",
            "--fields",
            "description,why_matters,latest_news",
        ],
    )
    rc = backfill.main()
    after = _read_json(str(input_file))

    assert rc == 0
    assert after == before


def test_no_provider_skips_without_data_damage(tmp_path, monkeypatch):
    input_file = tmp_path / "products_featured.json"
    payload = [{"name": "A", "description": "中文描述", "why_matters": "中文理由"}]
    _write_json(str(input_file), payload)
    before = _read_json(str(input_file))

    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "backfill_product_en_fields.py",
            "--input",
            str(input_file),
            "--provider",
            "auto",
            "--fields",
            "description,why_matters",
        ],
    )

    rc = backfill.main()
    after = _read_json(str(input_file))

    assert rc == 0
    assert after == before
    assert os.path.exists(input_file)
