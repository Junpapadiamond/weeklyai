"""The complete demo contract: identity, budgets, cache, provider and publishing."""
import copy
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests
from app import create_app, rate_limiter
from app.routes import demos
from app.services import demo_experiences as service
from app.services import demo_store
from app.services.demo_contract import cache_key, validate_experience
from app.services.demo_store import DemoStore, StoreUnavailable

PRODUCT = {"_id": "demo-product", "name": "Demo Product", "website": "https://product.example",
           "description": "Find and review web evidence", "dark_horse_index": 5}


@pytest.fixture
def spec():
    entry = next(iter(service.published().values()))
    result = copy.deepcopy(entry["spec"])
    result["sources"] = [{"url": PRODUCT["website"], "label": {"zh": "官网", "en": "Official"}}]
    return result


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_DAILY_USER_LIMIT", "3")
    monkeypatch.setenv("DEMO_DAILY_GLOBAL_LIMIT", "20")
    return DemoStore(tmp_path / "demos.sqlite3")


@pytest.fixture
def client(monkeypatch, store):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setattr(demos, "DemoStore", lambda: store)
    monkeypatch.setattr(service, "providers", lambda: [])
    monkeypatch.setattr(demos.ProductService, "get_product_by_id", lambda value: PRODUCT if value == "demo-product" else None)
    monkeypatch.setattr(demos.ProductService, "get_discovery_products", lambda: [PRODUCT])
    rate_limiter.requests.clear()
    return create_app().test_client()


def test_cached_workflow_needs_no_model_and_costs_nothing(client, store, spec):
    key = cache_key(PRODUCT)
    lease = store.reserve(key, "publisher")
    store.finish(key, lease["token"], service.envelope(PRODUCT, spec, "pregenerated"))
    first = client.get("/api/v1/demos/product/demo-product")
    assert first.status_code == 200 and first.json["state"] == "ready"
    assert "HttpOnly" in first.headers["Set-Cookie"] and "SameSite=Lax" in first.headers["Set-Cookie"]
    response = client.post("/api/v1/demos/generate", json={"product_id": "demo-product"})
    assert response.status_code == 200 and response.json["cached"]
    assert response.json["quota"]["used"] == 0
    assert response.json["experience"]["spec"]["confidence"] == "illustrative"
    assert not response.json["generation_available"]


def test_reviewed_profile_opens_without_model_quota_or_stale_cache(client, store, monkeypatch):
    product = {**PRODUCT, "name": "Higgsfield", "website": "https://higgsfield.ai/"}
    monkeypatch.setattr(demos.ProductService, "get_product_by_id", lambda value: product)
    monkeypatch.setattr(demos.ProductService, "get_discovery_products", lambda: [product])
    monkeypatch.setenv("DEMO_DAILY_USER_LIMIT", "0")
    monkeypatch.setattr(service, "generate_spec", lambda value: pytest.fail("No model call for reviewed profile"))
    response = client.post("/api/v1/demos/generate", json={"product_id": "demo-product"})
    assert response.status_code == 200 and response.json["cached"]
    assert response.json["experience"]["spec"]["workspace"]["kind"] == "video"
    assert response.json["quota"]["site_remaining"] == 20
    assert client.get("/api/v1/demos/catalog?filter=ready").json["ready_count"] == 1
    assert service.ready_experience({**product, "website": "https://higgsfield.ai.evil.example"}, store) is None


def test_daily_preparation_prioritizes_fresh_discoveries():
    from tools.pregenerate_demos import candidates
    fresh = {"name": "Fresh", "dark_horse_index": 4, "discovered_at": "2026-09-27"}
    old = {"name": "Old", "dark_horse_index": 5, "discovered_at": "2026-02-01"}
    assert candidates([old, fresh])[0] == fresh


