"""Tests for the interactive demo system.

The invariants here are the ones that would otherwise be enforced by a review
checklist. They are tests because a checklist erodes and a test does not.
"""
import copy
import json
import os

import pytest

from app.services import demo_service
from app.services.demo_repository import DemoRepository
from app.services.demo_spec import ENDPOINT_REGISTRY, SpecError, validate_spec

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_DIR = os.path.join(REPO_ROOT, "crawler", "data", "demos", "published")


def minimal_spec(**overrides):
    spec = {
        "version": 1,
        "product_slug": "acme",
        "product_name": "Acme",
        "tier": "concept",
        "title": {"zh": "标题", "en": "Title"},
        "premise": {"zh": "前提", "en": "Premise"},
        "confidence": "inferred",
        "evidence": [{"claim": "Acme raised a round.", "source_url": "https://example.com/a"}],
        "steps": [
            {
                "id": f"s{i}",
                "label": {"zh": "步骤", "en": "Step"},
                "narration": {"zh": "说明", "en": "Narration"},
                "widget": {
                    "type": "pipeline",
                    "stages": [
                        {"name": {"zh": "一", "en": "One"},
                         "input": {"zh": "输入", "en": "in"}, "output": {"zh": "输出", "en": "out"}},
                        {"name": {"zh": "二", "en": "Two"},
                         "input": {"zh": "输入", "en": "in"}, "output": {"zh": "输出", "en": "out"}},
                    ],
                },
            }
            for i in range(3)
        ],
    }
    spec.update(overrides)
    return spec


class TestStructure:
    def test_minimal_spec_validates(self):
        assert validate_spec(minimal_spec())["product_slug"] == "acme"

    @pytest.mark.parametrize("count", [0, 1, 2, 6])
    def test_step_count_is_bounded(self, count):
        spec = minimal_spec()
        spec["steps"] = spec["steps"][:1] * count
        with pytest.raises(SpecError, match="steps"):
            validate_spec(spec)

    def test_duplicate_step_ids_rejected(self):
        spec = minimal_spec()
        spec["steps"][1]["id"] = spec["steps"][0]["id"]
        with pytest.raises(SpecError, match="duplicate step id"):
            validate_spec(spec)

    def test_both_locales_required(self):
        spec = minimal_spec()
        spec["title"] = {"zh": "只有中文", "en": ""}
        with pytest.raises(SpecError, match="title.en"):
            validate_spec(spec)

    def test_datum_value_must_be_bilingual(self):
        spec = minimal_spec()
        spec["steps"][0]["widget"] = {
            "type": "param_dial",
            "param": {"zh": "参数", "en": "Param"},
            "min": 0, "max": 10, "step": 1, "unit": "x",
            "formula_note": {"zh": "说明", "en": "Note"},
            "outputs": [{"label": {"zh": "A", "en": "A"}, "value": "English only", "is_example": True}],
        }
        with pytest.raises(SpecError, match="value"):
            validate_spec(spec)

    def test_widget_prose_must_be_bilingual(self):
        """A plain string where a locale pair belongs would render English text
        under the Chinese UI."""
        spec = minimal_spec()
        spec["steps"][0]["widget"]["stages"][0]["output"] = "English only"
        with pytest.raises(SpecError, match="output"):
            validate_spec(spec)

    def test_unknown_widget_type_rejected(self):
        spec = minimal_spec()
        spec["steps"][0]["widget"] = {"type": "iframe", "src": "https://evil.example"}
        with pytest.raises(SpecError, match="widget.type"):
            validate_spec(spec)

    def test_bad_version_rejected(self):
        with pytest.raises(SpecError, match="version"):
            validate_spec(minimal_spec(version=2))


