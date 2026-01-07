# Session: WeeklyAI Ranking + UI Refinement
Date: 2025-01-06
Duration: ~25 messages

## Context Snapshot
Adjusted ranking logic to reduce HuggingFace dominance, added company product ingestion, refined the white/blue UI, and provided log commands for crawler scheduling.

## What Was Accomplished
- Tuned Hot score to 50% momentum and normalized metrics per source to reduce source dominance.
- Added per‑source caps for Hot and Top 15 lists.
- Added company product ingestion pipeline (LG/TCL/ASUS placeholders) and data folder.
- Further refined the frontend UI with a stronger white/blue visual system and typography update.
- Documented log locations and commands for crawler/launchd.

## Key Decisions & Rationale
| Decision | Why | Alternatives Rejected |
|----------|-----|----------------------|
| Per‑source log normalization for metrics | Prevent HuggingFace from dominating due to massive downloads | Raw global log scale — still biased |
| Per‑source caps for ranking lists | Ensure list diversity and discoverability | Category‑only caps — still source skew |
| Company ingestion via local JSON | Avoid scraping/licensing issues; enables curated accuracy | Automated company crawling — brittle + legal risk |
| UI refinement with Lexend + crisp gradients | Improve legibility and visual hierarchy after UI regression | Keep prior typography — felt flat |

## Current State
- **Working**: Updated scoring pipeline; source normalization; company ingestion; refined UI.
- **Broken/Blocked**: Exhibition crawler still failing (needs log details and valid data with `status: active`).
- **Modified files**:
  - `crawler/main.py` — hot score mix, per‑source normalization, source stats.
  - `backend/app/services/product_service.py` — per‑source caps for Hot/Top lists.
  - `crawler/spiders/company_spider.py` — new company ingestion spider.
  - `crawler/data/companies/lg.json`
  - `crawler/data/companies/tcl.json`
  - `crawler/data/companies/asus.json`
  - `crawler/data/companies/README.md`
  - `crawler/spiders/__init__.py` — export CompanySpider.
  - `frontend/views/index.ejs` — font swap to Lexend.
  - `frontend/public/css/style.css` — major UI refinement.

## Dead Ends (Don't Retry)
- ❌ Exhibition crawler “failure” without logs — need exact error to fix.

## Next Steps (Prioritized)
1. [ ] Check crawler logs to find exhibition failure cause; verify JSON format + `status: active`.
2. [ ] Populate `crawler/data/companies/*.json` with real products and activate them.
3. [ ] Run crawler to regenerate scores with new normalization.

## Environment & Gotchas
- Exhibition/company ingestion only includes items with `status: active`/`published`/`live`.
- Logs are written to `crawler/logs/` when using the scheduling scripts.

## Key Code/Commands Reference
- Tail crawler log: `tail -n 200 crawler/logs/crawler.log`
- Tail launchd logs: `tail -n 200 crawler/logs/launchd.out.log` and `tail -n 200 crawler/logs/launchd.err.log`
- Run crawler once: `python3 crawler/main.py`
