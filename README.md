# WeeklyAI

> Global AI Product Discovery Platform for Product Managers

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/Node-18+-green.svg)](https://nodejs.org/)
[![GitHub](https://img.shields.io/badge/GitHub-Repo-black.svg)](https://github.com/your-username/WeeklyAI)

WeeklyAI is a product intelligence platform that continuously discovers, evaluates, and ranks high-potential AI startups and tools from multiple regions.

It helps PMs, operators, and investors quickly spot:
- **Dark Horses (4-5分)**: high potential + low exposure, priority recommendations
- **Rising Stars (2-3分)**: early-stage innovation with emerging signals
- **Industry Leaders**: known incumbents for context and benchmark

---

## ✨ Product Value

- **Global coverage**: US / China / Europe / Japan-Korea / SEA
- **Daily automated discovery**: multi-source discovery and AI scoring
- **Hardware-native signals**: special focus on emerging AI form factors
- **Actionable ranking**: one-click consumption on homepage and category pages
- **Dual data strategy**: MongoDB primary store + JSON fallback for stability

---

## 🧭 Platform Overview

### Current architecture

- **Frontend (active)**: `frontend-next/`
  - Next.js 16, React 19, TypeScript, Tailwind CSS, SWR
- **Backend**: `backend/`
  - Flask 3.0, PyMongo 4.6, REST API design
- **Crawler & pipeline**: `crawler/`
  - Perplexity + GLM provider routing
  - Data cleaning, dedup, enrichment, and publishing
- **Legacy frontend**: `frontend/` (Express + EJS)
  - Kept for compatibility only; no active development

---

## 🚀 Demo & API

- Base API: `http://localhost:5000/api/v1`
- Frontend (dev): `http://localhost:3001`

### Main endpoints

| Endpoint | Description |
| --- | --- |
| `/products/weekly-top` | Weekly Top 15 |
| `/products/dark-horses` | Dark Horses (4-5分) |
| `/products/rising-stars` | Rising Stars (2-3分) |
| `/products/trending` | Trending Top 5 |
| `/products/today` | Today Picks |
| `/products/<id>` | Product detail |
| `/products/<id>/related` | Related products |
| `/products/blogs` | News and blogs |
| `/products/categories` | Category list |
| `/products/industry-leaders` | Industry leader reference |
| `/search?q=xxx` | Search |

Full endpoint list is documented in source service layer and route handlers.

---

## 🛠️ Quick Start

### Requirements

- Python 3.9+
- Node.js 18+
- npm
- MongoDB (optional, fallback to JSON if unavailable)

### Install dependencies

```bash
git clone https://github.com/your-username/WeeklyAI.git
cd WeeklyAI

# backend
cd backend
python -m pip install -r requirements.txt

# frontend
cd ../frontend-next
npm install

# crawler
cd ../crawler
python -m pip install -r requirements.txt
```

### Environment setup

```bash
cp .env.example .env
cp crawler/.env.example crawler/.env
```

At minimum, configure one provider key:

- `PERPLEXITY_API_KEY` (Perplexity)
- `ZHIPU_API_KEY` (GLM)

---

## ▶️ Run the system

```bash
# backend
cd backend && python run.py

# frontend (next.js)
cd frontend-next && npm run dev
```

Expected:
- Backend: `http://localhost:5000`
- Frontend: `http://localhost:3001`

---

## 📆 Daily pipeline

Core update chain (`crawler/tools` + `ops/scheduling`):

1. `auto_discover.py --region all`
2. `auto_publish.py`
3. `backfill_source_urls.py`
4. `resolve_websites.py --aggressive`
5. `validate_websites.py`
6. `cleanup_unknowns_and_duplicates.py`
7. `fix_logos.py`
8. `main.py --news-only`
9. `rss_to_products.py --enrich-featured`
10. `sync_to_mongodb.py --all`

Default schedule is `3:00 AM` via launchd.  
Log file: `crawler/logs/daily_update.log`

Common manual commands:

```bash
cd crawler
python3 tools/auto_discover.py --region all
python3 tools/rss_to_products.py --sources youtube,x --enrich-featured --dry-run
python3 tools/sync_to_mongodb.py --all
```

---

## 📂 Key data files

- `crawler/data/products_featured.json` — main featured pool
- `crawler/data/dark_horses/week_*.json` — weekly dark horses
- `crawler/data/rising_stars/global_*.json` — weekly rising stars
- `crawler/data/blogs_news.json` — news stream
- `crawler/data/products_hot_search.json` — hot search terms
- `crawler/data/source_watchlists.json` — social sources
- `crawler/data/industry_leaders.json` — exclusion list
- `crawler/data/logo_cache.json` — logo cache

---

## ⚙️ Provider routing

- **cn** → GLM (`glm-4.7`, `search_pro` / `search_pro_quark` / `search_std`)
- **us / eu / jp / sea** → Perplexity (`sonar`)
- `USE_GLM_FOR_CN=false` falls back CN traffic to Perplexity

---

## ✅ Data quality rules

- Required fields: `name`, `website`, `description`, `why_matters`, `dark_horse_index`
- `website` must be valid `http/https` URL
- `description` length > 20 chars
- `why_matters` length > 30 chars with concrete evidence (numbers/differentiators)
- Dedup key: `_sync_key` (normalized domain)
- Exclude industry leaders in `crawler/data/industry_leaders.json`

---

## 📚 Environment variables

- `MONGO_URI`
- `PERPLEXITY_API_KEY`, `PERPLEXITY_MODEL` (default: `sonar`)
- `ZHIPU_API_KEY`, `GLM_MODEL` (default: `glm-4.7`), `GLM_SEARCH_ENGINE`
- `USE_GLM_FOR_CN`
- `CONTENT_YEAR` (default: `2026`)
- `SOCIAL_HOURS` (default: `96h`)
- `DARK_HORSE_FRESH_DAYS` (default: `5`)
- `DARK_HORSE_STICKY_DAYS` (default: `10`)

---

## 🤝 Contributing

1. Fork and create your branch
2. Keep changes scoped and include clear rationale in PR description
3. Follow module boundaries:  
   - backend logic in `backend/app/services`
   - crawler tools in `crawler/tools`
   - frontend features in `frontend-next/src`
4. Provide validation screenshots or API examples for UI/API changes

---

## 🔒 License

MIT
