# Session: Crawler Discovery + Momentum Refactor
Date: 2026-01-13
Duration: ~28 messages

## Context Snapshot
WeeklyAI crawler coverage was limited by static sources and lack of recency/momentum tracking; user asked for a no-API refactor with daily cadence acceptable.

## What Was Accomplished
- Added history tracking to annotate `first_seen`, `last_seen`, `published_at`, and metric deltas per product.
- Implemented recency/velocity GitHub discovery and a new Hacker News Algolia spider for recent AI launches.
- Updated Product Hunt ingestion to apply recency filtering and removed the hardcoded legacy list.

## Key Decisions & Rationale
| Decision | Why | Alternatives Rejected |
|----------|-----|----------------------|
| Use local JSON history (`products_history.json`) for deltas | No paid APIs and minimal infra change; enables momentum scoring immediately | Database schema changes (Mongo/MySQL) deferred |
| Add HN Algolia source | Free, near-real-time signals for launches without paid API | Product Hunt GraphQL (token required) |
| Recency filters for Product Hunt and GitHub | Focus on emerging products; reduce big-name bias | Keeping legacy list and high-star-only search |

## Current State
- **Working**: Recency-weighted scoring, history annotations, HN + updated GitHub/Product Hunt sources.
- **Broken/Blocked**: None noted; network access still restricted by environment.
- **Modified files**: `crawler/main.py` (history + scoring + HN wiring), `crawler/spiders/base_spider.py` (published_at support), `crawler/spiders/github_spider.py` (recency/velocity discovery), `crawler/spiders/product_hunt_spider.py` (recency filter, no legacy list), `crawler/spiders/hackernews_spider.py` (new), `crawler/spiders/__init__.py` (export new spider).

## Dead Ends (Don't Retry)
- ❌ Using Product Hunt curated legacy list — removed to avoid bias toward big-name, older products.

## Next Steps (Prioritized)
1. [ ] Run the crawler once to generate `crawler/data/products_history.json` and validate new fields.
2. [ ] Tune HN keyword set and time window if coverage is too narrow/wide.

## Environment & Gotchas
- No paid APIs available; solution must remain API-free.
- History file is created at runtime: `crawler/data/products_history.json`.

## Key Code/Commands Reference
```bash
python crawler/main.py --no-db
```
