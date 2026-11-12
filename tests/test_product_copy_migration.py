import copy
import json
from pathlib import Path

import mongomock
import pytest

from tools.migrate_product_copy import MigrationError, main, migrate_collection, validate_manifest


@pytest.fixture
def migration():
    manifest = {'version': 1, 'id': 'test-copy', 'products': [
        {'name': 'Example One', '_sync_key': 'one.test', 'fields': {
            'description': {'before': 'Original task description', 'after': 'Reviewed task description'},
            'why_matters_en': {'before': 'Funding-led text', 'after': 'Sourced product evidence'},
        }},
        {'name': 'Example Two', '_sync_key': 'two.test', 'fields': {
            'why_matters': {'before': '原有文案', 'after': '有来源的产品价值文案'},
        }},
    ]}
    collection = mongomock.MongoClient().weeklyai.products
    for product in manifest['products']:
        collection.insert_one({
            'name': product['name'], '_sync_key': product['_sync_key'],
            **{field: values['before'] for field, values in product['fields'].items()},
            'funding_total': '$25M', 'dark_horse_index': 4, 'logo_url': 'https://logo.test/real.png',
            'latest_news': 'Financing announcement retained', 'extra': {'evidence': ['original quote']},
        })
    return collection, manifest


def test_preflight_mismatch_on_later_product_means_zero_writes(migration, tmp_path, monkeypatch):
    collection, manifest = migration
    collection.update_one({'_sync_key': 'two.test'}, {'$set': {'why_matters': 'A newer editorial change'}})
    original = list(collection.find())
    monkeypatch.setattr(collection, 'update_one', lambda *a, **kw: pytest.fail('Preflight must finish before any update'))
    with pytest.raises(MigrationError, match='Preflight text mismatch'):
        migrate_collection(collection, manifest, tmp_path / 'receipt.json')
    assert list(collection.find()) == original


@pytest.mark.parametrize('fault', ['changed', 'missing', 'null'])
def test_failed_preflight_receipt_only_contains_declared_raw_text(migration, tmp_path, monkeypatch, fault):
    collection, manifest = migration
    if fault == 'missing':
        collection.update_one({'_sync_key': 'one.test'}, {'$unset': {'description': ''}})
    else:
        collection.update_one({'_sync_key': 'one.test'}, {'$set': {
            'description': 'Unreviewed text remains unchanged' if fault == 'changed' else None,
        }})
    # Include another permitted text field, unrelated fields, and an undeclared copy.
    collection.update_one({'_sync_key': 'two.test'}, {'$set': {
        'description_en': 'Raw untranslated evidence', 'private_metadata': 'must not be exported',
    }})
    collection.insert_one({'name': 'Example Two', '_sync_key': 'not-declared.test',
                           'description': 'Undeclared record must not be exported'})
    original = list(collection.find())
    monkeypatch.setattr(collection, 'update_one', lambda *a, **kw: pytest.fail('Failed preflight cannot write'))
    path = tmp_path / 'failure.json'
    with pytest.raises(MigrationError, match='field description') as caught:
        migrate_collection(collection, manifest, path)
    assert 'Unreviewed text' not in str(caught.value)
    assert list(collection.find()) == original
    receipt = json.loads(path.read_text(encoding='utf-8'))
    assert set(receipt) == {'execution'}
    assert set(receipt['execution']) == {'status', 'products'}
    assert receipt['execution']['status'] == 'preflight_failed'
    records = {record['_sync_key']: record for record in receipt['execution']['products']}
    assert set(records) == {'one.test', 'two.test'}
    for key, record in records.items():
        assert set(record) == {'name', '_sync_key', 'fields', 'missing_fields'}
        raw = collection.find_one({'_sync_key': key})
        permitted = {'description', 'description_en', 'why_matters', 'why_matters_en'}
        assert record['fields'] == {field: raw[field] for field in permitted if field in raw}
        assert record['missing_fields'] == sorted(permitted - raw.keys())
    assert records['two.test']['fields']['description_en'] == 'Raw untranslated evidence'
    assert ('description' in records['one.test']['missing_fields']) == (fault == 'missing')
    assert '_id' not in path.read_text(encoding='utf-8')


