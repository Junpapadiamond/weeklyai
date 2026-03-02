#!/bin/bash
# WeeklyAI Daily Update Script
# Runs AI global search and news updates daily

REPO_DIR="/Users/jun/Desktop/Projects/WeeklyAI"
PYTHON_BIN="/usr/bin/python3"
LOG_DIR="$REPO_DIR/crawler/logs"

cd "$REPO_DIR"

# Create logs directory if not exists
mkdir -p "$LOG_DIR"

# Load environment variables from .env if exists
if [ -f "$REPO_DIR/.env" ]; then
    export $(grep -v '^#' "$REPO_DIR/.env" | xargs)
fi

TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "=== WeeklyAI Daily Update Started at $TIMESTAMP ===" >> "$LOG_DIR/daily_update.log"

# 1. AI Global Search (main task)
echo "[$(date +%H:%M:%S)] Running auto_discover.py --region all..." >> "$LOG_DIR/daily_update.log"
if $PYTHON_BIN crawler/tools/auto_discover.py --region all >> "$LOG_DIR/daily_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] auto_discover.py completed successfully" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] auto_discover.py failed with exit code $?" >> "$LOG_DIR/daily_update.log"
fi

# 1.5 Auto publish to products_featured.json
echo "[$(date +%H:%M:%S)] Running auto_publish.py..." >> "$LOG_DIR/daily_update.log"
if $PYTHON_BIN crawler/tools/auto_publish.py >> "$LOG_DIR/daily_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] auto_publish.py completed successfully" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] auto_publish.py failed with exit code $?" >> "$LOG_DIR/daily_update.log"
fi

# 1.6 Backfill source_url into featured (from weekly files)
echo "[$(date +%H:%M:%S)] Running backfill_source_urls.py..." >> "$LOG_DIR/daily_update.log"
if $PYTHON_BIN crawler/tools/backfill_source_urls.py >> "$LOG_DIR/daily_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] backfill_source_urls.py completed successfully" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] backfill_source_urls.py failed with exit code $?" >> "$LOG_DIR/daily_update.log"
fi

# 1.7 Resolve missing websites from source_url (aggressive mode)
echo "[$(date +%H:%M:%S)] Running resolve_websites.py..." >> "$LOG_DIR/daily_update.log"
if $PYTHON_BIN crawler/tools/resolve_websites.py --input crawler/data/products_featured.json --aggressive >> "$LOG_DIR/daily_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] resolve_websites.py completed successfully" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] resolve_websites.py failed with exit code $?" >> "$LOG_DIR/daily_update.log"
fi

# 1.8 Validate auto-resolved websites (avoid wrong domains)
echo "[$(date +%H:%M:%S)] Running validate_websites.py..." >> "$LOG_DIR/daily_update.log"
if $PYTHON_BIN crawler/tools/validate_websites.py >> "$LOG_DIR/daily_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] validate_websites.py completed successfully" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] validate_websites.py failed with exit code $?" >> "$LOG_DIR/daily_update.log"
fi

# 1.9 Remove unknown websites + duplicates
echo "[$(date +%H:%M:%S)] Running cleanup_unknowns_and_duplicates.py..." >> "$LOG_DIR/daily_update.log"
if $PYTHON_BIN crawler/tools/cleanup_unknowns_and_duplicates.py >> "$LOG_DIR/daily_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] cleanup_unknowns_and_duplicates.py completed successfully" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] cleanup_unknowns_and_duplicates.py failed with exit code $?" >> "$LOG_DIR/daily_update.log"
fi

# 1.10 Build stable logo assets
echo "[$(date +%H:%M:%S)] Running build_logo_assets.py --mode incremental..." >> "$LOG_DIR/daily_update.log"
if $PYTHON_BIN crawler/tools/build_logo_assets.py --mode incremental >> "$LOG_DIR/daily_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] build_logo_assets.py completed successfully" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] build_logo_assets.py failed with exit code $?" >> "$LOG_DIR/daily_update.log"
fi

# 2-3. Social signals pipeline with delayed retry
SOCIAL_HEALTH_FILE="$REPO_DIR/crawler/data/social_source_health.json"
SOCIAL_RETRY_DELAY_SECONDS="${SOCIAL_RETRY_DELAY_SECONDS:-1200}"
SOCIAL_MIN_SIGNALS="${SOCIAL_MIN_SIGNALS:-1}"

