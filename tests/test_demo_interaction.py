"""Offline contract probes shared with the frontend; never call a provider."""
import copy
import json
from pathlib import Path

import pytest

from app.services.demo_contract import _artifact
from app.services.demo_interaction import interaction_snapshot, validate_interaction


GOLDENS = json.loads((Path(__file__).parent / "fixtures/demo_interactions.json").read_text(encoding="utf-8"))


def fixture(kind):
    return copy.deepcopy(GOLDENS[kind])


def art(value, index=0):
    return value["variants"][index]["artifact"]


def bilingual(text):
    return {"zh": text, "en": text}


@pytest.mark.parametrize("kind", list(GOLDENS))
def test_shared_goldens_round_trip_without_mutation(kind):
    value = fixture(kind)
    before = copy.deepcopy(value)
    normalized = validate_interaction(value)
    assert normalized == value == before
    normalized["variants"][0]["brief"]["en"] = "Changed outside the original payload"
    assert value == before


@pytest.mark.parametrize("kind", list(GOLDENS))
def test_compatibility_snapshot_is_a_valid_short_v2_artifact(kind):
    snapshot = interaction_snapshot(validate_interaction(fixture(kind)))
    assert _artifact(snapshot) == snapshot
    assert all(len(snapshot[key][locale]) <= 220 for key in ("input", "output") for locale in ("zh", "en"))


def test_snapshot_resolves_initial_options_even_when_variants_are_reordered():
    value = fixture("editor")
    value["variants"].reverse()
    snapshot = interaction_snapshot(validate_interaction(value))
    assert "conversation" in snapshot["output"]["en"]
    assert "green-tea" not in snapshot["output"]["en"]


def test_snapshot_composition_cannot_create_a_legacy_execution_claim():
    value = fixture("editor")
    art(value)["fields"][0]["label"] = bilingual("Accuracy")
    art(value)["fields"][0]["value"] = bilingual("96")
    normalized = validate_interaction(value)
    snapshot = interaction_snapshot(normalized)
    assert _artifact(snapshot) == snapshot
    assert art(normalized)["fields"][0]["value"]["en"] == "96"


@pytest.mark.parametrize("target", [
    lambda x: x,
    lambda x: x["input_label"],
    lambda x: x["inputs"][0],
    lambda x: x["inputs"][0]["options"][0],
    lambda x: x["variants"][0],
    lambda x: art(x),
    lambda x: art(x)["fields"][0],
    lambda x: art(x)["fields"][0]["value"],
])
def test_unknown_fields_are_rejected_at_every_editor_level(target):
    value = fixture("editor")
    target(value)["html"] = "unrecognized field"
    with pytest.raises(ValueError, match="unknown fields"):
        validate_interaction(value)


@pytest.mark.parametrize("kind,target", [
    ("records", lambda a: a["columns"][0]),
    ("records", lambda a: a["columns"][2]["options"][0]),
    ("records", lambda a: a["rows"][0]),
    ("records", lambda a: a["rows"][0]["evidence"]),
    ("records", lambda a: a["calculation"]),
    ("form", lambda a: a["fields"][0]),
    ("review", lambda a: a["patches"][0]),
])
def test_other_artifacts_do_not_accept_generated_actions(kind, target):
    value = fixture(kind)
    target(art(value))["onClick"] = "run something"
    with pytest.raises(ValueError, match="unknown fields"):
        validate_interaction(value)


@pytest.mark.parametrize("invalid", [None, [], "editor", 1, True])
def test_interaction_requires_an_object(invalid):
    with pytest.raises(ValueError):
        validate_interaction(invalid)


@pytest.mark.parametrize("identifier", ["", "id with space", "标识", "x" * 41, 1, None])
def test_input_identifiers_are_bounded(identifier):
    value = fixture("editor")
    value["inputs"][0]["id"] = identifier
    with pytest.raises(ValueError):
        validate_interaction(value)


def test_duplicate_option_and_field_ids_are_rejected():
    value = fixture("editor")
    value["inputs"][0]["options"][1]["id"] = "app"
    with pytest.raises(ValueError, match="duplicate"):
        validate_interaction(value)
    value = fixture("editor")
    art(value)["fields"][1]["id"] = "headline"
    with pytest.raises(ValueError, match="duplicate"):
        validate_interaction(value)


