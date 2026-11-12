"""Exact-spec withdrawals keep rejected examples auditable without blocking products."""
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path


REGISTRY_PATH = Path(__file__).resolve().parents[2] / "data" / "demo_withdrawals.json"


def withdrawal_signature():
    stat = REGISTRY_PATH.stat()
    return str(REGISTRY_PATH), stat.st_mtime_ns, stat.st_size


def canonical_spec_sha256(spec):
    """Hash only the spec; timestamps, provenance and other entry metadata may change."""
    encoded = json.dumps(spec, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def _load_registry(path, mtime_ns, size):
    # Stat arguments invalidate the process cache when the audit registry changes.
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("Demo withdrawals must be a list")
    entries = {}
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {"cache_key", "spec_sha256", "reason"}
                or not isinstance(row["cache_key"], str) or not row["cache_key"].strip()
                or not isinstance(row["reason"], str) or not row["reason"].strip()
                or not isinstance(row["spec_sha256"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", row["spec_sha256"])):
            raise ValueError("Invalid demo withdrawal record")
        entries.setdefault(row["cache_key"], set()).add(row["spec_sha256"])
    return entries


def is_withdrawn(entry, cache_key=None):
    """Only an exact registered key and spec are hidden, never an entire product."""
    registry = _load_registry(*withdrawal_signature())
    if not isinstance(entry, dict):
        return False
    key = cache_key if cache_key is not None else entry.get("cache_key")
    digests = registry.get(key)
    return bool(digests and canonical_spec_sha256(entry.get("spec")) in digests)


def withdrawn_cache_keys():
    """Keys needing a digest check, not a denylist of every spec at those keys."""
    return frozenset(_load_registry(*withdrawal_signature()))