def test_daily_preparation_reads_new_snapshot_without_disabling_shared_mongo(tmp_path, monkeypatch):
    from tools.pregenerate_demos import load_candidates, ProductService
    import os
    monkeypatch.setenv("MONGO_URI", "mongodb://shared-budget.invalid")
    monkeypatch.setattr(ProductService, "get_discovery_products", lambda: pytest.fail("Live catalog is stale before sync"))
    product = {**PRODUCT, "source_url": "https://publisher.example/news", "description_en": "Find and review web evidence",
               "why_matters": "独立来源验证检索结果，帮助团队减少人工核对时间。", "why_matters_en": "Checks independent sources for teams reviewing web evidence.",
               "discovered_at": "2026-09-27"}
    snapshot = tmp_path / "products.json"
    snapshot.write_text(json.dumps([product, {**product, "name": "Unverified", "website": "https://unverified.example", "needs_verification": True}]), encoding="utf-8")
    loaded = load_candidates(snapshot)
    assert [p["name"] for p in loaded] == [product["name"]]
    assert os.environ["MONGO_URI"] == "mongodb://shared-budget.invalid"


@pytest.mark.parametrize("kind", ["video", "image", "search", "document", "board"])
def test_workspace_contract_is_bounded_data_only(spec, kind):
    spec["workspace"] = {"kind": kind, "label": {"zh": "任务", "en": "Brief"}, "initial": {"zh": "示例", "en": "Example"}, "html": "<script />"}
    assert "html" not in validate_experience(spec)["workspace"]
    spec["workspace"]["kind"] = "iframe"
    with pytest.raises(ValueError, match="workspace"):
        validate_experience(spec)
    spec["workspace"]["kind"] = kind
    spec["workspace"]["initial"]["en"] = "x" * 201
    with pytest.raises(ValueError, match="text"):
        validate_experience(spec)


def test_generate_then_replay_and_other_visitors_use_same_cache(client, store, spec, monkeypatch):
    monkeypatch.setattr(service, "providers", lambda: [("relay", "https://relay.example", "secret", "model")])
    generate = MagicMock(return_value=spec)
    monkeypatch.setattr(service, "generate_spec", generate)
    result = client.post("/api/v1/demos/generate", json={"product_id": "demo-product"})
    assert result.status_code == 200 and result.json["quota"]["remaining"] == 2
    for _ in range(3):
        assert client.post("/api/v1/demos/generate", json={"product_id": "demo-product"}).json["cached"]
    other = create_app().test_client().post("/api/v1/demos/generate", json={"product_id": "demo-product"})
    assert other.json["quota"]["remaining"] == 3
    assert generate.call_count == 1
    assert "secret" not in json.dumps(result.json)


@pytest.mark.parametrize("body", [None, [], {}, {"product_id": []}, {"product_id": ""}, {"product_id": "x" * 161}])
def test_invalid_requests_do_not_spend(client, body):
    assert client.post("/api/v1/demos/generate", json=body).status_code == 400


def test_unconfigured_or_unknown_is_not_reported_as_ai_success(client):
    assert client.post("/api/v1/demos/generate", json={"product_id": "missing"}).status_code == 404
    r = client.post("/api/v1/demos/generate", json={"product_id": "demo-product"})
    assert r.status_code == 503 and r.json["error"] == "GENERATOR_NOT_CONFIGURED"
    assert r.json["quota"]["used"] == 0


def test_failure_refunds_personal_but_not_global_attempts(client, monkeypatch, store):
    monkeypatch.setattr(service, "providers", lambda: [("relay", "https://relay.example", "secret", "model")])
    monkeypatch.setattr(service, "generate_spec", MagicMock(side_effect=requests.Timeout))
    r = client.post("/api/v1/demos/generate", json={"product_id": "demo-product"})
    assert r.status_code == 503 and r.json["error"] == "GENERATION_TIMEOUT"
    assert r.json["quota"]["remaining"] == 3 and r.json["quota"]["site_remaining"] == 19
    assert store.get(cache_key(PRODUCT)) is None