def test_migration_is_idempotent_and_preserves_all_unapproved_fields(migration, tmp_path):
    collection, manifest = migration
    before = {p['_sync_key']: p for p in collection.find()}
    # A partially already-applied document is allowed, and unchanged fields stay guarded.
    collection.update_one({'_sync_key': 'one.test'}, {'$set': {'description': 'Reviewed task description'}})
    receipt = migrate_collection(collection, manifest, tmp_path / 'receipt.json')
    assert [p['status'] for p in receipt['execution']['products']] == ['updated', 'updated']
    assert receipt['products'] == manifest['products']
    for product in manifest['products']:
        current = collection.find_one({'_sync_key': product['_sync_key']})
        for field, values in product['fields'].items():
            assert current[field] == values['after']
        for field, value in before[product['_sync_key']].items():
            if field not in product['fields']:
                assert current[field] == value
    repeated = migrate_collection(collection, manifest, tmp_path / 'repeat.json')
    assert {p['status'] for p in repeated['execution']['products']} == {'unchanged'}
    assert collection.count_documents({}) == 2


def test_receipt_is_reversible_and_rollback_is_idempotent(migration, tmp_path):
    collection, manifest = migration
    path = tmp_path / 'forward.json'
    migrate_collection(collection, manifest, path)
    receipt = json.loads(path.read_text(encoding='utf-8'))
    reverse = migrate_collection(collection, receipt, tmp_path / 'rollback.json', rollback=True)
    assert reverse['execution']['direction'] == 'rollback'
    for product in manifest['products']:
        current = collection.find_one({'_sync_key': product['_sync_key']})
        assert all(current[field] == values['before'] for field, values in product['fields'].items())
    repeated = migrate_collection(collection, receipt, tmp_path / 'rollback-repeat.json', rollback=True)
    assert {p['status'] for p in repeated['execution']['products']} == {'unchanged'}


def test_cas_refuses_a_concurrent_change_and_preserves_receipt(migration, tmp_path, monkeypatch):
    collection, manifest = migration
    real_update = collection.update_one
    def race(query, update, *, upsert):
        assert upsert is False
        assert set(update) == {'$set'}
        assert query['description'] == 'Original task description'
        real_update({'_id': query['_id']}, {'$set': {'description': 'Concurrent editor text'}})
        return real_update(query, update, upsert=upsert)
    monkeypatch.setattr(collection, 'update_one', race)
    path = tmp_path / 'receipt.json'
    with pytest.raises(MigrationError, match='Concurrent change detected'):
        migrate_collection(collection, manifest, path)
    assert collection.find_one({'_sync_key': 'one.test'})['description'] == 'Concurrent editor text'
    assert collection.find_one({'_sync_key': 'two.test'})['why_matters'] == '原有文案'
    receipt = json.loads(path.read_text(encoding='utf-8'))
    assert receipt['execution']['status'] == 'stopped'
    assert receipt['execution']['products'][0]['status'] == 'concurrent_conflict'


@pytest.mark.parametrize('fault', ['missing', 'duplicate', 'missing_field', 'wrong_name'])
def test_preflight_rejects_ambiguous_or_incomplete_records(migration, tmp_path, monkeypatch, fault):
    collection, manifest = migration
    if fault == 'missing':
        collection.delete_one({'_sync_key': 'two.test'})
    elif fault == 'duplicate':
        duplicate = collection.find_one({'_sync_key': 'two.test'})
        duplicate.pop('_id')
        collection.insert_one(duplicate)
    elif fault == 'missing_field':
        collection.update_one({'_sync_key': 'two.test'}, {'$unset': {'why_matters': ''}})
    else:
        collection.update_one({'_sync_key': 'two.test'}, {'$set': {'name': 'Different product'}})
    monkeypatch.setattr(collection, 'update_one', lambda *a, **kw: pytest.fail('No writes after failed preflight'))
    with pytest.raises(MigrationError, match='Preflight'):
        migrate_collection(collection, manifest, tmp_path / 'receipt.json')


def test_manifest_cannot_modify_scoring_or_funding(migration):
    _, manifest = migration
    invalid = copy.deepcopy(manifest)
    invalid['products'][0]['fields']['funding_total'] = {'before': '$25M', 'after': '$50M'}
    with pytest.raises(MigrationError, match='Unapproved migration fields'):
        validate_manifest(invalid)


