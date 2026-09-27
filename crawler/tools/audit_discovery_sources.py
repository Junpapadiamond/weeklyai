"""Probe source freshness and usable evidence without any model calls or writes to the catalog."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.claude_discover import collect_articles


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="logs/discovery/source-health.json")
    args = parser.parse_args()
    articles, sources = collect_articles(days=14, limit=12)
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "sources": sources,
              "readable_articles": len(articles),
              "evidence": [{k: a[k] for k in ("url", "title", "published_at", "source")} for a in articles]}
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for source in sources:
        print(source["source"], source["status"], source.get("eligible_articles", 0))
    print(f"Readable articles: {len(articles)}; report: {target}")
    return 0 if articles else 1


if __name__ == "__main__":
    sys.exit(main())