def test_concurrent_requests_cannot_exceed_daily_limit(store):
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda i: store.reserve(str(i), "one-visitor"), range(12)))
    assert sum(r["state"] == "reserved" for r in results) == 3
    assert store.quota("one-visitor")["used"] == 3
    assert DemoStore(store.path).quota("one-visitor")["remaining"] == 0


def test_global_budget_stops_new_visitors(store, monkeypatch):
    monkeypatch.setenv("DEMO_DAILY_GLOBAL_LIMIT", "2")
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda i: store.reserve(str(i), "visitor-" + str(i)), range(8)))
    assert sum(r["state"] == "reserved" for r in results) == 2
    assert store.quota("brand-new-visitor")["site_remaining"] == 0


def test_same_product_deduplicates_and_invalid_token_cannot_finish(store):
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda i: store.reserve("shared", "visitor-" + str(i)), range(8)))
    assert [r["state"] for r in results].count("reserved") == 1
    assert [r["state"] for r in results].count("pending") == 7
    with pytest.raises(StoreUnavailable):
        store.finish("shared", "wrong-token", {})


def test_utc_reset_and_expired_lease_refund(store, monkeypatch):
    lease = store.reserve("a", "user")
    monkeypatch.setattr(demo_store.time, "time", lambda: 10**12)
    assert store.reserve("a", "user")["state"] == "reserved"
    assert store.quota("user")["used"] == 1
    with pytest.raises(StoreUnavailable):
        store.finish("a", lease["token"], {})
    monkeypatch.setattr(demo_store, "day_info", lambda: ("2099-01-01", "2099-01-02T00:00:00+00:00"))
    assert store.quota("user")["used"] == 0
    assert store.quota("user")["site_remaining"] == 20


def test_production_requires_shared_storage(monkeypatch):
    monkeypatch.setattr(demo_store, "get_mongo_db", lambda: None)
    monkeypatch.setenv("VERCEL", "1")
    with pytest.raises(StoreUnavailable):
        DemoStore()