class TestLabellingInvariants:
    """The Tier 2 contract, enforced at parse time rather than in review."""

    def test_simulation_cannot_claim_verification(self):
        spec = minimal_spec(tier="simulation", confidence="verified")
        with pytest.raises(SpecError, match="illustrative"):
            validate_spec(spec)

    def test_simulation_accepts_illustrative(self):
        assert validate_spec(minimal_spec(tier="simulation", confidence="illustrative"))["tier"] == "simulation"

    def test_unsourced_number_rejected(self):
        spec = minimal_spec()
        spec["steps"][0]["widget"] = {
            "type": "spec_matrix",
            "subject": "Acme",
            "competitors": ["Rival"],
            "rows": [
                {
                    "spec": {"zh": "指标", "en": "Metric"},
                    # Neither cited nor flagged as an example: not publishable.
                    "values": [
                        {"label": {"zh": "A", "en": "A"}, "value": {"zh": "42", "en": "42"}, "evidence_ref": None, "is_example": False},
                        {"label": {"zh": "B", "en": "B"}, "value": {"zh": "7", "en": "7"}, "evidence_ref": None, "is_example": True},
                    ],
                }
            ] * 3,
        }
        with pytest.raises(SpecError, match="evidence_ref|is_example"):
            validate_spec(spec)

    def test_number_passes_when_cited(self):
        spec = minimal_spec()
        spec["steps"][0]["widget"] = {
            "type": "spec_matrix",
            "subject": "Acme",
            "competitors": ["Rival"],
            "rows": [
                {
                    "spec": {"zh": "指标", "en": "Metric"},
                    "values": [
                        {"label": {"zh": "A", "en": "A"}, "value": {"zh": "42", "en": "42"}, "evidence_ref": 0, "is_example": False},
                        {"label": {"zh": "B", "en": "B"}, "value": {"zh": "7", "en": "7"}, "evidence_ref": None, "is_example": True},
                    ],
                }
            ] * 3,
        }
        assert validate_spec(spec)["steps"][0]["widget"]["rows"][0]["values"][0]["evidence_ref"] == 0

    def test_evidence_ref_out_of_range_rejected(self):
        spec = minimal_spec()
        spec["steps"][0]["widget"] = {
            "type": "param_dial",
            "param": {"zh": "参数", "en": "Param"},
            "min": 0, "max": 10, "step": 1, "unit": "x",
            "formula_note": {"zh": "说明", "en": "Note"},
            "outputs": [{"label": {"zh": "A", "en": "A"}, "value": {"zh": "9", "en": "9"}, "evidence_ref": 7, "is_example": False}],
        }
        with pytest.raises(SpecError, match="out of range"):
            validate_spec(spec)

    def test_sandbox_requires_a_source(self):
        spec = minimal_spec(tier="sandbox", confidence="verified", evidence=[])
        with pytest.raises(SpecError, match="at least one source"):
            validate_spec(spec)


class TestSsrfGuard:
    """A generated spec must never be able to name an outbound URL."""

    def test_live_widget_without_endpoint_id_rejected(self):
        spec = minimal_spec(tier="sandbox", confidence="verified")
        spec["steps"][0]["widget"] = {
            "type": "query_response", "mode": "live",
            "presets": [{"query": "q", "response": {"zh": "", "en": ""}}],
        }
        with pytest.raises(SpecError, match="endpoint_id"):
            validate_spec(spec)

    def test_live_widget_with_unregistered_endpoint_rejected(self):
        spec = minimal_spec(tier="sandbox", confidence="verified")
        spec["steps"][0]["widget"] = {
            "type": "query_response", "mode": "live", "endpoint_id": "not_registered",
            "presets": [{"query": "q", "response": {"zh": "", "en": ""}}],
        }
        with pytest.raises(SpecError, match="not a registered endpoint"):
            validate_spec(spec)

    def test_url_as_endpoint_id_rejected(self):
        spec = minimal_spec(tier="sandbox", confidence="verified")
        spec["steps"][0]["widget"] = {
            "type": "query_response", "mode": "live",
            "endpoint_id": "https://attacker.example/exfiltrate",
            "presets": [{"query": "q", "response": {"zh": "", "en": ""}}],
        }
        # Rejected as unregistered before it can even be read as a URL.
        with pytest.raises(SpecError, match="registered endpoint|not a URL"):
            validate_spec(spec)

    def test_live_widget_allowed_when_endpoint_is_registered(self):
        ENDPOINT_REGISTRY["test_ep"] = {"url": "https://api.example.com/search", "key_var": "TEST_KEY"}
        try:
            spec = minimal_spec(tier="sandbox", confidence="verified")
            spec["steps"][0]["widget"] = {
                "type": "query_response", "mode": "live", "endpoint_id": "test_ep",
                "presets": [{"query": "q", "response": {"zh": "", "en": ""}}],
            }
            assert validate_spec(spec)["steps"][0]["widget"]["endpoint_id"] == "test_ep"
        finally:
            ENDPOINT_REGISTRY.pop("test_ep", None)

    def test_run_live_query_refuses_unregistered_endpoint(self):
        assert demo_service.run_live_query("nope", "q") == {"success": False, "error": "ENDPOINT_NOT_AVAILABLE"}