@pytest.mark.parametrize("edit", [
    lambda x: x["variants"].pop(),
    lambda x: x["variants"].append(copy.deepcopy(x["variants"][0])),
    lambda x: x["variants"][1]["when"].update(product="app"),
    lambda x: x["variants"][1]["when"].update(product="missing"),
    lambda x: x["variants"][1]["when"].clear(),
    lambda x: x["variants"][1]["when"].update(other="app"),
])
def test_every_input_combination_has_exactly_one_complete_variant(edit):
    value = fixture("editor")
    edit(value)
    with pytest.raises(ValueError):
        validate_interaction(value)


def test_two_inputs_cover_all_four_contexts_and_all_neighbor_changes():
    value = fixture("editor")
    value["inputs"].append({"id": "format", "label": bilingual("Format"), "options": [
        {"id": "short", "label": bilingual("Short")}, {"id": "long", "label": bilingual("Long")}]})
    variants = []
    for existing in value["variants"]:
        for format_id in ("short", "long"):
            variant = copy.deepcopy(existing)
            variant["when"]["format"] = format_id
            variant["artifact"]["fields"][0]["value"] = {
                locale: text + (" — a short invitation" if format_id == "short" else " — an extended conversation invitation")
                for locale, text in variant["artifact"]["fields"][0]["value"].items()}
            variants.append(variant)
    value["variants"] = variants
    assert len(validate_interaction(value)["variants"]) == 4
    value["variants"][1]["artifact"] = copy.deepcopy(value["variants"][0]["artifact"])
    with pytest.raises(ValueError, match="must change artifact"):
        validate_interaction(value)


def test_more_than_four_combinations_are_rejected_before_content():
    value = fixture("editor")
    value["inputs"].append({"id": "format", "label": bilingual("Format"), "options": [
        {"id": str(index), "label": bilingual(str(index))} for index in range(3)]})
    with pytest.raises(ValueError, match="four combinations"):
        validate_interaction(value)


def test_changing_only_brief_labels_or_ids_is_not_an_interaction():
    value = fixture("editor")
    art(value, 1).update(copy.deepcopy(art(value)))
    for field in art(value, 1)["fields"]:
        field["id"] += "-renamed"
        field["label"] = bilingual("A different decoration")
    with pytest.raises(ValueError, match="must change artifact"):
        validate_interaction(value)


def test_causal_content_must_change_in_each_language():
    value = fixture("editor")
    for first, second in zip(art(value)["fields"], art(value, 1)["fields"]):
        second["value"]["en"] = first["value"]["en"]
    with pytest.raises(ValueError, match="content in en"):
        validate_interaction(value)


@pytest.mark.parametrize("number", [True, False, "6", None, float("nan"), float("inf"), float("-inf"), 10 ** 1000])
def test_numeric_cells_reject_nonfinite_values_and_coercions(number):
    value = fixture("records")
    art(value)["rows"][0]["cells"]["hours"] = number
    with pytest.raises(ValueError, match="finite number"):
        validate_interaction(value)


def test_negative_and_decimal_values_remain_numbers():
    value = fixture("records")
    art(value)["rows"][0]["cells"]["hours"] = -2.75
    assert art(validate_interaction(value))["rows"][0]["cells"]["hours"] == -2.75


@pytest.mark.parametrize("edit", [
    lambda a: a["rows"][0]["cells"].pop("hours"),
    lambda a: a["rows"][0]["cells"].update(extra=4),
    lambda a: a["rows"][0]["cells"].update(status="unknown"),
    lambda a: a["rows"][0]["cells"].update(title="not bilingual"),
    lambda a: a["columns"][1].pop("unit"),
    lambda a: a["columns"][0].update(unit=bilingual("unit")),
    lambda a: a["columns"][1].update(options=[]),
    lambda a: a["columns"][2].pop("options"),
    lambda a: a["columns"][2]["options"][1].update(id="todo"),
    lambda a: a["rows"][1].update(id="navigation"),
    lambda a: a.update(group_by="hours"),
    lambda a: a.pop("group_by"),
])
def test_record_shape_units_and_references_are_enforced(edit):
    value = fixture("records")
    edit(art(value))
    with pytest.raises(ValueError):
        validate_interaction(value)


@pytest.mark.parametrize("calculation", [
    {"op": "sum", "column": "hours", "label": bilingual("Total")},
    {"op": "count", "label": bilingual("Selected")},
    {"op": "difference", "column": "hours", "left": "navigation", "right": "copy", "label": bilingual("Difference")},
])
def test_only_fixed_well_typed_calculations_are_accepted(calculation):
    value = fixture("records")
    art(value)["calculation"] = calculation
    assert art(validate_interaction(value))["calculation"] == calculation


