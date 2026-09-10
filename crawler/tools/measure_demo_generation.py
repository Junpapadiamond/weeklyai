#!/usr/bin/env python3
"""Measure whether on-demand demo generation actually works.

Generation has never been run against a real model, so its pass rate against
the DemoSpec schema is unknown. Turning it on is a measurement, not a decision -
this is the measurement.

Picks real products across all tiers, generates a demo for each, and reports how
many passed on the first attempt, how many needed the retry, and exactly which
schema rule the failures broke. That last column is the useful one: it says
whether to change the prompt, the model, or the schema.

    export PERPLEXITY_API_KEY=...
    export DEMO_GENERATION_ENABLED=true
    python3 crawler/tools/measure_demo_generation.py --count 9

Nothing is published. Use --save to write passing specs for inspection.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from app.services import demo_service  # noqa: E402
from app.services.demo_repository import DemoRepository  # noqa: E402

CATALOG = os.path.join(ROOT, "crawler", "data", "products_featured.json")


def pick_products(count: int, seed: int) -> list[dict]:
    """A spread across tiers, so one easy tier cannot flatter the average."""
    with open(CATALOG, encoding="utf-8") as handle:
        catalog = json.load(handle)

    eligible = [
        p for p in catalog
        if (p.get("dark_horse_index") or 0) >= 4
        and str(p.get("website", "")).startswith("http")
        and not p.get("needs_verification")
        and str(p.get("description") or p.get("description_en") or "").strip()
    ]
    by_tier: dict[str, list[dict]] = collections.defaultdict(list)
    for product in eligible:
        by_tier[demo_service.classify_tier(product)].append(product)

    rng = random.Random(seed)
    for pool in by_tier.values():
        rng.shuffle(pool)

    # Round-robin across tiers so the sample stays balanced AND reaches `count`,
    # even when one tier has fewer eligible products than an even split wants.
    chosen: list[dict] = []
    cursors = dict.fromkeys(by_tier, 0)
    while len(chosen) < count:
        took_any = False
        for tier in sorted(by_tier):
            if len(chosen) >= count:
                break
            index = cursors[tier]
            if index < len(by_tier[tier]):
                chosen.append(by_tier[tier][index])
                cursors[tier] = index + 1
                took_any = True
        if not took_any:
            break
    return chosen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=9, help="how many demos to generate (default 9)")
    parser.add_argument("--seed", type=int, default=7, help="sampling seed, so a run is repeatable")
    parser.add_argument("--save", metavar="DIR", help="write passing specs here for inspection")
    args = parser.parse_args()

    if not demo_service.generation_enabled():
        print("DEMO_GENERATION_ENABLED is not set. Export it as true to measure.")
        return 1
    if not demo_service._key():
        print("PERPLEXITY_API_KEY is not set.")
        return 1

    products = pick_products(args.count, args.seed)
    if not products:
        print("No eligible products found in the catalog.")
        return 1

    print(f"model={demo_service._model()}  products={len(products)}\n")
    print(f"{'product':<26}{'tier':<12}{'result':<10}{'s':>6}  detail")
    print("-" * 100)

    outcomes = collections.Counter()
    failures: list[tuple[str, str]] = []
    durations: list[float] = []

    for product in products:
        name = str(product.get("name", ""))[:24]
        slug = DemoRepository.slug_for(product)
        tier = demo_service.classify_tier(product)

        started = time.monotonic()
        # attempts are counted by instrumenting the one call the service makes
        attempts = {"n": 0}
        original = demo_service._call_model

        def counting_call(prompt, timeout, _original=original, _attempts=attempts):
            _attempts["n"] += 1
            return _original(prompt, timeout)

        demo_service._call_model = counting_call
        try:
            result = demo_service.generate(product, slug, tier)
        finally:
            demo_service._call_model = original
        elapsed = time.monotonic() - started
        durations.append(elapsed)

        if result.get("success"):
            outcome = "PASS" if attempts["n"] == 1 else "PASS(retry)"
            detail = f"{len(result['spec']['steps'])} steps, "
            detail += ", ".join(s["widget"]["type"] for s in result["spec"]["steps"])
            if args.save:
                os.makedirs(args.save, exist_ok=True)
                with open(os.path.join(args.save, f"{slug}.json"), "w", encoding="utf-8") as handle:
                    json.dump(result["spec"], handle, ensure_ascii=False, indent=2)
        else:
            outcome = result.get("error", "FAIL")
            detail = str(result.get("detail", ""))[:60]
            failures.append((name, detail or outcome))

        outcomes[outcome] += 1
        print(f"{name:<26}{tier:<12}{outcome:<10}{elapsed:>5.0f}s  {detail[:52]}")

    total = len(products)
    passed = outcomes["PASS"] + outcomes["PASS(retry)"]
    print("-" * 100)
    print(f"\nfirst try   {outcomes['PASS']}/{total}")
    print(f"after retry {outcomes['PASS(retry)']}/{total}")
    print(f"failed      {total - passed}/{total}")
    if durations:
        durations.sort()
        print(f"\nmedian {durations[len(durations) // 2]:.0f}s, slowest {durations[-1]:.0f}s "
              f"(budget is {demo_service.GENERATION_BUDGET_SECONDS}s)")

    if failures:
        print("\nWhat the failures broke:")
        for name, detail in failures:
            print(f"  {name}: {detail}")
        print("\nA repeated field means the prompt or schema needs work; scattered")
        print("failures usually mean the model is too weak - try DEMO_MODEL first.")

    rate = passed / total
    print(f"\npass rate {rate:.0%}")
    if rate >= 0.8:
        print("Good enough to switch on. Keep the review queue for a while regardless.")
    elif rate >= 0.5:
        print("Marginal. Try a stronger DEMO_MODEL before switching on.")
    else:
        print("Do not switch on yet. Read the failures above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
