"""Regression coverage for the task-specific Clutch example and shipped-cache repair."""
import json
from pathlib import Path

import pytest

from app.services.demo_contract import compatible_cache_keys, validate_experience
from app.services import demo_experiences as service


ROOT = Path(__file__).resolve().parents[1]
NAME = "a4c21dccf77c1b8009a70798-ecbdc5d85e669caaec13eaaa.json"


def clutch_entry():
    return json.loads((ROOT / "backend/data/demos" / NAME).read_text(encoding="utf-8"))


def test_clutch_shipped_repair_wins_over_stale_database_without_generation(monkeypatch):
    catalog = json.loads((ROOT / "backend/data/products_featured.json").read_text(encoding="utf-8"))
    product = next(product for product in catalog if product["name"] == "Clutch Security")
    entry = clutch_entry()
    assert entry["cache_key"] in compatible_cache_keys(product)
    monkeypatch.setenv("DEMO_PUBLISHED_PATH", str(ROOT / "backend/data/demos"))
    monkeypatch.setattr(service, "generate_spec", lambda _: pytest.fail("Playback must never generate"))

    class UnavailableStore:
        def get(self, key):
            pytest.fail("The shipped correction must supersede an old database entry")

    prepared = service.ready_experience(product, UnavailableStore())
    assert prepared["origin"] == "curated"
    assert prepared["spec"] == validate_experience(entry["spec"])
    mirror = (ROOT / "crawler/data/demos" / NAME).read_bytes()
    assert mirror == (ROOT / "backend/data/demos" / NAME).read_bytes()


def test_clutch_request_examples_follow_each_task_without_stale_cross_task_logs():
    spec = validate_experience(clutch_entry()["spec"])
    tasks, requests = spec["steps"]
    service._validate_generated_artifacts(spec)
    outcomes = []
    for task in tasks["options"]:
        eligible = [option for option in requests["options"]
                    if option["when"] == {"step_id": tasks["id"], "option_id": task["id"]}]
        assert len(eligible) == 1
        outcome = eligible[0]["artifact"]
        assert len(outcome["items"]) == 3
        outcomes.append(outcome)
    # Switching tasks must change the request examples and the actual decisions.
    assert outcomes[0]["input"] != outcomes[1]["input"]
    assert outcomes[0]["items"] != outcomes[1]["items"]
    for lang in ("zh", "en"):
        code_text = " ".join(item["detail"][lang] for item in tasks["options"][0]["artifact"]["items"])
        assert ("环境变量" if lang == "zh" else "environment variables") in code_text
        assert ("测试凭证" if lang == "zh" else "test credentials") in code_text
        assert ("完全阻止" if lang == "zh" else "completely block") not in code_text