@pytest.mark.parametrize("edit", [
    lambda c: c.update(op="eval"),
    lambda c: c.update(column="title"),
    lambda c: c.update(left="unknown"),
    lambda c: c.update(left="copy"),
    lambda c: c.pop("column"),
    lambda c: c.update(op="count"),
    lambda c: c.update(formula="sum(hours)"),
])
def test_invalid_calculations_are_not_silently_downgraded(edit):
    value = fixture("records")
    edit(art(value)["calculation"])
    with pytest.raises(ValueError):
        validate_interaction(value)


def test_evidence_quote_must_be_literal_in_both_languages():
    value = fixture("records")
    art(value)["rows"][0]["evidence"]["quote"]["en"] = "not in the evidence"
    with pytest.raises(ValueError, match="quote must occur"):
        validate_interaction(value)


@pytest.mark.parametrize("edit", [
    lambda a: a["fields"][0].update(required="true"),
    lambda a: a["fields"][0].update(type="password"),
    lambda a: a.update(action="send"),
    lambda a: a["fields"].pop(),
])
def test_form_is_a_bounded_local_native_form(edit):
    value = fixture("form")
    edit(art(value))
    with pytest.raises(ValueError):
        validate_interaction(value)


def test_review_preserves_inert_code_and_exact_whitespace():
    value = fixture("review")
    a = art(value)
    a["base"] = bilingual("  const entries: Array<string> = [];\n  const limit = 10;  ")
    a["patches"][0]["before"] = bilingual("  const entries: Array<string> = [];")
    a["patches"][0]["after"] = bilingual("  const entries: Array<string> = ['draft'];")
    a["patches"][1]["before"] = bilingual("const limit = 10;")
    a["patches"][1]["after"] = bilingual("const limit = 20;")
    assert art(validate_interaction(value)) == a


def test_review_accepts_comparison_operators_without_confusing_them_with_html():
    value = fixture("review")
    a = art(value)
    a["base"] = bilingual("if (value < limit && count > 0) return value;\nconst limit = 10;")
    a["patches"][0]["before"] = bilingual("count > 0")
    a["patches"][0]["after"] = bilingual("count > 1")
    a["patches"][1]["before"] = bilingual("const limit = 10;")
    a["patches"][1]["after"] = bilingual("const limit = 20;")
    assert art(validate_interaction(value)) == a


@pytest.mark.parametrize("edit", [
    lambda a: a["patches"][0].update(before=bilingual("absent")),
    lambda a: a["patches"][0].update(after=copy.deepcopy(a["patches"][0]["before"])),
    lambda a: a["patches"][1].update(before=bilingual("strip()")),
    lambda a: a["patches"][1].update(id="lowercase"),
    lambda a: a["base"].update(en=a["base"]["en"] + "\nvalue.strip()"),
])
def test_patches_are_real_unique_nonoverlapping_edits(edit):
    value = fixture("review")
    edit(art(value))
    with pytest.raises(ValueError):
        validate_interaction(value)


def test_overlapping_occurrences_are_not_mistaken_for_one_match():
    value = fixture("review")
    art(value)["base"] = bilingual("aaa and other")
    art(value)["patches"][0]["before"] = bilingual("aa")
    art(value)["patches"][0]["after"] = bilingual("bb")
    art(value)["patches"][1]["before"] = bilingual("other")
    art(value)["patches"][1]["after"] = bilingual("different")
    with pytest.raises(ValueError, match="exactly once"):
        validate_interaction(value)


@pytest.mark.parametrize("unsafe", [
    "https://example.com", "www.example.com", "javascript:alert(1)", "data:text/html,hello",
    "<script>alert(1)</script>", "<img src=x>", "Accuracy 96%", "Video generated", "文件已保存本地",
])
def test_plain_artifact_copy_rejects_unsafe_representations(unsafe):
    value = fixture("editor")
    art(value)["fields"][0]["value"]["en"] = unsafe
    with pytest.raises(ValueError, match="unsupported"):
        validate_interaction(value)


def test_inert_code_exception_does_not_allow_html_or_urls():
    for unsafe in ("<script>alert(1)</script>", "const url = 'https://example.com';", "<div>hello</div>"):
        value = fixture("review")
        art(value)["base"]["en"] = unsafe
        with pytest.raises(ValueError, match="unsupported"):
            validate_interaction(value)


