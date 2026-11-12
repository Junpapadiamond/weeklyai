"""A reviewed bad spec cannot reappear through shipped or persisted cache copies."""
import copy
import json
from pathlib import Path

import mongomock
import pytest

from app import create_app, rate_limiter
from app.routes import demos
from app.services import demo_experiences as service
from app.services import demo_store, demo_withdrawals
from app.services.demo_contract import cache_key, validate_experience
from app.services.demo_store import DemoStore
from app.services.demo_withdrawals import canonical_spec_sha256, is_withdrawn


ROOT = Path(__file__).resolve().parents[1]
KEY = "2561dcea0804ca1875e3e6d5-a28f9e5f9a8c828ad69f68d9"
SHA = "145ff735b348b1cab707344dc5e73ea2ba3ec175ab7f5c4b7bb670d6e244ffd1"


@pytest.fixture
def old_entry():
    return json.loads((ROOT / "backend/data/demos" / f"{KEY}.json").read_text(encoding="utf-8"))


@pytest.fixture
def replacement(old_entry):
    entry = copy.deepcopy(old_entry)
    # A different spec is eligible for normal review/generation; a withdrawal is
    # not a product denylist. This fixture is not a replacement published demo.
    entry["spec"]["scenario"]["en"] += " A different local fixture."
    validate_experience(entry["spec"])
    return entry


@pytest.fixture(autouse=True)
def no_generation(monkeypatch):
    monkeypatch.setattr(service, "generate_spec", lambda *a, **k: pytest.fail("Read paths must not generate"))
    monkeypatch.setattr(service.requests, "post", lambda *a, **k: pytest.fail("No provider calls"))


