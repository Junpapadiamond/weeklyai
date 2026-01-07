# Session: WeeklyAI UI + Rankings + Exhibitions
Date: 2025-01-06
Duration: ~60 messages

## Context Snapshot
Updated the WeeklyAI frontend design and hero animation, generated GIF components, added algorithmic art, then implemented multi-factor ranking, exhibitions ingestion, and 12-hour scheduling.

## What Was Accomplished
- Refreshed frontend theme to a vital white/blue aesthetic with aligned layout grid and improved motion.
- Embedded a p5.js hero animation inspired by the Azure Tides art.
- Generated three matching GIF components (hero ambient, hot badge, loading shimmer).
- Implemented multi-factor scoring for Hot Recommend and Top 15 with category diversity.
- Added exhibition ingestion (CES/MWC/IFA/GTC) via local JSON files and status gating.
- Added 12-hour scheduling assets (launchd + cron) and crawler interval flag.

## Key Decisions & Rationale
| Decision | Why | Alternatives Rejected |
|----------|-----|----------------------|
| Use multi-factor scoring (momentum/recency/engagement/quality/volume) | Avoid download-only bias and create balanced ranking | Pure download ranking — too skewed |
| Hot score weights set to 50% momentum | User requested optimized mix with higher momentum emphasis | Lower momentum mix — less “hot” signal |
| Exhibition data from local JSON | Avoid network scraping constraints and licensing issues | Direct scraping of exhibitor sites — brittle and licensing risk |
| Hero art as p5.js overlay | Matches Azure Tides dynamics while keeping layout intact | Static image — less vitality |

## Current State
- **Working**: Vital white/blue theme, aligned layout grid, hero art animation, multi-factor rankings, exhibition ingestion, crawler interval scheduling.
- **Broken/Blocked**: None reported.
- **Modified files**:
  - `frontend/views/index.ejs` — updated fonts, hero art container, p5.js include.
  - `frontend/public/css/style.css` — new theme, alignment tokens, hero overlay, footer alignment.
  - `frontend/public/js/hero-art.js` — Azure Tides-inspired field with pressure + tidal cadence.
  - `frontend/public/gifs/weeklyai-hero-ambient.gif`
  - `frontend/public/gifs/weeklyai-hot-badge.gif`
  - `frontend/public/gifs/weeklyai-loading-shimmer.gif`
  - `frontend/public/art/azure-tides.md`
  - `frontend/public/art/azure-tides.html`
  - `crawler/main.py` — multi-factor scoring, hot/top scores, interval scheduling, exhibition spider integration.
  - `backend/app/services/product_service.py` — uses hot_score/top_score + diversity caps.
  - `crawler/database/db_handler.py` — hot/top sorting.
  - `crawler/spiders/exhibition_spider.py` — reads `crawler/data/exhibitions/*.json` with status gating.
  - `crawler/spiders/__init__.py` — exports new spiders.
  - `crawler/utils/image_utils.py` — logo overrides for LG/TCL/ASUS.
  - `crawler/data/exhibitions/ces.json` (pending placeholders)
  - `crawler/data/exhibitions/mwc.json`
  - `crawler/data/exhibitions/ifa.json`
  - `crawler/data/exhibitions/gtc.json`
  - `crawler/data/exhibitions/README.md`
  - `ops/scheduling/run_crawler.sh`
  - `ops/scheduling/com.weeklyai.crawler.plist`
  - `ops/scheduling/cron.txt`

## Dead Ends (Don't Retry)
- ❌ Running Playwright with downloaded Chromium initially timed out; used system Chrome instead.
- ❌ Starting Node server in sandbox failed with EPERM on 0.0.0.0; needed escalated permissions for local server.

## Next Steps (Prioritized)
1. [ ] Fill real CES/MWC/IFA/GTC product entries and set `status: "active"` in `crawler/data/exhibitions/*.json`.
2. [ ] Enable launchd or cron for 12-hour scheduling; verify logs in `crawler/logs/`.

## Environment & Gotchas
- Python 3.11 needed for GIF generation due to type hints in GIF builder.
- Playwright required Chrome channel on macOS; Chromium download was slow.
- Logo fetching uses Clearbit/Google favicon; confirm licensing for press-kit images.

## Key Code/Commands Reference
- Run crawler every 12 hours (loop): `python3 crawler/main.py --interval-hours 12`
- Enable launchd:
  - Copy plist: `cp ops/scheduling/com.weeklyai.crawler.plist ~/Library/LaunchAgents/`
  - Load: `launchctl load ~/Library/LaunchAgents/com.weeklyai.crawler.plist`