class TestIndependenceFirewall:
    """Outreach means vendors will supply keys while we score them. The demo
    pipeline must be structurally incapable of moving a score."""

    def test_generation_never_mutates_the_product_record(self, monkeypatch):
        product = {
            "name": "Acme", "website": "https://acme.example", "description": "An AI thing",
            "why_matters": "Raised money", "categories": ["agent"], "dark_horse_index": 4,
            "final_score": 88.5, "trending_score": 12, "criteria_met": ["funding"], "hot_score": 3,
        }
        before = copy.deepcopy(product)
        monkeypatch.setattr(demo_service, "_key", lambda: "test-key")
        monkeypatch.setattr(demo_service, "_call_model", lambda *a, **k: json.dumps(minimal_spec(tier="simulation", confidence="illustrative")))

        result = demo_service.generate(product, "acme")

        assert result["success"] is True
        assert product == before, "generation must not touch the product record"

    def test_scoring_fields_are_absent_from_generated_specs(self, monkeypatch):
        product = {"name": "Acme", "description": "thing", "dark_horse_index": 5, "final_score": 99}
        monkeypatch.setattr(demo_service, "_key", lambda: "test-key")
        monkeypatch.setattr(demo_service, "_call_model", lambda *a, **k: json.dumps(minimal_spec(tier="simulation", confidence="illustrative")))
        spec = demo_service.generate(product, "acme")["spec"]
        for field in demo_service.SCORING_FIELDS:
            assert field not in spec, f"{field} must never be carried on a demo"

    def test_vendor_status_defaults_to_none(self):
        assert validate_spec(minimal_spec())["vendor_status"] == "none"


class TestGeneration:
    def test_identity_comes_from_us_not_the_model(self, monkeypatch):
        """A model that names a different product must not be able to publish
        under that name."""
        monkeypatch.setattr(demo_service, "_key", lambda: "test-key")
        hostile = minimal_spec(tier="simulation", confidence="illustrative",
                               product_slug="someone-else", product_name="Someone Else")
        monkeypatch.setattr(demo_service, "_call_model", lambda *a, **k: json.dumps(hostile))
        spec = demo_service.generate({"name": "Acme", "description": "thing"}, "acme")["spec"]
        assert spec["product_slug"] == "acme"
        assert spec["product_name"] == "Acme"

    def test_retry_is_told_what_failed(self, monkeypatch):
        monkeypatch.setattr(demo_service, "_key", lambda: "test-key")
        calls = []

        def fake_call(prompt, timeout):
            calls.append(prompt)
            if len(calls) == 1:
                return json.dumps(minimal_spec(tier="simulation", confidence="verified"))
            return json.dumps(minimal_spec(tier="simulation", confidence="illustrative"))

        monkeypatch.setattr(demo_service, "_call_model", fake_call)
        result = demo_service.generate({"name": "Acme", "description": "thing"}, "acme")
        assert result["success"] is True
        assert len(calls) == 2
        assert "rejected" in calls[1] and "illustrative" in calls[1]

    def test_unparseable_response_does_not_leak_raw_text(self, monkeypatch):
        monkeypatch.setattr(demo_service, "_key", lambda: "test-key")
        monkeypatch.setattr(demo_service, "_call_model", lambda *a, **k: "Sorry, I cannot help with that.")
        result = demo_service.generate({"name": "Acme", "description": "thing"}, "acme")
        assert result["success"] is False
        assert result["error"] == "INVALID_SPEC"

    def test_json_extracted_from_fenced_response(self):
        payload = minimal_spec()
        assert demo_service._extract_json(f"```json\n{json.dumps(payload)}\n```")["product_slug"] == "acme"

    def test_json_extracted_when_wrapped_in_prose(self):
        payload = minimal_spec()
        text = f"Here you go:\n{json.dumps(payload)}\nHope that helps."
        assert demo_service._extract_json(text)["product_slug"] == "acme"

    def test_extract_returns_none_rather_than_raw_text(self):
        assert demo_service._extract_json("no json here at all") is None

    def test_not_configured_without_api_key(self, monkeypatch):
        monkeypatch.setattr(demo_service, "_key", lambda: "")
        assert demo_service.generate({"name": "Acme"}, "acme")["error"] == "NOT_CONFIGURED"


class TestTierClassification:
    @pytest.mark.parametrize("product,expected", [
        ({"name": "Apptronik", "description": "humanoid robot", "categories": ["hardware"]}, "concept"),
        ({"name": "Chipco", "description": "AI semiconductor for inference", "categories": []}, "concept"),
        ({"name": "Cradle", "description": "protein design for drug discovery", "categories": ["healthcare"]}, "concept"),
        ({"name": "Exa", "description": "search API for developers", "categories": ["agent"]}, "sandbox"),
        ({"name": "Rogo", "description": "analysis platform for finance teams", "categories": ["agent"]}, "simulation"),
    ])
    def test_classification(self, product, expected):
        assert demo_service.classify_tier(product) == expected

    def test_hardware_flag_forces_concept(self):
        assert demo_service.classify_tier({"name": "X", "description": "an API for developers", "is_hardware": True}) == "concept"