@pytest.fixture(params=["sqlite", "mongo"])
def store(request, tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_DAILY_USER_LIMIT", "3")
    monkeypatch.setenv("DEMO_DAILY_GLOBAL_LIMIT", "20")
    if request.param == "mongo":
        monkeypatch.setattr(demo_store, "get_mongo_db", lambda: mongomock.MongoClient().weeklyai)
        return DemoStore()
    return DemoStore(tmp_path / "demos.sqlite3")


def persist(store, entry, key=KEY):
    if store.db is not None:
        store.db.demo_cache.replace_one({"_id": key}, {"_id": key, "payload": entry}, upsert=True)
    else:
        with store.connect() as conn:
            conn.execute("INSERT OR REPLACE INTO demo_cache VALUES (?,?)", (key, json.dumps(entry)))


def persisted(store):
    if store.db is not None:
        return store.db.demo_cache.find_one({"_id": KEY})["payload"]
    with store.connect() as conn:
        return json.loads(conn.execute("SELECT payload FROM demo_cache WHERE key=?", (KEY,)).fetchone()[0])


def test_registry_matches_only_canonical_spec_and_key(old_entry, replacement):
    assert canonical_spec_sha256(old_entry["spec"]) == SHA
    assert canonical_spec_sha256(validate_experience(old_entry["spec"])) == SHA
    assert is_withdrawn(old_entry)
    reordered = {key: old_entry["spec"][key] for key in reversed(old_entry["spec"])}
    assert canonical_spec_sha256(reordered) == SHA
    changed_metadata = {**old_entry, "origin": "ai", "generated_at": "2099-01-01", "product_name": "Renamed"}
    assert is_withdrawn(changed_metadata)
    assert is_withdrawn({**changed_metadata, "cache_key": "changed-payload-metadata"}, KEY)
    assert not is_withdrawn(old_entry, "another-cache-key")
    assert not is_withdrawn(replacement)


def test_shipped_cache_is_hidden_but_original_json_is_preserved(old_entry, monkeypatch):
    path = ROOT / "backend/data/demos" / f"{KEY}.json"
    original = path.read_bytes()
    monkeypatch.setattr(service, "_published_signature", None)
    monkeypatch.setattr(service, "_published_entries", {})
    assert KEY not in service.published()
    assert path.read_bytes() == original
    # A copy already loaded in a process must also be filtered after withdrawal.
    service._published_entries[KEY] = old_entry
    assert KEY not in service.published()


def test_shipped_new_spec_at_same_key_is_allowed(old_entry, replacement, tmp_path, monkeypatch):
    (tmp_path / f"{KEY}.json").write_text(json.dumps(replacement), encoding="utf-8")
    monkeypatch.setenv("DEMO_PUBLISHED_PATH", str(tmp_path))
    assert service.published()[KEY] == replacement


def test_store_read_and_keys_do_not_resurrect_or_mutate_withdrawn_copy(store, old_entry):
    persist(store, old_entry)
    before = store.quota("visitor")
    assert store.get(KEY) is None
    assert KEY not in store.keys()
    assert not store.pending(KEY)
    assert store.quota("visitor") == before
    assert persisted(store) == old_entry


def test_keys_read_payload_only_for_registered_intersection(store, old_entry, monkeypatch):
    persist(store, old_entry)
    ordinary_keys = {"ordinary-cache-key", "eval:20261112:melius"}
    for key in ordinary_keys:
        persist(store, {**old_entry, "cache_key": key}, key)
    fetched, queries = [], []
    original_get = store.get

    def tracked_get(key):
        fetched.append(key)
        return original_get(key)

    monkeypatch.setattr(store, "get", tracked_get)
    if store.db is not None:
        original_find = store.db.demo_cache.find

        def tracked_find(*args, **kwargs):
            queries.append((args, kwargs))
            return original_find(*args, **kwargs)

        monkeypatch.setattr(store.db.demo_cache, "find", tracked_find)
    else:
        original_connect = store.connect

        def tracked_connect():
            conn = original_connect()
            conn.set_trace_callback(queries.append)
            return conn

        monkeypatch.setattr(store, "connect", tracked_connect)

    assert store.keys() == ordinary_keys
    assert fetched == [KEY]
    if store.db is not None:
        broad_queries = [(args, kwargs) for args, kwargs in queries if args and args[0] == {}]
        assert broad_queries == [(({}, {"_id": 1}), {})]
    else:
        assert "SELECT key FROM demo_cache" in queries
        payload_reads = [query for query in queries if query.startswith("SELECT") and "payload" in query]
        assert payload_reads == [f"SELECT payload FROM demo_cache WHERE key='{KEY}'"]


def test_reserve_cannot_return_withdrawn_payload_and_keeps_normal_budget(store, old_entry, replacement):
    persist(store, old_entry)
    before = store.quota("visitor")
    result = store.reserve(KEY, "visitor")
    assert result["state"] == "reserved"
    assert "payload" not in result
    during = store.quota("visitor")
    assert during["used"] == before["used"] + 1
    assert during["site_remaining"] == before["site_remaining"] - 1
    assert persisted(store) == old_entry  # audit copy survives until normal finish
    store.finish(KEY, result["token"], replacement)
    assert store.get(KEY) == replacement
    assert KEY in store.keys()
    assert store.reserve(KEY, "another-visitor") == {"state": "cached", "payload": replacement}
    assert store.quota("visitor") == during
    assert store.quota("another-visitor")["used"] == 0


def test_zero_budget_does_not_replay_withdrawn_content_or_charge(store, old_entry):
    persist(store, old_entry)
    before = store.quota("visitor", user_limit=0)
    assert store.reserve(KEY, "visitor", user_limit=0)["state"] == "limited"
    assert store.quota("visitor", user_limit=0) == before
    assert not store.pending(KEY)
    assert persisted(store) == old_entry


def test_gets_and_catalog_hide_shipped_and_store_copies_without_spending(store, old_entry, monkeypatch):
    product = next(p for p in json.loads((ROOT / "backend/data/products_featured.json").read_text(encoding="utf-8"))
                   if p["name"] == "Melius")
    persist(store, old_entry)
    monkeypatch.setattr(demos, "DemoStore", lambda: store)
    monkeypatch.setattr(service, "providers", lambda: [])
    monkeypatch.setattr(demos.ProductService, "get_product_by_id", lambda _: product)
    monkeypatch.setattr(demos.ProductService, "get_discovery_products", lambda: [product])
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("FLASK_ENV", "development")
    rate_limiter.requests.clear()
    client = create_app().test_client()
    before = client.get("/api/v1/demos/status").json["quota"]
    for route in ("prepared", "product"):
        result = client.get(f"/api/v1/demos/{route}/melius")
        assert result.status_code == 200 and result.json["state"] == "not_generated"
        assert result.json.get("experience") is None
        assert "no-store" in result.headers["Cache-Control"]
    catalog = client.get("/api/v1/demos/catalog").json
    assert catalog["ready_count"] == 0 and not catalog["products"][0]["demo_ready"]
    assert client.get("/api/v1/demos/catalog?filter=ready").json["products"] == []
    assert client.get("/api/v1/demos/status").json["quota"] == before
    assert not store.pending(KEY)
    assert persisted(store) == old_entry


def test_registry_changes_apply_without_entry_metadata_changes(old_entry, tmp_path, monkeypatch):
    path = tmp_path / "withdrawals.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(demo_withdrawals, "REGISTRY_PATH", path)
    assert not is_withdrawn(old_entry)
    assert KEY in service.published()
    path.write_text(json.dumps([{"cache_key": KEY, "spec_sha256": SHA, "reason": "Reviewed contradiction"}]), encoding="utf-8")
    assert is_withdrawn(old_entry)
    assert KEY not in service.published()
    path.write_text("[]", encoding="utf-8")
    assert KEY in service.published()


def test_withdrawn_curated_profile_is_not_advertised_as_ready(tmp_path, monkeypatch):
    product = {"_id": "reviewed", "name": "Higgsfield", "website": "https://higgsfield.ai",
               "description": "An isolated reviewed-profile test fixture"}
    spec = service.product_profile(product)
    registry = tmp_path / "withdrawals.json"
    registry.write_text(json.dumps([{"cache_key": cache_key(product), "spec_sha256": canonical_spec_sha256(spec),
                                     "reason": "Test withdrawal of a reviewed profile"}]), encoding="utf-8")
    monkeypatch.setattr(demo_withdrawals, "REGISTRY_PATH", registry)
    monkeypatch.setenv("DEMO_PUBLISHED_PATH", str(tmp_path / "no-shipped-examples"))
    store = DemoStore(tmp_path / "profiles.sqlite3")
    monkeypatch.setattr(demos, "DemoStore", lambda: store)
    monkeypatch.setattr(service, "providers", lambda: [])
    monkeypatch.setattr(demos.ProductService, "get_product_by_id", lambda _: product)
    monkeypatch.setattr(demos.ProductService, "get_discovery_products", lambda: [product])
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("FLASK_ENV", "development")
    rate_limiter.requests.clear()
    assert service.ready_experience(product, store) is None
    response = create_app().test_client().get("/api/v1/demos/catalog").json
    assert response["ready_count"] == 0
    assert not response["products"][0]["demo_ready"]
