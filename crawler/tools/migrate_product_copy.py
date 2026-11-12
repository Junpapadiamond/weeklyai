#!/usr/bin/env python3
"""Apply a reviewed text-only manifest to existing MongoDB product records.

Every record is preflighted before any write. Each subsequent write uses compare
and set against all preflighted text values, never upserts, and never changes
other fields. A concurrent conflict stops the run; the receipt identifies any
earlier completed writes. --rollback reverses the same before/after manifest.
Neither database connection details nor product text are printed to logs.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys


ALLOWED_FIELDS = frozenset({'description', 'description_en', 'why_matters', 'why_matters_en'})
DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / 'data' / 'migrations' / 'product_copy_focus_2026_11_12.json'


class MigrationError(RuntimeError):
    """A safe operational error, containing no database values or credentials."""


def validate_manifest(manifest):
    if not isinstance(manifest, dict) or manifest.get('version') != 1:
        raise MigrationError('Invalid migration manifest.')
    products = manifest.get('products')
    if not isinstance(products, list) or not products:
        raise MigrationError('Manifest has no products.')
    keys = set()
    for product in products:
        if not isinstance(product, dict):
            raise MigrationError('Invalid product entry.')
        name, key, fields = (product.get(k) for k in ('name', '_sync_key', 'fields'))
        if not isinstance(name, str) or not name.strip() or not isinstance(key, str) or not key.strip() or key in keys:
            raise MigrationError('Missing or duplicate product identity.')
        keys.add(key)
        if not isinstance(fields, dict) or not fields or not set(fields) <= ALLOWED_FIELDS:
            raise MigrationError(f'Unapproved migration fields: {name}.')
        for values in fields.values():
            if (not isinstance(values, dict) or set(values) != {'before', 'after'}
                    or not all(isinstance(values[k], str) for k in ('before', 'after'))
                    or values['before'] == values['after']):
                raise MigrationError(f'Invalid text transition: {name}.')
        legacy_records = product.get('legacy_records', [])
        if not isinstance(legacy_records, list):
            raise MigrationError(f'Invalid legacy record declarations: {name}.')
        for legacy in legacy_records:
            if not isinstance(legacy, dict) or set(legacy) != {'_sync_key', 'before'}:
                raise MigrationError(f'Invalid legacy record declaration: {name}.')
            legacy_key, before = legacy['_sync_key'], legacy['before']
            if (not isinstance(legacy_key, str) or not legacy_key.strip()
                    or legacy_key in keys):
                raise MigrationError('Missing or duplicate product identity.')
            keys.add(legacy_key)
            if (not isinstance(before, dict) or set(before) != set(fields)
                    or not all(isinstance(value, str) for value in before.values())):
                raise MigrationError(f'Invalid legacy text transitions: {name}.')
    return products


def declared_records(product):
    """Expand only explicitly reviewed identities, retaining each one's old text."""
    records = {product['_sync_key']: product}
    for legacy in product.get('legacy_records', []):
        records[legacy['_sync_key']] = {
            'name': product['name'], '_sync_key': legacy['_sync_key'],
            'fields': {field: {'before': legacy['before'][field], 'after': values['after']}
                       for field, values in product['fields'].items()},
        }
    return records


