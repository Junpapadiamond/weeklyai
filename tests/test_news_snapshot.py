import json
from pathlib import Path
import sys

import mongomock
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'crawler')]
from app.services import product_repository as repo
from app.services.product_service import ProductService
from tools import sync_to_mongodb as sync


@pytest.fixture
def snapshot_store(tmp_path, monkeypatch):
    db = mongomock.MongoClient().weeklyai
    monkeypatch.setenv('MONGO_URI', 'mongodb://test/weeklyai')
    monkeypatch.setattr(repo, 'get_mongo_db', lambda: db)
    monkeypatch.setattr(repo, 'BLOGS_NEWS_FILE', str(tmp_path / 'blogs_news.json'))
    monkeypatch.setattr(sync, 'DATA_DIR', str(tmp_path))
    repo.ProductRepository.refresh_cache()
    yield db, tmp_path
    repo.ProductRepository.refresh_cache()


def write_snapshot(path, name, stamp):
    items = [{'name': name, 'website': 'https://example.com/' + name, 'source': 'x'}]
    health = {'updated_at': stamp, 'sources': {'x': {'status': 'direct'}}}
    (path / 'blogs_news.json').write_text(json.dumps(items), encoding='utf-8')
    (path / 'news_source_health.json').write_text(json.dumps(health), encoding='utf-8')
    return items, health


def test_new_publication_ignores_legacy_upsert_collection(snapshot_store):
    db, path = snapshot_store
    items, health = write_snapshot(path, 'published', '2026-10-29T10:00:00Z')
    db.blogs.insert_one({'name': 'legacy', 'website': 'https://legacy.test'})
    assert repo.ProductRepository.load_blogs() == items
    assert repo.ProductRepository._cached_news_health == health


def test_atomic_database_snapshot_wins_only_when_newer(snapshot_store):
    db, path = snapshot_store
    latest, health = write_snapshot(path, 'new', '2026-10-29T12:00:00Z')
    assert sync.sync_news_snapshot(db, latest)
    write_snapshot(path, 'old', '2026-10-29T10:00:00Z')
    assert repo.ProductRepository.load_blogs() == latest
    assert repo.ProductRepository._cached_news_health == health
    assert db.blogs.count_documents({}) == 0


def test_new_deployment_wins_over_older_database(snapshot_store):
    db, path = snapshot_store
    old, _ = write_snapshot(path, 'old', '2026-10-29T10:00:00Z')
    sync.sync_news_snapshot(db, old)
    latest, _ = write_snapshot(path, 'new', '2026-10-29T12:00:00Z')
    assert repo.ProductRepository.load_blogs() == latest


def test_empty_refresh_does_not_replace_database_snapshot(snapshot_store):
    db, path = snapshot_store
    items, _ = write_snapshot(path, 'saved', '2026-10-29T10:00:00Z')
    sync.sync_news_snapshot(db, items)
    assert not sync.sync_news_snapshot(db, [])
    assert db.news_snapshots.find_one({'_id': 'current'})['items'] == items


def test_completed_quality_rejection_can_clear_news_without_reviving_legacy(snapshot_store):
    db, path = snapshot_store
    items, _ = write_snapshot(path, 'old', '2026-10-29T10:00:00Z')
    sync.sync_news_snapshot(db, items)
    db.blogs.insert_one({'name': 'legacy', 'website': 'https://legacy.test'})
    _, health = write_snapshot(path, 'unused', '2026-10-29T12:00:00Z')
    health.update(quality_complete=True, quality_policy_version=1)
    (path / 'news_source_health.json').write_text(json.dumps(health), encoding='utf-8')
    (path / 'blogs_news.json').write_text('[]', encoding='utf-8')
    assert repo.ProductRepository.load_blogs() == []
    assert sync.sync_news_snapshot(db, [])
    assert db.news_snapshots.find_one({'_id': 'current'})['items'] == []


def test_mixed_preview_keeps_small_platforms_and_source_query_fetches_all(monkeypatch):
    posts = [{'name': str(i), 'source': 'hackernews', 'website': f'https://example.com/{i}',
              'published_at': '2026-10-29T12:00:00Z'} for i in range(130)]
    posts += [{'name': 'X signal', 'source': 'x', 'website': 'https://x.com/a/status/123',
               'published_at': '2026-10-28T12:00:00Z'}]
    monkeypatch.setattr(ProductService, '_load_blogs', lambda: posts)
    assert len(ProductService.get_blogs_news(120)) == 120
    assert {p['source'] for p in ProductService.get_blogs_news(120)} == {'x', 'hackernews'}
    assert ProductService.get_blogs_by_source('x', 120) == [posts[-1]]
