"""First-value artifacts are additive to cached v2 examples, required for new output."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.services import demo_experiences as service
from app.services.demo_contract import cache_key, validate_experience


PRODUCT = {"_id": "artifact-test", "name": "Artifact test", "website": "https://artifact.example",
           "description": "Example product"}


def bilingual(zh, en):
    return {"zh": zh, "en": en}


@pytest.fixture
def artifact():
    return {"kind": "excerpt", "input_label": bilingual("虚构回答", "Fictional answer"),
            "output_label": bilingual("示例主题", "Example theme"),
            "input": bilingual("我不想透露具体地址。", "I do not want to share my exact address."),
            "output": bilingual("位置隐私", "Location privacy"),
            "emphasis": bilingual("具体地址", "my exact address")}


@pytest.fixture
def legacy_spec():
    return {"version": 2, "confidence": "illustrative", "tier": "workflow",
            "headline": bilingual("研究问题示例", "Example research question"),
            "scenario": bilingual("探索虚构回答与主题的关系。", "Explore a fictional answer and its related theme."),
            "takeaway": bilingual("下一步需要真实研究。", "Real research is still needed."),
            "sources": [{"url": PRODUCT["website"], "label": bilingual("产品资料", "Product information")}],
            "steps": [{"id": step_id, "widget": "choice", "title": bilingual("选择示例", "Choose an example"),
                       "instruction": bilingual("查看预先编写的示例。", "Inspect a prepared example."),
                       "example_data": True,
                       "options": [{"id": str(index), "label": bilingual("位置隐私" if index == 0 else "健身水平",
                                                                            "Location privacy" if index == 0 else "Fitness level"),
                                    "output": bilingual("示例研究方向，尚待验证。", "An example research direction, still unverified.")}
                                   for index in range(2)]}
                      for step_id in ("example", "focus", "review")]}


def with_artifacts(spec, artifact):
    result = copy.deepcopy(spec)
    for option in result["steps"][0]["options"]:
        option["artifact"] = copy.deepcopy(artifact)
    return result


def test_legacy_contract_and_cache_key_are_unchanged(legacy_spec):
    assert validate_experience(legacy_spec) == legacy_spec
    assert cache_key(PRODUCT) == "1a4fc26d9c5c0b33629e8abf-390f262401cc017df2ac6817"


def test_one_example_is_sufficient_but_sections_remain_bounded(legacy_spec):
    legacy_spec["steps"] = legacy_spec["steps"][:1]
    assert len(validate_experience(legacy_spec)["steps"]) == 1
    legacy_spec["steps"] = []
    with pytest.raises(ValueError, match="1–6 example sections"):
        validate_experience(legacy_spec)
    legacy_spec["steps"] = [{} for _ in range(7)]
    with pytest.raises(ValueError, match="1–6 example sections"):
        validate_experience(legacy_spec)


def test_every_existing_cache_remains_readable_without_artifact_migration():
    paths = list((Path(__file__).resolve().parents[1] / "backend/data/demos").glob("*.json"))
    assert paths
    for path in paths:
        spec = json.loads(path.read_text(encoding="utf-8"))["spec"]
        assert validate_experience(spec) == spec, path.name


def test_legacy_replay_does_not_generate_or_reserve_credit(legacy_spec, monkeypatch):
    entry = service.envelope(PRODUCT, legacy_spec, "pregenerated")
    monkeypatch.setattr(service, "published", lambda: {})
    monkeypatch.setattr(service, "generate_spec", lambda _: pytest.fail("Replay must not generate"))
    monkeypatch.setattr(service, "provider_available", lambda: pytest.fail("Replay needs no provider"))
    store = SimpleNamespace(get=lambda key: entry, reserve=lambda *args: pytest.fail("Replay must not reserve credits"))
    body, status = service.prepare_experience(PRODUCT, "visitor", store)
    assert status == 200 and body["cached"] is True
    assert body["experience"]["spec"] == legacy_spec


def test_artifact_and_focus_survive_validation_and_unknown_fields_are_removed(legacy_spec, artifact):
    spec = with_artifacts(legacy_spec, artifact)
    spec["focus_step_id"] = "review"
    spec["steps"][0]["options"][0]["artifact"].update(html="<script>alert(1)</script>", url="https://injected.example", code="alert(1)")
    spec["steps"][0]["options"][0]["artifact"]["input"]["html"] = "<img src=x>"
    validated = validate_experience(spec)
    assert validated["focus_step_id"] == "review"
    assert validated["steps"][0]["options"][0]["artifact"] == artifact


@pytest.mark.parametrize("kind", ["iframe", [], {}, None])
def test_artifact_kind_rejects_unknown_or_malformed_values(legacy_spec, artifact, kind):
    artifact["kind"] = kind
    with pytest.raises(ValueError, match="Unsupported artifact kind"):
        validate_experience(with_artifacts(legacy_spec, artifact))


@pytest.mark.parametrize("focus", ["missing", "", None, [], 3])
def test_focus_must_reference_an_existing_step(legacy_spec, focus):
    legacy_spec["focus_step_id"] = focus
    with pytest.raises(ValueError):
        validate_experience(legacy_spec)


@pytest.mark.parametrize("language,emphasis", [("en", "not in the passage"), ("zh", "文中不存在"), ("en", " ")])
def test_highlight_is_an_exact_nonempty_substring_in_each_language(legacy_spec, artifact, language, emphasis):
    artifact["emphasis"][language] = emphasis
    with pytest.raises(ValueError):
        validate_experience(with_artifacts(legacy_spec, artifact))


@pytest.mark.parametrize("field,limit", [("input_label", 40), ("output_label", 40), ("input", 220), ("output", 220), ("emphasis", 100)])
def test_artifact_copy_is_bounded_without_truncating_meaning(legacy_spec, artifact, field, limit):
    artifact[field]["en"] = "x" * (limit + 1)
    with pytest.raises(ValueError):
        validate_experience(with_artifacts(legacy_spec, artifact))


@pytest.mark.parametrize("text", ["https://vendor.example/result", "www.vendor.example", "javascript:alert(1)",
                                 "<script>alert(1)</script>", "<img src=x onerror=alert(1)>", "Accuracy 96%",
                                 "Latency: 30", "Completes in 20ms", "Exported: demo.png",
                                 "Agent deployed in company data center", "Connected SEC data stream",
                                 "Completed interviews with customers", "Video generated", "文件已保存本地"])
def test_artifact_rejects_unsafe_representation_and_execution_claims(legacy_spec, artifact, text):
    artifact["output"]["en"] = text
    with pytest.raises(ValueError, match="Artifact text"):
        validate_experience(with_artifacts(legacy_spec, artifact))


def test_sequence_items_are_bounded_and_plain_data(legacy_spec, artifact):
    artifact["kind"] = "sequence"
    artifact["items"] = [{"label": bilingual("开场", "Opening"), "detail": bilingual("介绍问题。", "Introduce the problem."),
                          "image_url": "https://injected.example/shot.png"},
                         {"label": bilingual("结尾", "Ending"), "detail": bilingual("邀请了解产品。", "Invite viewers to learn more.")}]
    validated = validate_experience(with_artifacts(legacy_spec, artifact))["steps"][0]["options"][0]["artifact"]
    assert len(validated["items"]) == 2
    assert "image_url" not in validated["items"][0]
    for invalid_items in ([], artifact["items"][:1], artifact["items"] * 3, "text"):
        invalid = {**artifact, "items": invalid_items}
        with pytest.raises(ValueError, match="Artifact items"):
            validate_experience(with_artifacts(legacy_spec, invalid))
    artifact["kind"] = "excerpt"
    with pytest.raises(ValueError, match="Artifact items"):
        validate_experience(with_artifacts(legacy_spec, artifact))


def mock_completions(monkeypatch, responses):
    monkeypatch.setenv("DEMO_API_PROTOCOL", "anthropic")
    monkeypatch.setenv("DEMO_API_KEY", "test-key")
    monkeypatch.setenv("DEMO_API_BASE_URL", "https://provider.invalid/v1")
    monkeypatch.setattr(service, "providers", lambda: [("demo", "https://provider.invalid/v1", "test-key", "claude")])
    monkeypatch.setattr(service.requests, "post", lambda *args, **kwargs: pytest.fail("Tests must not call a provider"))
    sent = []
    remaining = iter(responses)

    def complete(base, endpoint, headers, payload, deadline):
        sent.append(copy.deepcopy(payload))
        return {"content": [{"type": "text", "text": json.dumps(next(remaining))}], "stop_reason": "end_turn"}

    completion = Mock(side_effect=complete)
    monkeypatch.setattr(service, "_completion", completion)
    return completion, sent


def test_missing_artifact_in_one_opening_branch_uses_existing_repair(legacy_spec, artifact, monkeypatch):
    complete_spec = with_artifacts(legacy_spec, artifact)
    incomplete = copy.deepcopy(complete_spec)
    del incomplete["steps"][0]["options"][1]["artifact"]
    completion, sent = mock_completions(monkeypatch, [incomplete, complete_spec])
    result = service.generate_spec(PRODUCT)
    assert result == validate_experience(complete_spec)
    assert completion.call_count == 2
    assert "Every first-step option needs a concrete artifact" in sent[1]["messages"][-1]["content"]
    prompt = sent[0]["messages"][0]["content"]
    assert "EVERY option of the FIRST step" in prompt
    assert "1-6 independent example sections" in prompt
    assert "one focused input/output artifact" in prompt
    assert "editable example brief" not in prompt
    assert "exact nonempty substring" in prompt
    assert '"artifact":' in prompt


def test_new_generation_without_artifacts_fails_after_one_repair(legacy_spec, monkeypatch):
    completion, _ = mock_completions(monkeypatch, [legacy_spec, legacy_spec])
    with pytest.raises(service.GenerationFailure) as error:
        service.generate_spec(PRODUCT)
    assert error.value.code == "GENERATION_INVALID_RESPONSE"
    assert completion.call_count == 2
    assert validate_experience(legacy_spec) == legacy_spec


def test_compact_artifact_round_trip_keeps_localized_highlight_and_items(legacy_spec, artifact, monkeypatch):
    artifact["kind"] = "list"
    artifact["items"] = [{"label": bilingual("问题", "Question"), "detail": bilingual("愿意分享哪些信息？", "What information would you share?")},
                         {"label": bilingual("假设", "Hypothesis"), "detail": bilingual("允许选择分享范围。", "Let people choose what to share.")}]
    complete_spec = with_artifacts(legacy_spec, artifact)

    def compact(value):
        if isinstance(value, dict):
            if set(value) == {"zh", "en"}:
                return [value["zh"], value["en"]]
            return {key: compact(part) for key, part in value.items()}
        return [compact(part) for part in value] if isinstance(value, list) else value

    wire = compact(complete_spec)
    wire["format"] = "compact-v1"
    completion, _ = mock_completions(monkeypatch, [wire])
    result = service.generate_spec(PRODUCT)
    assert result["steps"] == complete_spec["steps"]
    assert completion.call_count == 1
