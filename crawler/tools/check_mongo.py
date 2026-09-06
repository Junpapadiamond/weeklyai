#!/usr/bin/env python3
"""Diagnose the MongoDB setup end to end.

Answers the question the Atlas console cannot: is this URI reachable from
*here*, which database does it actually resolve to, and does it hold what the
backend expects to read? Every line of output is safe to paste into a chat -
credentials are redacted and never printed.

    export MONGO_URI='mongodb+srv://...'
    python3 crawler/tools/check_mongo.py

Exit code is 0 when the backend would serve from MongoDB, 1 otherwise.
"""
from __future__ import annotations

import os
import re
import socket
import time
from urllib.parse import urlsplit

EXPECTED_COLLECTIONS = ("products", "blogs", "demos", "candidates")
# The backend reads these; anything missing means it silently falls back to JSON.
BACKEND_CRITICAL = ("products",)

OK, WARN, BAD = "  ok  ", " warn ", " FAIL "


def redact(uri: str) -> str:
    """Strip credentials so output can be shared."""
    return re.sub(r"://[^@/]+@", "://<user>:<pass>@", uri or "")


def line(status: str, message: str) -> None:
    print(f"[{status}] {message}")


def check_uri() -> tuple[str, str | None]:
    uri = os.environ.get("MONGO_URI", "").strip().strip("'\"")
    if not uri:
        line(BAD, "MONGO_URI is not set in this shell.")
        print("        The backend runs on JSON snapshots without it - that is a")
        print("        supported mode, not a crash, which is why this can go unnoticed.")
        return "", None
    if not uri.startswith(("mongodb://", "mongodb+srv://")):
        line(BAD, f"MONGO_URI does not look like a Mongo URI: {redact(uri)[:60]}")
        return "", None

    scheme = uri.split("://", 1)[0]
    line(OK, f"MONGO_URI is set ({scheme})")

    # A database path is what get_default_database() falls back from.
    path = urlsplit(uri.replace("mongodb+srv://", "https://").replace("mongodb://", "https://")).path
    db_in_uri = path.strip("/").split("/")[0] or None
    if db_in_uri:
        line(OK, f"URI names a database: {db_in_uri}")
    else:
        fallback = os.environ.get("MONGO_DB_NAME", "weeklyai")
        line(WARN, f"URI names no database; code falls back to MONGO_DB_NAME or 'weeklyai' -> {fallback}")
        print("        crawler/database/db_handler.py calls get_database() with no default,")
        print("        so it raises where the backend and sync tool would fall back.")
    return uri, db_in_uri


def check_dns(uri: str) -> bool:
    """The failure mode recorded in AUDIT-2026-09-02: the SRV host does not resolve."""
    if not uri.startswith("mongodb+srv://"):
        return True
    host = uri.split("://", 1)[1].split("/")[0].split("@")[-1].split("?")[0]
    try:
        socket.getaddrinfo(f"_mongodb._tcp.{host}", None)
    except socket.gaierror:
        pass  # SRV lookups do not go through getaddrinfo; fall through to the A record probe
    try:
        socket.getaddrinfo(host, 27017)
        line(OK, f"host resolves: {host}")
        return True
    except socket.gaierror as error:
        line(BAD, f"host does not resolve: {host} ({error})")
        print("        A +srv URI needs DNS SRV lookups. Blocked or filtered DNS is the")
        print("        usual cause; a paused Atlas cluster is the other.")
        return False


def main() -> int:
    print("MongoDB check\n" + "=" * 52)
    uri, _ = check_uri()
    if not uri:
        return 1
    if not check_dns(uri):
        return 1

    try:
        from pymongo import MongoClient
        from pymongo.errors import PyMongoError
    except ImportError:
        line(BAD, "pymongo is not installed here (pip install -r backend/requirements.txt)")
        return 1

    client = None
    try:
        started = time.monotonic()
        client = MongoClient(uri, serverSelectionTimeoutMS=8000, connectTimeoutMS=8000)
        client.admin.command("ping")
        line(OK, f"connected and pinged in {int((time.monotonic() - started) * 1000)} ms")
    except PyMongoError as error:
        line(BAD, f"cannot connect: {type(error).__name__}: {str(error)[:200]}")
        print("        Most common causes, in order:")
        print("        1. Network Access allowlist - Vercel and CI have dynamic egress IPs,")
        print("           so they need 0.0.0.0/0 there. Your laptop's IP alone is not enough.")
        print("        2. Database user missing, or wrong password (URL-encode special chars).")
        print("        3. Cluster paused - free clusters pause after ~60 days idle.")
        if client is not None:
            client.close()
        return 1

    try:
        db = client.get_default_database(os.getenv("MONGO_DB_NAME", "weeklyai"))
        line(OK, f"database in use: {db.name}")

        names = set(db.list_collection_names())
        empty_critical = False
        for name in EXPECTED_COLLECTIONS:
            if name not in names:
                status = BAD if name in BACKEND_CRITICAL else WARN
                line(status, f"collection '{name}' missing")
                if name in BACKEND_CRITICAL:
                    empty_critical = True
                continue
            count = db[name].count_documents({})
            if count == 0 and name in BACKEND_CRITICAL:
                line(BAD, f"collection '{name}' exists but is empty")
                empty_critical = True
            else:
                line(OK if count else WARN, f"{name}: {count} documents")

        for name in ("products", "blogs", "demos"):
            if name not in names:
                continue
            indexes = db[name].index_information()
            unique = [k for k, v in indexes.items() if v.get("unique")]
            if unique:
                line(OK, f"{name} unique index: {', '.join(unique)}")
            else:
                line(WARN, f"{name} has no unique index - run sync_to_mongodb.py --ensure-indexes")

        print("-" * 52)
        if empty_critical:
            line(BAD, "backend would fall back to JSON snapshots")
            print("        Run: python3 crawler/tools/sync_to_mongodb.py --all")
            return 1
        line(OK, "backend would serve from MongoDB")
        if "demos" not in names or db["demos"].count_documents({}) == 0:
            print("        Demos are not in Mongo yet; on-demand demos will live only in")
            print("        process memory and be lost on cold start. Run:")
            print("        python3 crawler/tools/sync_to_mongodb.py --demos")
        return 0
    except PyMongoError as error:
        line(BAD, f"connected, but inspecting the database failed: {str(error)[:200]}")
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