def test_dry_run_only_preflights_and_writes_receipt(migration, tmp_path, monkeypatch):
    collection, manifest = migration
    monkeypatch.setattr(collection, 'update_one', lambda *a, **kw: pytest.fail('Dry run must not update'))
    receipt = migrate_collection(collection, manifest, tmp_path / 'receipt.json', dry_run=True)
    assert receipt['execution']['status'] == 'dry_run'


def test_missing_secret_fails_explicitly_without_connecting(migration, tmp_path, monkeypatch, capsys):
    _, manifest = migration
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps(manifest), encoding='utf-8')
    monkeypatch.delenv('MONGO_URI', raising=False)
    assert main(['--manifest', str(path)]) == 1
    assert 'MONGO_URI is required' in capsys.readouterr().err


def test_driver_error_never_prints_connection_details(migration, tmp_path, monkeypatch, capsys):
    _, manifest = migration
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps(manifest), encoding='utf-8')
    monkeypatch.setenv('MONGO_URI', 'mongodb://dummy-user:dummy-password@invalid.test/weeklyai')
    def fail(*args, **kwargs):
        raise RuntimeError('mongodb://dummy-user:dummy-password@invalid.test/weeklyai')
    monkeypatch.setattr('pymongo.MongoClient', fail)
    assert main(['--manifest', str(path)]) == 1
    captured = capsys.readouterr()
    assert 'MongoDB migration failed' in captured.err
    assert 'dummy-password' not in captured.err + captured.out


def test_committed_manifest_only_contains_reviewed_changes():
    from tools.sync_to_mongodb import build_sync_key
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'crawler/data/migrations/product_copy_focus_2026_11_12.json').read_text(encoding='utf-8'))
    current = json.loads((root / 'crawler/data/products_featured.json').read_text(encoding='utf-8'))
    by_key = {build_sync_key(product): product for product in current}
    products = validate_manifest(manifest)
    assert sum(len(product['fields']) for product in products) == 22
    assert {p['name'] for p in products} == {'Primero', 'Rently', 'Synapse Analytics', 'Daytona', 'Holo', 'AI Diagnostics', 'Harvey'}
    for product in products:
        assert by_key[product['_sync_key']]['name'] == product['name']
        for field, transition in product['fields'].items():
            assert by_key[product['_sync_key']][field] == transition['after']
    harvey = next(product for product in products if product['name'] == 'Harvey')
    assert harvey['legacy_records'] == [{
        '_sync_key': 'harveyllc.com', 'before': {
            'description': 'AI legal technology platform that automates legal document analysis and contract review for law firms.',
            'why_matters': 'Raised $300M Series D round at $3B valuation, demonstrating strong market adoption in legal AI sector.',
        },
    }]


def add_legacy_record(collection, manifest):
    product = manifest['products'][0]
    legacy = {'_sync_key': 'one-legacy.test', 'before': {
        'description': 'Legacy task description', 'why_matters_en': 'Legacy financing text',
    }}
    product['legacy_records'] = [legacy]
    collection.insert_one({
        'name': product['name'], '_sync_key': legacy['_sync_key'], **legacy['before'],
        'website': 'https://one-legacy.test', 'funding_total': '$10M', 'dark_horse_index': 4,
    })
    return legacy


@pytest.mark.parametrize('primary_present', [True, False])
def test_declared_legacy_copies_migrate_and_roll_back_their_own_text(migration, tmp_path, primary_present):
    collection, manifest = migration
    legacy = add_legacy_record(collection, manifest)
    if not primary_present:
        collection.delete_one({'_sync_key': 'one.test'})
    original = {record['_sync_key']: record for record in collection.find()}
    path = tmp_path / 'forward.json'
    result = migrate_collection(collection, manifest, path)
    expected_keys = {'one-legacy.test', 'two.test'} | ({'one.test'} if primary_present else set())
    assert {record['_sync_key'] for record in result['execution']['products']} == expected_keys
    for key in expected_keys - {'two.test'}:
        current = collection.find_one({'_sync_key': key})
        for field, values in manifest['products'][0]['fields'].items():
            assert current[field] == values['after']
        for field, value in original[key].items():
            if field not in manifest['products'][0]['fields']:
                assert current[field] == value
    repeated = migrate_collection(collection, manifest, tmp_path / 'repeat.json')
    assert {record['status'] for record in repeated['execution']['products']} == {'unchanged'}
    saved = json.loads(path.read_text(encoding='utf-8'))
    assert saved['products'][0]['legacy_records'] == [legacy]
    migrate_collection(collection, saved, tmp_path / 'rollback.json', rollback=True)
    assert {record['_sync_key']: record for record in collection.find()} == original


