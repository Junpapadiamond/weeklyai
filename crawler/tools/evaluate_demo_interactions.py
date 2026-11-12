#!/usr/bin/env python3
"""Evaluate the CURRENT generator; live calls use its existing daily reservations.

Default: inspect the twelve-case cache baseline, with no model calls.
--live --product Melius --product Exa --product Lovable runs a small real-provider
pilot, retains raw model replies for inspection, and NEVER publishes its output.
Only --evaluation-limit can raise this local actor's allowance (explicit user
authorization required). Production limits and the site cap are unchanged.
A separate persistent attempt ledger counts failed evaluations too.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.services import demo_experiences as service  # noqa: E402
from app.services.demo_contract import cache_key  # noqa: E402
from app.services.demo_interaction import validate_interaction  # noqa: E402
from app.services.demo_prompt import GENERATOR_REVISION, generation_context  # noqa: E402
from app.services.demo_store import DemoStore  # noqa: E402
from app.services.product_service import ProductService  # noqa: E402

CASES = ["Melius", "Sonilo", "Black Forest Labs", "GasLab", "Higgsfield", "Conductor",
         "Orchids", "Namespace", "Lovable", "Exa", "Daloopa", "Autentic"]
ACTOR = "generator-evaluation-v1"
ARTIFACTS = ROOT / "artifacts/demo-generator-evaluation"
ALIASES = {"Orchids": "Orchids 1.0", "Autentic": "Autentic AI"}


class EvaluationBudget:
    """Local session attempt cap, independent of refunded daily user credits."""

    def __init__(self, path, legacy_directory=None):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=10)
        self.db.execute("CREATE TABLE IF NOT EXISTS attempts (id INTEGER PRIMARY KEY, evaluation_key TEXT, created_at TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY)")
        # Migrate the original pilot once: each raw file is ONE evaluation,
        # even when that evaluation contains two provider requests.
        with self.db:
            if not self.db.execute("SELECT 1 FROM metadata WHERE key='legacy_imported'").fetchone():
                if legacy_directory:
                    for raw in sorted(legacy_directory.glob("*-raw.json")):
                        if json.loads(raw.read_text(encoding="utf-8")):
                            self.db.execute("INSERT INTO attempts(evaluation_key,created_at) VALUES (?,?)",
                                            ("legacy:" + raw.stem, "initial-pilot"))
                self.db.execute("INSERT INTO metadata(key) VALUES ('legacy_imported')")

    def used(self):
        return self.db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]

    def acquire(self, key, limit):
        if limit not in (3, 9):
            raise ValueError("Only the default 3 or explicitly authorized 9 evaluation cap is supported")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            if self.used() >= limit:
                return False
            self.db.execute("INSERT INTO attempts(evaluation_key,created_at) VALUES (?,?)",
                            (key, datetime.now(timezone.utc).isoformat()))
            return True


def products():
    # Match the actual API resolver, including its first-match identity. Raw
    # crawler records can contain duplicate names and different fingerprints.
    result = {}
    for product in ProductService.get_all_products():
        result.setdefault(str(product.get("name", "")).casefold(), product)
    return result


def inspect_spec(spec):
    """Structural/behavior coverage only, NOT semantic correctness or human UX."""
    interaction = spec.get("interaction")
    if not interaction:
        steps = spec.get("steps", [])
        return {"interaction_contract": False, "legacy_sections": len(steps),
                "conditional_sections": sum(any(o.get("when") for o in s.get("options", [])) for s in steps),
                "manual_review": "required"}
    valid = validate_interaction(interaction)
    return {"interaction_contract": True, "kind": valid["kind"], "variants": len(valid["variants"]),
            "input_combinations": len(valid["variants"]), "manual_review": "required",
            "human_comprehension": "not_tested"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--product", action="append", choices=CASES)
    parser.add_argument("--output", type=Path, default=ARTIFACTS)
    parser.add_argument("--evaluation-limit", type=int, choices=(3, 9), default=3,
                        help="Local actor only; 9 requires explicit authorization. Failures count toward the cap.")
    args = parser.parse_args(argv)
    chosen = args.product or CASES
    if args.live and len(chosen) > 3:
        parser.error("Choose at most three products per pilot. Existing daily quotas still apply.")
    args.output.mkdir(parents=True, exist_ok=True)
    catalog = products()
    store = DemoStore() if args.live else None
    budget = EvaluationBudget(ARTIFACTS / "evaluation-budget.sqlite3", ARTIFACTS) if args.live else None
    if args.live and not service.provider_available():
        parser.error("The current demo provider is not configured; no model calls made.")
    entries = list(service.published().values())
    report = {"revision": GENERATOR_REVISION, "mode": "live_pilot" if args.live else "stored_baseline",
              "release_approved": False, "human_comprehension": "not_tested", "cases": []}
    if store:
        report["quota_before"] = store.quota(ACTOR, user_limit=args.evaluation_limit)
        report["attempt_budget_before"] = {"used": budget.used(), "limit": args.evaluation_limit}
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_directory = args.output / "runs" / run_id if args.live else args.output
    run_directory.mkdir(parents=True, exist_ok=True)
    for name in chosen:
        product = catalog.get(ALIASES.get(name, name).casefold())
        if not product:
            report["cases"].append({"product": name, "result": "catalog_missing"})
            continue
        context = generation_context(product)
        row = {"product": name, "product_id": str(product.get("_id", "")),
               "cache_key": cache_key(product), "grounding": context["grounding"]}
        if not store:
            entry = service.ready_experience(product) or next((e for e in entries if e.get("product_name", "").casefold() == product["name"].casefold()), None)
            row.update(inspect_spec(entry["spec"]) if entry else {"result": "no_stored_example"})
            row["current_fingerprint_ready"] = bool(service.ready_experience(product))
            report["cases"].append(row)
            continue
        key = "evaluation:" + GENERATOR_REVISION + ":" + cache_key(product)
        if budget.used() >= args.evaluation_limit:
            row["result"] = "evaluation_attempt_limit"
            report["cases"].append(row)
            break
        reservation = store.reserve(key, ACTOR, user_limit=args.evaluation_limit)
        state = reservation["state"]
        if state == "cached":
            row.update(result="cached_evaluation", **inspect_spec(reservation["payload"]["spec"]))
            report["cases"].append(row)
            continue
        if state != "reserved":
            row["result"] = state
            report["cases"].append(row)
            if state == "limited":
                break
            continue
        if not budget.acquire(key, args.evaluation_limit):
            store.finish(key, reservation["token"])
            row["result"] = "evaluation_attempt_limit"
            report["cases"].append(row)
            break
        attempts = []
        (run_directory / (name.replace(" ", "-").lower() + "-input.json")).write_text(
            json.dumps({"context": context, "website": product.get("website"), "source_url": product.get("source_url"),
                        "product_id": row["product_id"], "cache_key": row["cache_key"]}, ensure_ascii=False, indent=2), encoding="utf-8")
        row["model"] = service.providers()[0][3]
        original = service._completion
        started = time.monotonic()
        def observe(*params):
            body = original(*params)
            anthropic = params[1] == "/messages"
            # Auth headers/URLs are deliberately not recorded.
            if anthropic:
                raw = "".join(p.get("text", "") for p in body.get("content", []) if p.get("type") == "text")
                stop = body.get("stop_reason")
            else:
                choice = (body.get("choices") or [{}])[0]
                raw = choice.get("message", {}).get("content", "")
                stop = choice.get("finish_reason")
            attempts.append({"content": raw, "stop": stop, "usage": body.get("usage", {})})
            return body
        service._completion = observe
        try:
            spec = service.generate_spec(product)
            entry = service.envelope(product, spec, "ai")
            store.finish(key, reservation["token"], entry)
            row.update(result="validated", **inspect_spec(spec))
            row["spec_sha256"] = hashlib.sha256(json.dumps(spec, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            (run_directory / (name.replace(" ", "-").lower() + ".json")).write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as error:
            store.finish(key, reservation["token"])
            row.update(result=getattr(error, "code", type(error).__name__), constraint=getattr(error, "constraint", ""))
        finally:
            service._completion = original
        row.update(attempts=len(attempts), seconds=round(time.monotonic() - started, 2))
        (run_directory / (name.replace(" ", "-").lower() + "-raw.json")).write_text(json.dumps(attempts, ensure_ascii=False, indent=2), encoding="utf-8")
        report["cases"].append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    if store:
        report["quota_after"] = store.quota(ACTOR, user_limit=args.evaluation_limit)
        report["attempt_budget_after"] = {"used": budget.used(), "limit": args.evaluation_limit}
    destination = run_directory / ("live-report.json" if args.live else "baseline-report.json")
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(destination), "cases": len(report["cases"]), "published": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
