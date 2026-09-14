"""Durable demo cache, generation leases and atomic daily quotas.

Mongo is shared by deployed instances. SQLite is only a local development fallback;
serverless deployments fail closed rather than pretending /tmp is a shared budget.
"""
import json
import os
import sqlite3
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from app.services.product_repository import get_mongo_db, _mongo_uri_configured

LEASE_SECONDS = 150  # Outlives the 90-second generation + persistence window.

def env_int(name, default):
    try:
        return min(10000, max(0, int(os.getenv(name, default))))
    except (ValueError, TypeError):
        return default


def day_info():
    now = datetime.now(timezone.utc)
    reset = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return now.date().isoformat(), reset.isoformat()


def production():
    return bool(os.getenv("VERCEL")) or os.getenv("FLASK_ENV") == "production"


class StoreUnavailable(RuntimeError):
    pass


class DemoStore:
    def __init__(self, sqlite_path=None):
        self.db = None if sqlite_path else get_mongo_db()
        self.path = None
        if self.db is None:
            if not sqlite_path and (_mongo_uri_configured() or production()):
                raise StoreUnavailable("Shared demo storage unavailable")
            default = Path(__file__).resolve().parents[3] / "artifacts" / "demo-runtime.sqlite3"
            self.path = str(sqlite_path or os.getenv("DEMO_SQLITE_PATH") or default)
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            with self.connect() as conn:
                conn.executescript("""
                CREATE TABLE IF NOT EXISTS demo_cache (key TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS demo_usage (day TEXT, actor TEXT, used INTEGER NOT NULL, PRIMARY KEY(day, actor));
                CREATE TABLE IF NOT EXISTS demo_leases (key TEXT PRIMARY KEY, token TEXT, day TEXT, actor TEXT, expires REAL);
                """)

    def connect(self):
        conn = sqlite3.connect(self.path, timeout=8)
        conn.row_factory = sqlite3.Row
        return conn

    def get(self, key):
        if self.db is not None:
            entry = self.db.demo_cache.find_one({"_id": key})
            return entry.get("payload") if entry else None
        with self.connect() as conn:
            entry = conn.execute("SELECT payload FROM demo_cache WHERE key=?", (key,)).fetchone()
            return json.loads(entry[0]) if entry else None

    def keys(self):
        if self.db is not None:
            return {item["_id"] for item in self.db.demo_cache.find({}, {"_id": 1})}
        with self.connect() as conn:
            return {item[0] for item in conn.execute("SELECT key FROM demo_cache")}

    def quota(self, actor, user_limit=None):
        day, reset = day_info()
        personal_limit = env_int("DEMO_DAILY_USER_LIMIT", 3) if user_limit is None else user_limit
        site_limit = env_int("DEMO_DAILY_GLOBAL_LIMIT", 20)
        if self.db is not None:
            row = self.db.demo_daily.find_one({"_id": day}) or {}
            used = row.get("users", {}).get(actor, 0)
            attempts = row.get("attempts", 0)
        else:
            with self.connect() as conn:
                rows = dict(conn.execute("SELECT actor,used FROM demo_usage WHERE day=?", (day,)).fetchall())
            used, attempts = rows.get(actor, 0), rows.get("site", 0)
        return {"limit": personal_limit, "used": used, "remaining": max(0, personal_limit - used),
                "site_limit": site_limit, "site_remaining": max(0, site_limit - attempts), "resets_at": reset}

    def reserve(self, key, actor, user_limit=None):
        """Return cached / pending / limited / reserved without overspending in a race."""
        personal = env_int("DEMO_DAILY_USER_LIMIT", 3) if user_limit is None else user_limit
        site = env_int("DEMO_DAILY_GLOBAL_LIMIT", 20)
        day, _ = day_info()
        token, now = uuid.uuid4().hex, time.time()
        if self.db is not None:
            cached = self.get(key)
            if cached:
                return {"state": "cached", "payload": cached}
            try:
                previous = self.db.demo_leases.find_one_and_update(
                    {"_id": key, "expires": {"$lte": now}},
                    {"$set": {"token": token, "day": day, "actor": actor, "expires": now + LEASE_SECONDS, "charged": False}},
                    upsert=True, return_document=ReturnDocument.BEFORE)
            except DuplicateKeyError:
                return {"state": "pending"}
            if previous and previous.get("charged"):
                self.db.demo_daily.update_one({"_id": previous["day"], f"users.{previous['actor']}": {"$gt": 0}},
                                              {"$inc": {f"users.{previous['actor']}": -1}})
            # Recheck after acquiring the lease; another request might just have finished.
            cached = self.get(key)
            if cached:
                self.db.demo_leases.delete_one({"_id": key, "token": token})
                return {"state": "cached", "payload": cached}
            try:
                self.db.demo_daily.update_one({"_id": day}, {"$setOnInsert": {"attempts": 0, "users": {}}}, upsert=True)
            except DuplicateKeyError:
                pass
            accepted = self.db.demo_daily.find_one_and_update(
                {"_id": day, "attempts": {"$lt": site}, "$expr": {"$lt": [{"$ifNull": [f"$users.{actor}", 0]}, personal]}},
                {"$inc": {"attempts": 1, f"users.{actor}": 1}}, return_document=ReturnDocument.AFTER)
            if not accepted:
                self.db.demo_leases.delete_one({"_id": key, "token": token})
                return {"state": "limited"}
            self.db.demo_leases.update_one({"_id": key, "token": token}, {"$set": {"charged": True}})
            return {"state": "reserved", "token": token}
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            cached = conn.execute("SELECT payload FROM demo_cache WHERE key=?", (key,)).fetchone()
            if cached:
                return {"state": "cached", "payload": json.loads(cached[0])}
            lease = conn.execute("SELECT * FROM demo_leases WHERE key=?", (key,)).fetchone()
            if lease and lease["expires"] > now:
                return {"state": "pending"}
            if lease:
                conn.execute("UPDATE demo_usage SET used=MAX(0,used-1) WHERE day=? AND actor=?", (lease["day"], lease["actor"]))
                conn.execute("DELETE FROM demo_leases WHERE key=?", (key,))
            for subject in (actor, "site"):
                conn.execute("INSERT OR IGNORE INTO demo_usage VALUES (?,?,0)", (day, subject))
            used = dict(conn.execute("SELECT actor,used FROM demo_usage WHERE day=?", (day,)).fetchall())
            if used[actor] >= personal or used["site"] >= site:
                return {"state": "limited"}
            conn.execute("UPDATE demo_usage SET used=used+1 WHERE day=? AND actor IN (?, 'site')", (day, actor))
            conn.execute("INSERT INTO demo_leases VALUES (?,?,?,?,?)", (key, token, day, actor, now + LEASE_SECONDS))
            return {"state": "reserved", "token": token}

    def finish(self, key, token, payload=None):
        """Failed attempts refund the visitor but retain site cost accounting."""
        if self.db is not None:
            lease = self.db.demo_leases.find_one({"_id": key, "token": token})
            if not lease:
                raise StoreUnavailable("Generation lease expired")
            if payload is not None:
                self.db.demo_cache.replace_one({"_id": key}, {"_id": key, "payload": payload}, upsert=True)
            removed = self.db.demo_leases.find_one_and_delete({"_id": key, "token": token})
            if payload is None and removed:
                self.db.demo_daily.update_one({"_id": lease["day"], f"users.{lease['actor']}": {"$gt": 0}},
                                              {"$inc": {f"users.{lease['actor']}": -1}})
            return
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            lease = conn.execute("SELECT * FROM demo_leases WHERE key=? AND token=?", (key, token)).fetchone()
            if not lease:
                raise StoreUnavailable("Generation lease expired")
            if payload is None:
                conn.execute("UPDATE demo_usage SET used=MAX(0,used-1) WHERE day=? AND actor=?", (lease["day"], lease["actor"]))
            else:
                conn.execute("INSERT OR REPLACE INTO demo_cache VALUES (?,?)", (key, json.dumps(payload, ensure_ascii=False)))
            conn.execute("DELETE FROM demo_leases WHERE key=? AND token=?", (key, token))