@pytest.mark.parametrize('fault', ['unknown_text', 'unknown_key', 'duplicate_key'])
def test_legacy_preflight_conflict_prevents_every_write(migration, tmp_path, monkeypatch, fault):
    collection, manifest = migration
    add_legacy_record(collection, manifest)
    if fault == 'unknown_text':
        collection.update_one({'_sync_key': 'one-legacy.test'}, {'$set': {'description': 'Unreviewed live text'}})
    elif fault == 'unknown_key':
        unknown = collection.find_one({'_sync_key': 'one-legacy.test'})
        unknown.pop('_id')
        unknown['_sync_key'] = 'undeclared.test'
        collection.insert_one(unknown)
    else:
        duplicate = collection.find_one({'_sync_key': 'one-legacy.test'})
        duplicate.pop('_id')
        collection.insert_one(duplicate)
    original = list(collection.find())
    monkeypatch.setattr(collection, 'update_one', lambda *a, **kw: pytest.fail('No writes after failed preflight'))
    with pytest.raises(MigrationError, match='Preflight'):
        migrate_collection(collection, manifest, tmp_path / 'receipt.json')
    assert list(collection.find()) == original


@pytest.mark.parametrize('fault', ['empty_fields', 'unapproved_field', 'duplicate_identity'])
def test_legacy_manifest_is_explicit_and_limited_to_product_fields(migration, fault):
    collection, manifest = migration
    legacy = add_legacy_record(collection, manifest)
    if fault == 'empty_fields':
        legacy['before'].clear()
    elif fault == 'unapproved_field':
        legacy['before']['website'] = 'https://different.test'
    else:
        legacy['_sync_key'] = 'two.test'
    with pytest.raises(MigrationError):
        validate_manifest(manifest)


@pytest.mark.parametrize('legacy_first', [True, False])
def test_harvey_legacy_subset_preserves_missing_english_and_merges_reviewed_copy(tmp_path, legacy_first):
    from app.services.product_repository import ProductRepository
    from tools.migrate_product_copy import declared_records

    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'crawler/data/migrations/product_copy_focus_2026_11_12.json').read_text(encoding='utf-8'))
    collection = mongomock.MongoClient().weeklyai.products
    for product in manifest['products']:
        for key, declaration in declared_records(product).items():
            collection.insert_one({
                'name': product['name'], '_sync_key': key, 'website': f'https://{key}',
                **{field: values['before'] for field, values in declaration['fields'].items()},
                'dark_horse_index': 4, 'funding_total': '$300M',
            })
    original = {record['_sync_key']: record for record in collection.find()}
    receipt = migrate_collection(collection, manifest, tmp_path / 'forward.json')
    assert len(receipt['execution']['products']) == 8
    assert sum(record['field_count'] for record in receipt['execution']['products']) == 24
    legacy = collection.find_one({'_sync_key': 'harveyllc.com'})
    primary = collection.find_one({'_sync_key': 'harvey.ai/blog'})
    for field in ('description_en', 'why_matters_en'):
        assert field not in legacy
    harvey = next(product for product in manifest['products'] if product['name'] == 'Harvey')
    ordered = [legacy, primary] if legacy_first else [primary, legacy]
    merged = ProductRepository._dedupe_products(copy.deepcopy(ordered))
    assert len(merged) == 1
    assert all(merged[0][field] == values['after'] for field, values in harvey['fields'].items())
    repeated = migrate_collection(collection, manifest, tmp_path / 'repeat.json')
    assert {record['status'] for record in repeated['execution']['products']} == {'unchanged'}
    migrate_collection(collection, receipt, tmp_path / 'rollback.json', rollback=True)
    assert {record['_sync_key']: record for record in collection.find()} == original