def test_production_requires_signed_identity(client, monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("DEMO_COOKIE_SECRET", raising=False)
    assert client.post("/api/v1/demos/generate", json={"product_id": "demo-product"}).json["error"] == "IDENTITY_NOT_CONFIGURED"


def test_catalog_search_ready_filter_and_product_change_invalidates_cache(client, store, spec):
    key = cache_key(PRODUCT)
    lease = store.reserve(key, "publisher")
    store.finish(key, lease["token"], service.envelope(PRODUCT, spec, "curated"))
    assert client.get("/api/v1/demos/catalog?q=demo&filter=ready").json["total"] == 1
    assert client.get("/api/v1/demos/catalog?q=nomatch").json["total"] == 0
    assert cache_key({**PRODUCT, "description": "Changed capabilities"}) != key
    assert cache_key({**PRODUCT, "dark_horse_index": 4}) == key


def test_schema_rejects_executable_widgets_sources_and_unbounded_controls(spec):
    bad = copy.deepcopy(spec)
    bad["steps"][0]["widget"] = "iframe"
    with pytest.raises(ValueError):
        validate_experience(bad)
    bad = copy.deepcopy(spec)
    bad["sources"][0]["url"] = "javascript:alert(1)"
    with pytest.raises(ValueError):
        validate_experience(bad)
    with pytest.raises(ValueError):
        validate_experience(spec, allowed_sources=["https://different.example"])
    valid = validate_experience({**spec, "script": "alert(1)"})
    assert "script" not in valid


@pytest.mark.parametrize("protocol", ["openai", "anthropic"])
def test_provider_protocol_validation_and_secret_isolation(monkeypatch, spec, protocol):
    monkeypatch.setenv("DEMO_API_PROTOCOL", protocol)
    monkeypatch.setenv("DEMO_API_KEY", "private-key")
    monkeypatch.setenv("DEMO_API_BASE_URL", "https://relay.example/v1")
    monkeypatch.setattr(service, "providers", lambda: [("relay", "https://relay.example/v1", "private-key", "model")])
    body = {"content": [{"type": "text", "text": json.dumps(spec)}]} if protocol == "anthropic" else {"choices": [{"message": {"content": json.dumps(spec)}}]}
    response = MagicMock()
    response.__enter__.return_value = response
    response.iter_content.return_value = [json.dumps(body).encode()]
    post = MagicMock(return_value=response)
    monkeypatch.setattr(service.requests, "post", post)
    assert service.generate_spec(PRODUCT) == validate_experience(spec)
    kwargs = post.call_args.kwargs
    assert "private-key" not in json.dumps(kwargs["json"])
    assert post.call_args.args[0].endswith("/messages" if protocol == "anthropic" else "/chat/completions")
    assert kwargs["json"]["max_tokens"] <= 3600


def _mock_completions(monkeypatch, specs, stops=None):
    monkeypatch.setenv("DEMO_API_PROTOCOL", "anthropic")
    monkeypatch.setenv("DEMO_API_KEY", "private-key")
    monkeypatch.setattr(service, "providers", lambda: [("relay", "https://relay.example/v1", "private-key", "claude")])
    responses = []
    for index, spec in enumerate(specs):
        body = {"content": [{"type": "text", "text": json.dumps(spec)}],
                "stop_reason": stops[index] if stops else "end_turn"}
        response = MagicMock()
        response.__enter__.return_value = response
        response.iter_content.return_value = [json.dumps(body).encode()]
        responses.append(response)
    post = MagicMock(side_effect=responses)
    monkeypatch.setattr(service.requests, "post", post)
    return post


def test_invalid_outcome_is_repaired_once_and_charged_once(client, store, spec, monkeypatch, caplog):
    invalid = copy.deepcopy(spec)
    invalid["steps"][0]["options"][0]["output"]["en"] = "Improved by 20%"
    post = _mock_completions(monkeypatch, [invalid, spec])
    result = client.post("/api/v1/demos/generate", json={"product_id": "demo-product"})
    assert result.status_code == 200
    assert result.json["quota"]["remaining"] == 2 and result.json["quota"]["site_remaining"] == 19
    assert post.call_count == 2
    assert "Unsupported measured or executed outcome" in post.call_args.kwargs["json"]["messages"][-1]["content"]
    assert "GENERATION_INVALID_RESPONSE" in caplog.text and "private-key" not in caplog.text
    assert client.post("/api/v1/demos/generate", json={"product_id": "demo-product"}).json["cached"]
    assert post.call_count == 2


@pytest.mark.parametrize("protocol,stop", [("anthropic", "max_tokens"), ("openai", "length")])
def test_truncated_output_is_detected_even_if_json_is_valid(monkeypatch, spec, protocol, stop):
    if protocol == "anthropic":
        body = {"content": [{"type": "text", "text": json.dumps(spec)}], "stop_reason": stop}
    else:
        body = {"choices": [{"message": {"content": json.dumps(spec)}, "finish_reason": stop}]}
    with pytest.raises(service.GenerationFailure, match="GENERATION_INCOMPLETE"):
        service._content(body, protocol == "anthropic")


def test_truncated_completion_regenerates_a_complete_spec(monkeypatch, spec):
    post = _mock_completions(monkeypatch, [{"steps": []}, spec], ["max_tokens", "end_turn"])
    assert service.generate_spec(PRODUCT) == validate_experience(spec)
    assert post.call_count == 2


def test_failed_repair_refunds_personal_credit_and_never_publishes_invalid_spec(client, store, spec, monkeypatch):
    invalid = {**spec, "sources": [{"url": "https://invented.example", "label": {"zh": "来源", "en": "Source"}}]}
    post = _mock_completions(monkeypatch, [invalid, invalid])
    result = client.post("/api/v1/demos/generate", json={"product_id": "demo-product"})
    assert result.status_code == 503 and result.json["error"] == "GENERATION_INVALID_RESPONSE"
    assert post.call_count == 2
    assert result.json["quota"]["remaining"] == 3 and result.json["quota"]["site_remaining"] == 19
    assert store.get(cache_key(PRODUCT)) is None


def test_repair_does_not_start_when_time_budget_is_exhausted(monkeypatch, spec):
    post = _mock_completions(monkeypatch, [{**spec, "steps": []}])
    clock = iter([0, 0, 50, 50, 50])
    monkeypatch.setattr(service.time, "monotonic", lambda: next(clock))
    with pytest.raises(service.GenerationFailure, match="GENERATION_INVALID_RESPONSE"):
        service.generate_spec(PRODUCT)
    assert post.call_count == 1


@pytest.mark.parametrize("status,code", [(429, "GENERATOR_BUSY"), (401, "GENERATOR_UNAVAILABLE")])
def test_provider_http_errors_are_safe_and_not_retried(client, monkeypatch, spec, caplog, status, code):
    post = _mock_completions(monkeypatch, [])
    response = requests.Response()
    response.status_code = status
    post.side_effect = requests.HTTPError("private-key and provider body must not leak", response=response)
    result = client.post("/api/v1/demos/generate", json={"product_id": "demo-product"})
    assert result.json["error"] == code and result.json["quota"]["remaining"] == 3
    assert post.call_count == 1
    assert "private-key" not in caplog.text and "private-key" not in json.dumps(result.json)


@pytest.mark.parametrize("failure", [requests.ReadTimeout(), requests.HTTPError(response=type("Upstream", (), {"status_code": 503})())])
def test_temporary_provider_failure_retries_once_with_same_credit(client, spec, monkeypatch, failure):
    post = _mock_completions(monkeypatch, [spec])
    response = next(post.side_effect)
    post.side_effect = [failure, response]
    result = client.post("/api/v1/demos/generate", json={"product_id": "demo-product"})
    assert result.status_code == 200 and result.json["quota"]["remaining"] == 2
    assert result.json["quota"]["site_remaining"] == 19 and post.call_count == 2


def test_repeated_timeout_stops_after_two_calls_and_refunds(client, spec, monkeypatch):
    post = _mock_completions(monkeypatch, [])
    post.side_effect = requests.ReadTimeout()
    result = client.post("/api/v1/demos/generate", json={"product_id": "demo-product"})
    assert result.json["error"] == "GENERATION_TIMEOUT"
    assert result.json["quota"]["remaining"] == 3 and post.call_count == 2


def test_exhausted_quota_returns_429_without_calling_provider(client, store, monkeypatch):
    monkeypatch.setenv("DEMO_DAILY_USER_LIMIT", "0")
    monkeypatch.setattr(service, "providers", lambda: [("relay", "https://relay.example", "key", "model")])
    generate = MagicMock()
    monkeypatch.setattr(service, "generate_spec", generate)
    r = client.post("/api/v1/demos/generate", json={"product_id": "demo-product"})
    assert r.status_code == 429 and r.json["error"] == "DAILY_LIMIT"
    assert r.json["quota"]["remaining"] == 0
    generate.assert_not_called()


def test_rejects_unsubstantiated_metric_or_file_claims(spec):
    for text in ("Improved by 20%", "已导出 PNG", "Exported: image.png", "文件已保存本地", "saved to your device"):
        bad = copy.deepcopy(spec)
        bad["steps"][0]["options"][0]["output"]["en"] = text
        with pytest.raises(ValueError):
            validate_experience(bad)


def test_all_published_experiences_validate_and_match_snapshots():
    root = Path(__file__).resolve().parents[1]
    entries = service.published()
    assert len(entries) >= 5
    for key, entry in entries.items():
        assert validate_experience(entry["spec"]) == entry["spec"]
        front = json.loads((root / "crawler/data/demos" / (key + ".json")).read_text(encoding="utf-8"))
        assert front == entry


def test_legacy_generation_shares_daily_budget_and_cached_replay_is_free(client, store, spec, monkeypatch):
    from app.routes import legacy_demos
    monkeypatch.setenv("DEMO_DAILY_USER_LIMIT", "1")
    monkeypatch.setattr(service, "providers", lambda: [("relay", "https://relay.example", "key", "model")])
    monkeypatch.setattr(service, "generate_spec", lambda product: spec)
    monkeypatch.setattr(legacy_demos.demo_service, "is_configured", lambda: True)
    monkeypatch.setattr(legacy_demos.DemoRepository, "get", lambda slug: None)
    generate = MagicMock()
    monkeypatch.setattr(legacy_demos.demo_service, "generate", generate)
    first = client.post("/api/v1/demos/generate", json={"product_id": "demo-product"})
    assert first.status_code == 200 and first.json["quota"]["remaining"] == 0
    blocked = client.post("/api/v1/demos/demo-product/generate", json={})
    assert blocked.status_code == 429
    generate.assert_not_called()
    assert client.get("/api/v1/demos/status").json["quota"]["site_remaining"] == 19
    monkeypatch.setattr(legacy_demos.DemoRepository, "get", lambda slug: {"product_slug": slug})
    replay = client.post("/api/v1/demos/demo-product/generate", json={})
    assert replay.status_code == 200 and replay.json["cached"]
    assert client.get("/api/v1/demos/status").json["quota"]["site_remaining"] == 19


def test_legacy_provider_failure_refunds_daily_credit(client, monkeypatch):
    from app.routes import legacy_demos
    monkeypatch.setattr(legacy_demos.demo_service, "is_configured", lambda: True)
    monkeypatch.setattr(legacy_demos.DemoRepository, "get", lambda slug: None)
    monkeypatch.setattr(legacy_demos.demo_service, "generate", lambda *args: {"success": False, "error": "PROVIDER_UNAVAILABLE"})
    legacy_demos._generate_tracker.clear()
    response = client.post("/api/v1/demos/demo-product/generate", json={})
    assert response.status_code == 503
    assert response.json["quota"]["remaining"] == 3
    assert response.json["quota"]["site_remaining"] == 19
    assert "HttpOnly" in response.headers["Set-Cookie"]


def test_catalog_preserves_company_logo_sources(client, monkeypatch):
    product = {**PRODUCT, "logo_url": "https://product.example/logo.svg", "logo": "https://product.example/icon.png"}
    monkeypatch.setattr(demos.ProductService, "get_discovery_products", lambda: [product])
    result = client.get("/api/v1/demos/catalog").json["products"][0]
    assert result["logo_url"] == product["logo_url"]
    assert result["logo"] == product["logo"]


def test_legacy_seeds_are_in_backend_deployment_snapshot():
    from app.services.demo_spec import validate_spec
    root = Path(__file__).resolve().parents[1]
    for path in (root / "crawler/data/demos/published").glob("*.json"):
        target = root / "backend/data/demos/published" / path.name
        assert target.read_bytes() == path.read_bytes()
        assert validate_spec(json.loads(target.read_text(encoding="utf-8")))


@pytest.mark.parametrize("source,expected", [("html", True), ("unknown", False)])
def test_official_html_cdn_logos_survive_backend_normalization(source, expected):
    from app.services.product_filters import _sanitize_logo_url
    url = "https://framerusercontent.com/images/company.png"
    product = {**PRODUCT, "logo_url": url, "logo_source": source}
    _sanitize_logo_url(product)
    assert product["logo_url"] == (url if expected else "")


def test_html_logo_provenance_does_not_allow_executable_urls():
    from app.services.product_filters import _sanitize_logo_url
    product = {**PRODUCT, "logo_url": "javascript:alert(1)", "logo_source": "html"}
    _sanitize_logo_url(product)
    assert product["logo_url"] == ""