run_social_pipeline_attempt() {
    local attempt_label="$1"
    echo "[$(date +%H:%M:%S)] [$attempt_label] Running main.py --news-only..." >> "$LOG_DIR/daily_update.log"
    if $PYTHON_BIN crawler/main.py --news-only >> "$LOG_DIR/daily_update.log" 2>&1; then
        echo "[$(date +%H:%M:%S)] [$attempt_label] main.py --news-only completed successfully" >> "$LOG_DIR/daily_update.log"
    else
        echo "[$(date +%H:%M:%S)] [$attempt_label] main.py --news-only failed with exit code $?" >> "$LOG_DIR/daily_update.log"
    fi

    echo "[$(date +%H:%M:%S)] [$attempt_label] Running rss_to_products.py (sources=youtube,x)..." >> "$LOG_DIR/daily_update.log"
    if $PYTHON_BIN crawler/tools/rss_to_products.py --input crawler/data/blogs_news.json --sources youtube,x --enrich-featured >> "$LOG_DIR/daily_update.log" 2>&1; then
        echo "[$(date +%H:%M:%S)] [$attempt_label] rss_to_products.py completed successfully" >> "$LOG_DIR/daily_update.log"
    else
        echo "[$(date +%H:%M:%S)] [$attempt_label] rss_to_products.py failed with exit code $?" >> "$LOG_DIR/daily_update.log"
    fi

    echo "[$(date +%H:%M:%S)] [$attempt_label] Running check_social_sources.py..." >> "$LOG_DIR/daily_update.log"
    if $PYTHON_BIN crawler/tools/check_social_sources.py --write-health >> "$LOG_DIR/daily_update.log" 2>&1; then
        echo "[$(date +%H:%M:%S)] [$attempt_label] check_social_sources.py completed successfully" >> "$LOG_DIR/daily_update.log"
    else
        echo "[$(date +%H:%M:%S)] [$attempt_label] check_social_sources.py failed with exit code $?" >> "$LOG_DIR/daily_update.log"
    fi

    SOCIAL_SIGNAL_TOTAL=$($PYTHON_BIN - <<PY
import json
from pathlib import Path
path = Path("$SOCIAL_HEALTH_FILE")
if not path.exists():
    print(0)
    raise SystemExit
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    print(0)
    raise SystemExit
sources = data.get("sources") if isinstance(data, dict) else {}
youtube = (sources.get("youtube") or {}).get("count", 0) if isinstance(sources, dict) else 0
x = (sources.get("x") or {}).get("count", 0) if isinstance(sources, dict) else 0
try:
    y = int(youtube or 0)
except Exception:
    y = 0
try:
    xx = int(x or 0)
except Exception:
    xx = 0
print(max(0, y) + max(0, xx))
PY
)
    echo "[$(date +%H:%M:%S)] [$attempt_label] social signals (youtube+x) = ${SOCIAL_SIGNAL_TOTAL}" >> "$LOG_DIR/daily_update.log"

    if [ "${SOCIAL_SIGNAL_TOTAL}" -ge "${SOCIAL_MIN_SIGNALS}" ]; then
        return 0
    fi
    return 1
}

if run_social_pipeline_attempt "attempt-1"; then
    echo "[$(date +%H:%M:%S)] Social pipeline succeeded on attempt-1" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] Social pipeline low-signal (${SOCIAL_SIGNAL_TOTAL} < ${SOCIAL_MIN_SIGNALS}), retry after ${SOCIAL_RETRY_DELAY_SECONDS}s" >> "$LOG_DIR/daily_update.log"
    sleep "$SOCIAL_RETRY_DELAY_SECONDS"
    if run_social_pipeline_attempt "attempt-2"; then
        echo "[$(date +%H:%M:%S)] Social pipeline recovered on attempt-2" >> "$LOG_DIR/daily_update.log"
    else
        echo "[$(date +%H:%M:%S)] Social pipeline still low after retry; actionable summary:" >> "$LOG_DIR/daily_update.log"
        $PYTHON_BIN - <<PY >> "$LOG_DIR/daily_update.log" 2>&1
import json
from pathlib import Path
path = Path("$SOCIAL_HEALTH_FILE")
if not path.exists():
    print("  - social health file missing")
    raise SystemExit
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception as exc:
    print(f"  - failed to read social health: {exc}")
    raise SystemExit
sources = data.get("sources") if isinstance(data, dict) else {}
for key in ("youtube", "x", "reddit"):
    item = sources.get(key) if isinstance(sources, dict) else None
    if not isinstance(item, dict):
        continue
    print(f"  - {key}: count={item.get('count', 0)}, errors={item.get('errors', {})}")
diag = sources.get("diagnostics") if isinstance(sources, dict) else None
if isinstance(diag, dict):
    for key in ("youtube", "x", "reddit"):
        recs = ((diag.get(key) or {}).get("recommendations") or []) if isinstance(diag.get(key), dict) else []
        if recs:
            print(f"    recommendations[{key}]={recs}")
PY
    fi
fi

# 3.5 Backfill localized fields before Mongo sync (*_en + Japanese *_zh)
echo "[$(date +%H:%M:%S)] Running backfill_product_en_fields.py (en+zh)..." >> "$LOG_DIR/daily_update.log"
if $PYTHON_BIN crawler/tools/backfill_product_en_fields.py --provider auto --only-missing --batch-size 8 >> "$LOG_DIR/daily_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] backfill_product_en_fields.py completed successfully" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] backfill_product_en_fields.py failed with exit code $?" >> "$LOG_DIR/daily_update.log"
fi

# 4. Sync to MongoDB (when MONGO_URI is configured)
if [ -n "$MONGO_URI" ]; then
    echo "[$(date +%H:%M:%S)] Running sync_to_mongodb.py --all..." >> "$LOG_DIR/daily_update.log"
    if $PYTHON_BIN crawler/tools/sync_to_mongodb.py --all >> "$LOG_DIR/daily_update.log" 2>&1; then
        echo "[$(date +%H:%M:%S)] sync_to_mongodb.py completed successfully" >> "$LOG_DIR/daily_update.log"
    else
        echo "[$(date +%H:%M:%S)] sync_to_mongodb.py failed with exit code $?" >> "$LOG_DIR/daily_update.log"
    fi
else
    echo "[$(date +%H:%M:%S)] MONGO_URI not set, skipping MongoDB sync" >> "$LOG_DIR/daily_update.log"
fi

echo "=== WeeklyAI Daily Update Completed at $(date +"%Y-%m-%d %H:%M:%S") ===" >> "$LOG_DIR/daily_update.log"
echo "" >> "$LOG_DIR/daily_update.log"