def test_copy_bounds_and_bilingual_shape_are_enforced_without_truncation():
    value = fixture("editor")
    art(value)["fields"][0]["value"]["en"] = "x" * 1400
    assert len(art(validate_interaction(value))["fields"][0]["value"]["en"]) == 1400
    art(value)["fields"][0]["value"]["en"] += "x"
    with pytest.raises(ValueError, match="1400"):
        validate_interaction(value)
    value = fixture("editor")
    value["input_label"]["en"] = " "
    with pytest.raises(ValueError, match="nonempty"):
        validate_interaction(value)


@pytest.mark.parametrize("kind", ["records", "form", "review"])
def test_renaming_visible_decorations_cannot_fake_a_new_result(kind):
    value = fixture(kind)
    value["inputs"] = [{"id": "choice", "label": bilingual("Choice"), "options": [
        {"id": "a", "label": bilingual("A")}, {"id": "b", "label": bilingual("B")}]}]
    value["variants"][0]["when"] = {"choice": "a"}
    value["variants"].append(copy.deepcopy(value["variants"][0]))
    value["variants"][1]["when"] = {"choice": "b"}
    second = art(value, 1)
    if kind == "records":
        for column in second["columns"]:
            column["label"] = bilingual("Changed heading")
        second["calculation"]["label"] = bilingual("New heading")
    elif kind == "form":
        second["title"] = bilingual("New form title")
        for field in second["fields"]:
            field["label"] = bilingual("Changed label")
    else:
        for patch in second["patches"]:
            patch["label"] = bilingual("Changed label")
    with pytest.raises(ValueError, match="must change artifact"):
        validate_interaction(value)


@pytest.mark.parametrize("locale", ["zh", "en"])
def test_selected_facts_must_appear_in_actual_values_in_each_language(locale):
    value = fixture("editor")
    fact = value["inputs"][0]["options"][0]["facts"][0][locale]
    art(value)["fields"][1]["value"][locale] = art(value)["fields"][1]["value"][locale].replace(fact, "Another product")
    # Merely putting the fact in the explanatory brief or a field label is insufficient.
    value["variants"][0]["brief"][locale] += " " + fact
    art(value)["fields"][1]["label"][locale] = fact
    with pytest.raises(ValueError, match=f"selected facts.*{locale}"):
        validate_interaction(value)


@pytest.mark.parametrize("locale", ["zh", "en"])
def test_unselected_exclusive_facts_cannot_leak_into_output(locale):
    value = fixture("editor")
    foreign = value["inputs"][0]["options"][1]["facts"][0][locale]
    art(value)["fields"][0]["value"][locale] += " " + foreign
    with pytest.raises(ValueError, match=f"unselected exclusive facts.*{locale}"):
        validate_interaction(value)


def test_shared_selected_facts_are_allowed_but_still_required():
    value = fixture("editor")
    shared = {"zh": "通勤", "en": "commute"}
    for option in value["inputs"][0]["options"]:
        option["facts"].append(shared.copy())
    for variant in value["variants"]:
        for locale in ("zh", "en"):
            variant["artifact"]["fields"][0]["value"][locale] += " " + shared[locale]
    assert validate_interaction(value) == value
    art(value)["fields"][0]["value"]["en"] = art(value)["fields"][0]["value"]["en"].replace("commute", "")
    with pytest.raises(ValueError, match="selected facts.*en"):
        validate_interaction(value)


def test_fact_matching_is_literal_case_sensitive_and_never_crosses_fields():
    value = fixture("editor")
    art(value)["fields"][1]["value"]["en"] = art(value)["fields"][1]["value"]["en"].replace("Speaking Partner", "speaking partner")
    with pytest.raises(ValueError, match="selected facts"):
        validate_interaction(value)
    value = fixture("editor")
    value["inputs"][0]["options"][0]["facts"] = [bilingual("alpha\nbeta")]
    art(value)["fields"][0]["value"] = bilingual("alpha")
    art(value)["fields"][1]["value"] = bilingual("beta")
    with pytest.raises(ValueError, match="selected facts"):
        validate_interaction(value)


@pytest.mark.parametrize("facts", [[], [bilingual("fact")] * 6, [bilingual("x" * 121)], ["not a Copy"], None])
def test_binding_facts_are_bounded_bilingual_text(facts):
    value = fixture("editor")
    value["inputs"][0]["options"][0]["facts"] = facts
    with pytest.raises(ValueError):
        validate_interaction(value)


