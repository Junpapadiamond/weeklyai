"""Tests for tools/backfill_primary_zh_fields.py."""

from __future__ import annotations

import json
import sys

from tools import backfill_primary_zh_fields as zh_backfill


def _write_json(path: str, payload: object) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _read_json(path: str) -> object:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_needs_zh_translation_detects_english_and_japanese():
    assert zh_backfill._needs_zh_translation("AI infrastructure platform for agent workflows.")
    assert zh_backfill._needs_zh_translation("日本発のAI基盤モデル企業。")
    assert not zh_backfill._needs_zh_translation("中文描述，支持企业级工作流。")
    assert not zh_backfill._needs_zh_translation("unknown")


def test_collect_work_items_preserves_non_zh_original_into_en_fields():
    records = [
        {
            "name": "Sample",
            "description": "English description only.",
            "why_matters": "中文理由，含具体数字 30%。",
            "latest_news": "日本語ニュースの概要。",
        }
    ]

    work_items, preserved_en, skipped_fields, scanned_fields = zh_backfill._collect_work_items(
        records,
        target="products",
        overwrite_en=False,
    )

    assert scanned_fields == 3
    assert preserved_en == 2
    assert skipped_fields == 1
    assert len(work_items) == 2
    assert records[0]["description_en"] == "English description only."
    assert records[0]["latest_news_en"] == "日本語ニュースの概要。"
    assert "why_matters_en" not in records[0]


def test_dry_run_does_not_modify_file(tmp_path, monkeypatch):
    input_file = tmp_path / "products_featured.json"
    payload = [
        {
            "name": "Rhoda AI",
            "website": "https://rhoda.ai",
            "description": "Palo Alto-based AI startup training foundational robotics models.",
            "why_matters": "$450M Series A with strong early momentum.",
        }
    ]
    _write_json(str(input_file), payload)
    before = _read_json(str(input_file))

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "backfill_primary_zh_fields.py",
            "--targets",
            "products",
            "--products-input",
            str(input_file),
            "--dry-run",
        ],
    )

    rc = zh_backfill.main()
    after = _read_json(str(input_file))

    assert rc == 0
    assert after == before