def write_receipt(path, receipt):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def migrate_collection(collection, manifest, receipt_path, *, rollback=False, dry_run=False):
    """Preflight the entire manifest, then CAS only its approved text fields."""
    products = validate_manifest(manifest)
    destination = 'before' if rollback else 'after'
    prepared = []
    # Do not mutate any record until every product and every field is compatible.
    for product in products:
        declarations = declared_records(product)
        projection = {'_id': 1, '_sync_key': 1, 'name': 1, **{field: 1 for field in product['fields']}}
        # Matching names expose undeclared copies, but never authorize updating them.
        matches = list(collection.find({'$or': [
            {'_sync_key': {'$in': list(declarations)}}, {'name': product['name']},
        ]}, projection))
        if not matches:
            raise MigrationError(f'Preflight identity mismatch: {product["name"]}. No writes performed.')
        seen = set()
        for current in matches:
            key = current.get('_sync_key')
            if not isinstance(key, str) or key not in declarations or key in seen:
                raise MigrationError(f'Preflight identity mismatch: {product["name"]}. No writes performed.')
            seen.add(key)
            if current.get('name') != product['name']:
                raise MigrationError(f'Preflight name mismatch: {product["name"]}. No writes performed.')
            declaration = declarations[key]
            for field, values in declaration['fields'].items():
                if field not in current or current[field] not in (values['before'], values['after']):
                    raise MigrationError(f'Preflight text mismatch: {product["name"]}. No writes performed.')
            observed = {field: current[field] for field in declaration['fields']}
            target = {field: values[destination] for field, values in declaration['fields'].items()}
            changes = {field: text for field, text in target.items() if observed[field] != text}
            prepared.append((declaration, current['_id'], observed, target, changes))

    receipt = {key: value for key, value in manifest.items() if key != 'execution'}
    receipt['execution'] = {
        'started_at': datetime.now(timezone.utc).isoformat(),
        'direction': 'rollback' if rollback else 'forward',
        'dry_run': dry_run, 'status': 'preflight_passed',
        'products': [{
            'name': product['name'], '_sync_key': product['_sync_key'],
            'observed_before': observed, 'intended_after': target,
            'status': 'pending' if changes else 'unchanged', 'field_count': len(changes),
        } for product, _, observed, target, changes in prepared],
    }
    # Store the complete reversible manifest and observed values before the first CAS.
    write_receipt(receipt_path, receipt)
    if dry_run:
        receipt['execution']['status'] = 'dry_run'
        write_receipt(receipt_path, receipt)
        return receipt

    for (product, identity, observed, _, changes), record in zip(prepared, receipt['execution']['products']):
        if not changes:
            continue
        query = {'_id': identity, '_sync_key': product['_sync_key'], 'name': product['name'], **observed}
        try:
            result = collection.update_one(query, {'$set': changes}, upsert=False)
        except Exception:
            # A transport failure may occur after the server applied the CAS.
            # Preserve that uncertainty and never print the driver's exception.
            record['status'] = 'write_outcome_unknown'
            receipt['execution']['status'] = 'stopped'
            write_receipt(receipt_path, receipt)
            raise MigrationError(f'Write outcome requires inspection: {product["name"]}.') from None
        if result.matched_count != 1:
            record['status'] = 'concurrent_conflict'
            receipt['execution']['status'] = 'stopped'
            write_receipt(receipt_path, receipt)
            raise MigrationError(f'Concurrent change detected: {product["name"]}. Stopped without overwriting it.')
        record['status'] = 'updated'
        write_receipt(receipt_path, receipt)
    receipt['execution']['status'] = 'complete'
    receipt['execution']['finished_at'] = datetime.now(timezone.utc).isoformat()
    write_receipt(receipt_path, receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument('--receipt', type=Path, default=Path('product-copy-migration-receipt.json'))
    parser.add_argument('--rollback', action='store_true', help='Restore the manifest before values, with the same preflight and CAS checks.')
    parser.add_argument('--dry-run', action='store_true', help='Preflight and save a receipt without updating records.')
    args = parser.parse_args(argv)
    client = None
    try:
        manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
        validate_manifest(manifest)
        uri = os.getenv('MONGO_URI', '').strip().strip('"').strip("'")
        if not uri:
            raise MigrationError('MONGO_URI is required; no writes performed.')
        from pymongo import MongoClient
        client = MongoClient(uri, serverSelectionTimeoutMS=10000, connectTimeoutMS=10000)
        client.admin.command('ping')
        database = client.get_default_database(os.getenv('MONGO_DB_NAME', 'weeklyai').strip() or 'weeklyai')
        receipt = migrate_collection(database.products, manifest, args.receipt,
                                     rollback=args.rollback, dry_run=args.dry_run)
        records = receipt['execution']['products']
        for record in records:
            print(f'{record["name"]}: {record["status"]}, {record["field_count"]} fields')
        print(f'Products: {len(manifest["products"])}; records: {len(records)}; '
              f'updated: {sum(r["status"] == "updated" for r in records)}; '
              f'unchanged: {sum(r["status"] == "unchanged" for r in records)}')
        return 0
    except MigrationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (OSError, ValueError):
        print('Migration input or receipt could not be read or written.', file=sys.stderr)
        return 1
    except Exception:
        print('MongoDB migration failed; connection details are not logged.', file=sys.stderr)
        return 1
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass


if __name__ == '__main__':
    raise SystemExit(main())