def two_control_editor():
    value = fixture("editor")
    value["inputs"].append({"id": "platform", "label": bilingual("Platform"), "options": [
        {"id": "social", "label": bilingual("Social")}, {"id": "professional", "label": bilingual("Professional")}]})
    variants = []
    for existing in value["variants"]:
        for platform in ("social", "professional"):
            variant = copy.deepcopy(existing)
            variant["when"]["platform"] = platform
            for locale in ("zh", "en"):
                variant["artifact"]["fields"][0]["value"][locale] += " " + platform
            variants.append(variant)
    value["variants"] = variants
    return value


def test_two_input_editor_keeps_product_facts_when_platform_changes():
    value = two_control_editor()
    assert validate_interaction(value) == value
    art(value, 1)["fields"][1]["value"]["en"] = "Analytics Hub creates business reports with a different product."
    with pytest.raises(ValueError, match="selected facts.*en"):
        validate_interaction(value)


def test_two_input_editors_require_one_fully_bound_input():
    value = two_control_editor()
    del value["inputs"][0]["options"][0]["facts"]
    with pytest.raises(ValueError, match="every option declares binding facts"):
        validate_interaction(value)
    # A zero/one-control interaction remains backward compatible without facts.
    value = fixture("editor")
    for option in value["inputs"][0]["options"]:
        del option["facts"]
    assert validate_interaction(value) == value
    assert validate_interaction(fixture("form")) == fixture("form")


def test_shared_facts_are_exempt_even_when_selected_by_another_input():
    value = two_control_editor()
    shared = {"zh": "通勤", "en": "commute"}
    value["inputs"][0]["options"][1]["facts"].append(shared.copy())
    for option in value["inputs"][1]["options"]:
        option["facts"] = [shared.copy()]
    for variant in value["variants"]:
        for locale in ("zh", "en"):
            variant["artifact"]["fields"][0]["value"][locale] += " " + shared[locale]
    assert validate_interaction(value) == value


def test_record_select_options_cannot_declare_scenario_facts():
    value = fixture("records")
    art(value)["columns"][2]["options"][0]["facts"] = [bilingual("unavailable binding")]
    with pytest.raises(ValueError, match="unknown fields"):
        validate_interaction(value)


def with_shared_fact(kind, fact):
    value = fixture(kind)
    value["inputs"] = [{"id": "case", "label": bilingual("Case"), "options": [
        {"id": "a", "label": bilingual("A"), "facts": [fact]},
        {"id": "b", "label": bilingual("B"), "facts": [fact]},
    ]}]
    value["variants"][0]["when"] = {"case": "a"}
    value["variants"].append(copy.deepcopy(value["variants"][0]))
    value["variants"][1]["when"] = {"case": "b"}
    if kind == "records":
        art(value, 1)["rows"][0]["cells"]["hours"] = 8
    elif kind == "form":
        art(value, 1)["fields"][0]["required"] = False
    else:
        art(value, 1)["patches"][1]["after"] = bilingual("limit = 30")
    return value


@pytest.mark.parametrize("fact", [
    {"zh": "整理导航", "en": "Organize navigation"},
    {"zh": "找不到价格页", "en": "cannot find pricing"},
    {"zh": "待处理", "en": "To do"},
    bilingual("2.5"),
])
def test_records_bind_visible_cells_and_evidence(fact):
    value = with_shared_fact("records", fact)
    assert validate_interaction(value) == value


def test_form_facts_bind_title_and_field_labels_but_not_confirmation():
    value = with_shared_fact("form", {"zh": "工作坊报名", "en": "Workshop signup"})
    assert validate_interaction(value) == value
    value = with_shared_fact("form", {"zh": "邮箱", "en": "Email"})
    assert validate_interaction(value) == value
    value = with_shared_fact("form", {"zh": "没有发送", "en": "nothing was sent"})
    with pytest.raises(ValueError, match="selected facts"):
        validate_interaction(value)


def test_review_facts_must_exist_before_and_after_every_builtin_edit():
    value = with_shared_fact("review", bilingual("def normalize"))
    assert validate_interaction(value) == value
    value = with_shared_fact("review", bilingual("value.strip().lower()"))
    with pytest.raises(ValueError, match="selected facts"):
        validate_interaction(value)
    value = with_shared_fact("review", {"zh": "统一小写", "en": "Normalize case"})
    with pytest.raises(ValueError, match="selected facts"):
        validate_interaction(value)


