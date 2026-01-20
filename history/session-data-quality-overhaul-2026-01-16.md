# Session: WeeklyAI Data Quality Overhaul
Date: 2026-01-16
Duration: ~15 messages

## Context Snapshot
Implemented architecture change to separate curated products from automated crawler news. Crawler now defaults to safe mode that never overwrites `products_featured.json`.

## What Was Accomplished
- Added `--news-only` (default), `--generate-candidates`, `--legacy` flags to crawler
- Backend now loads products ONLY from `products_featured.json` (no more MongoDB mix)
- Enhanced `add_product.py` with auto-logo fetch and direct save to featured
- Created `approve_candidate.py` for candidate → featured workflow
- Created `list_candidates.py` for reviewing AI-discovered products
- Set up `crawler/data/candidates/` directory structure

## Key Decisions & Rationale
| Decision | Why | Alternatives Rejected |
|----------|-----|----------------------|
| Default to `--news-only` | Protect curated products from crawler overwrites | Default to legacy mode (too risky) |
| Products from JSON only | Ensures human-curated quality | MongoDB + JSON merge (caused 179 low-quality items) |
| Candidate review workflow | Balance automation with curation | Full auto (low quality) or full manual (too slow) |

## Current State
- **Working**: All new flags, tools created and tested (`--help` verified)
- **Modified files**:
  - `crawler/main.py` - new modes + `save_news_only()`, `save_candidates()` methods
  - `backend/app/services/product_service.py` - simplified to JSON-only loading
  - `crawler/tools/add_product.py` - complete rewrite with auto-fetch
  - `crawler/tools/approve_candidate.py` - NEW
  - `crawler/tools/list_candidates.py` - NEW
  - `crawler/data/candidates/.gitkeep` - NEW

## Dead Ends (Don't Retry)
- ❌ None in this session

## Next Steps (Prioritized)
1. [ ] Run `python main.py --generate-candidates` to test candidate discovery
2. [ ] Verify API endpoints return curated products only
3. [ ] Consider adding `--reject-candidate` tool for discarding bad candidates

## Environment & Gotchas
- Python command is `python3` not `python` on this system
- `anthropic` package not installed (insight generation will skip)
- urllib3 SSL warning present but not blocking

## Key Code/Commands Reference
```bash
# Safe default (news only)
python3 main.py

# Discover candidates
python3 main.py --generate-candidates
python3 tools/list_candidates.py
python3 tools/approve_candidate.py "ProductName"

# Manual add
python3 tools/add_product.py "ProductName"
python3 tools/add_product.py --quick "Name" "https://url" "Desc" --category coding

# Legacy mode (use with caution!)
python3 main.py --legacy --no-db
```