class TestSeeds:
    """The committed seeds are what the site serves with no API key."""

    def test_seed_directory_exists(self):
        assert os.path.isdir(SEED_DIR), "seed demos must be committed"

    def test_every_seed_validates(self):
        names = [n for n in os.listdir(SEED_DIR) if n.endswith(".json")]
        assert names, "expected committed seed demos"
        for name in names:
            with open(os.path.join(SEED_DIR, name), encoding="utf-8") as handle:
                validate_spec(json.load(handle))

    def test_seeds_cover_every_tier_the_catalog_needs(self):
        tiers = set()
        for name in os.listdir(SEED_DIR):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(SEED_DIR, name), encoding="utf-8") as handle:
                tiers.add(json.load(handle)["tier"])
        assert {"sandbox", "simulation", "concept"} <= tiers

    def test_repository_reads_a_seed(self):
        DemoRepository.clear_memory_cache()
        spec = DemoRepository.get("exa")
        assert spec is not None and spec["product_name"] == "Exa"

    def test_repository_rejects_an_invalid_stored_spec(self, monkeypatch):
        """A spec written under looser rules must not render just because it
        is already on disk."""
        DemoRepository.clear_memory_cache()
        monkeypatch.setattr(
            "app.services.demo_repository._read_json_file",
            lambda slug: minimal_spec(tier="simulation", confidence="verified"),
        )
        assert DemoRepository.get("anything") is None

    def test_slugify_matches_expected_keys(self):
        assert DemoRepository.slug_for({"name": "Fireworks AI"}) == "fireworks-ai"
        assert DemoRepository.slug_for({"slug": "apptronik", "name": "Apptronik"}) == "apptronik"
        assert DemoRepository.slug_for({"name": "  Exa!  "}) == "exa"


class TestMongoSync:
    """Demos must survive a cold start, which means reaching MongoDB."""

    @staticmethod
    def _sync_module():
        import importlib.util
        path = os.path.join(REPO_ROOT, "crawler", "tools", "sync_to_mongodb.py")
        spec = importlib.util.spec_from_file_location("sync_to_mongodb_under_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def _db():
        mongomock = pytest.importorskip("mongomock")
        return mongomock.MongoClient().weeklyai

    def test_seeds_are_discovered_by_the_sync_tool(self):
        demos = self._sync_module().load_demos()
        assert {d["product_slug"] for d in demos} >= {"exa", "apptronik", "daloopa"}

    def test_demos_reach_mongo_under_sync_key(self):
        module, db = self._sync_module(), self._db()
        stats = module.sync_demos(db, module.load_demos())
        assert stats["inserted"] == db.demos.count_documents({}) > 0
        assert db.demos.find_one({"_sync_key": "exa"})["product_name"] == "Exa"

    def test_resync_updates_rather_than_duplicates(self):
        module, db = self._sync_module(), self._db()
        demos = module.load_demos()
        module.sync_demos(db, demos)
        module.sync_demos(db, demos)
        assert db.demos.count_documents({"_sync_key": "exa"}) == 1

    def test_invalid_spec_never_reaches_the_cluster(self):
        """A spec that would be refused on read must be refused on write, or it
        looks like a missing demo rather than a rejected one."""
        module, db = self._sync_module(), self._db()
        bad = {**minimal_spec(), "product_slug": "bad", "tier": "simulation", "confidence": "verified"}
        stats = module.sync_demos(db, [bad])
        assert stats["skipped"] == 1
        assert db.demos.count_documents({"_sync_key": "bad"}) == 0

    def test_ensure_indexes_creates_the_demo_uniqueness_guard(self):
        module, db = self._sync_module(), self._db()
        module.ensure_indexes(db)
        unique = [name for name, spec in db.demos.index_information().items() if spec.get("unique")]
        assert unique, "demos needs a unique _sync_key index or a race can store two specs per product"

    def test_repository_reads_what_the_sync_tool_writes(self):
        """The round trip that actually matters: sync writes, backend reads."""
        module, db = self._sync_module(), self._db()
        module.sync_demos(db, module.load_demos())

        from app.services import demo_repository
        original = demo_repository.get_mongo_db
        demo_repository.get_mongo_db = lambda: db
        try:
            DemoRepository.clear_memory_cache()
            spec = DemoRepository.get("exa")
            assert spec is not None and spec["product_name"] == "Exa"
            assert "_sync_key" not in spec and "synced_at" not in spec
        finally:
            demo_repository.get_mongo_db = original
            DemoRepository.clear_memory_cache()