def records_variants():
    value = fixture("records")
    value["inputs"] = [{"id": "audience", "label": bilingual("Audience"), "options": [
        {"id": "a", "label": bilingual("Founders")}, {"id": "b", "label": bilingual("Students")},
    ]}]
    value["variants"][0]["when"] = {"audience": "a"}
    value["variants"].append(copy.deepcopy(value["variants"][0]))
    value["variants"][1]["when"] = {"audience": "b"}
    return value


@pytest.mark.parametrize("field", ["text", "quote"])
def test_hidden_evidence_only_changes_do_not_make_record_variants_causal(field):
    value = records_variants()
    evidence = art(value, 1)["rows"][0]["evidence"]
    if field == "text":
        evidence["text"]["zh"] += " 这是另一组访谈。"
        evidence["text"]["en"] += " This is another interview group."
    else:
        evidence["quote"] = {"zh": "导航需要整理", "en": "navigation needs attention"}
    with pytest.raises(ValueError, match="must change artifact"):
        validate_interaction(value)


@pytest.mark.parametrize("visible_change", ["cell", "order", "calculation"])
def test_visible_record_result_changes_still_qualify(visible_change):
    value = records_variants()
    second = art(value, 1)
    if visible_change == "cell":
        second["rows"][0]["cells"]["hours"] = 9
    elif visible_change == "order":
        second["rows"].reverse()
    else:
        second["calculation"] = {"op": "sum", "column": "hours", "label": bilingual("Total")}
    assert validate_interaction(value) == value


def environment_review():
    value = fixture("review")
    value["inputs"] = [{"id": "env", "label": bilingual("Environment"), "options": [
        {"id": name, "label": bilingual(name), "facts": [bilingual(name)]} for name in ("staging", "sandbox")
    ]}]
    value["variants"] = []
    for name in ("staging", "sandbox"):
        value["variants"].append({"when": {"env": name}, "brief": bilingual("Review the selected environment."), "artifact": {
            "base": bilingual(f"Environment: {name}\nAudit: off"),
            "patches": [
                {"id": "target", "label": bilingual("Annotate target"), "before": bilingual(f"Environment: {name}"),
                 "after": bilingual(f"Environment: {name} (reviewed)")},
                {"id": "audit", "label": bilingual("Enable audit"), "before": bilingual("Audit: off"), "after": bilingual("Audit: on")},
            ],
        }})
    return value


def test_review_accepts_patches_that_preserve_each_selected_environment():
    value = environment_review()
    assert validate_interaction(value) == value


@pytest.mark.parametrize("locale", ["zh", "en"])
def test_review_patch_cannot_delete_a_selected_fact(locale):
    value = environment_review()
    art(value)["patches"][0]["after"][locale] = "Environment: default"
    with pytest.raises(ValueError, match=f"selected facts.*{locale}"):
        validate_interaction(value)


@pytest.mark.parametrize("locale", ["zh", "en"])
def test_review_patch_cannot_introduce_an_unselected_exclusive_fact(locale):
    value = environment_review()
    art(value)["patches"][1]["after"][locale] = "Audit: sandbox"
    with pytest.raises(ValueError, match=f"unselected exclusive facts.*{locale}"):
        validate_interaction(value)


def test_review_checks_all_sixteen_acceptance_combinations():
    value = environment_review()
    for variant in value["variants"]:
        name = variant["when"]["env"]
        variant["artifact"] = {
            "base": bilingual("\n".join(f"{letter}: {name}" for letter in "ABCD")),
            "patches": [
                {"id": letter, "label": bilingual("Simplify " + letter), "before": bilingual(f"{letter}: {name}"),
                 "after": bilingual(f"{letter}: default")} for letter in "ABCD"
            ],
        }
    # Every proper subset leaves at least one selected fact; only all four erase it.
    with pytest.raises(ValueError, match="selected facts"):
        validate_interaction(value)


def test_review_fact_checks_use_merged_text_not_independent_replacement_leaves():
    value = environment_review()
    for variant in value["variants"]:
        name = variant["when"]["env"]
        variant["artifact"]["base"] = bilingual(f"Environment: {name}\nsaXXbox\nAudit: off")
        variant["artifact"]["patches"][0].update(before=bilingual("XX"), after=bilingual("nd"))
    # Neither base nor the 'nd' replacement contains the foreign word by itself.
    # Applying that patch produces 'sandbox' in the staging variant.
    with pytest.raises(ValueError, match="unselected exclusive facts"):
        validate_interaction(value)
