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

# 1.5 Editorial gate notification (v2: no auto-publish)
if [ -f "$REPO_DIR/crawler/data/candidates/pending_review.json" ]; then
    CANDIDATE_COUNT=$($PYTHON_BIN -c "import json; p='$REPO_DIR/crawler/data/candidates/pending_review.json'; data=json.load(open(p, encoding='utf-8')); print(len(data) if isinstance(data, list) else 0)" 2>/dev/null || echo 0)
else
    CANDIDATE_COUNT=0
fi
echo "[$(date +%H:%M:%S)] $CANDIDATE_COUNT new candidates ready — run python3 crawler/tools/curate.py" >> "$LOG_DIR/daily_update.log"

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
if $PYTHON_BIN crawler/tools/validate_websites.py --scope provider --aggressive >> "$LOG_DIR/daily_update.log" 2>&1; then
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

# 1.10 Fix logos
echo "[$(date +%H:%M:%S)] Running fix_logos.py..." >> "$LOG_DIR/daily_update.log"
if $PYTHON_BIN crawler/tools/fix_logos.py --input data/products_featured.json >> "$LOG_DIR/daily_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] fix_logos.py completed successfully" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] fix_logos.py failed with exit code $?" >> "$LOG_DIR/daily_update.log"
fi

# 1.11 Generate experience config for new products (breakdown + Try it now)
echo "[$(date +%H:%M:%S)] Running generate_experience.py --new-only..." >> "$LOG_DIR/daily_update.log"
if $PYTHON_BIN crawler/tools/generate_experience.py --new-only >> "$LOG_DIR/daily_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] generate_experience.py completed successfully" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] generate_experience.py failed with exit code $? (non-fatal)" >> "$LOG_DIR/daily_update.log"
fi

# 2. Update news (optional, continues even if auto_discover fails)
echo "[$(date +%H:%M:%S)] Running main.py --news-only..." >> "$LOG_DIR/daily_update.log"
if $PYTHON_BIN crawler/main.py --news-only >> "$LOG_DIR/daily_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] main.py --news-only completed successfully" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] main.py --news-only failed with exit code $?" >> "$LOG_DIR/daily_update.log"
fi

# 2.5 CN-native news补偿（RSS）
echo "[$(date +%H:%M:%S)] Running cn_news_only.py..." >> "$LOG_DIR/daily_update.log"
if $PYTHON_BIN crawler/tools/cn_news_only.py >> "$LOG_DIR/daily_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] cn_news_only.py completed successfully" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] cn_news_only.py failed with exit code $?" >> "$LOG_DIR/daily_update.log"
fi

# 2.6 CN-native news补偿（GLM）
echo "[$(date +%H:%M:%S)] Running cn_news_glm.py..." >> "$LOG_DIR/daily_update.log"
if $PYTHON_BIN crawler/tools/cn_news_glm.py >> "$LOG_DIR/daily_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] cn_news_glm.py completed successfully" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] cn_news_glm.py failed with exit code $?" >> "$LOG_DIR/daily_update.log"
fi

# 3. Social + CN signals → candidates / enrich featured
echo "[$(date +%H:%M:%S)] Running rss_to_products.py (sources=youtube,x,cn_news,cn_news_glm)..." >> "$LOG_DIR/daily_update.log"
if $PYTHON_BIN crawler/tools/rss_to_products.py --input crawler/data/blogs_news.json --sources youtube,x,cn_news,cn_news_glm --enrich-featured >> "$LOG_DIR/daily_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] rss_to_products.py completed successfully" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] rss_to_products.py failed with exit code $?" >> "$LOG_DIR/daily_update.log"
fi

# 3.4 Normalize zh primary fields (products + blogs) before EN backfill
echo "[$(date +%H:%M:%S)] Running backfill_primary_zh_fields.py..." >> "$LOG_DIR/daily_update.log"
if $PYTHON_BIN crawler/tools/backfill_primary_zh_fields.py --targets products,blogs --provider auto --batch-size 8 --residual-limit 8 >> "$LOG_DIR/daily_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] backfill_primary_zh_fields.py completed successfully" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] backfill_primary_zh_fields.py failed with exit code $?" >> "$LOG_DIR/daily_update.log"
fi

# 3.5 Backfill English fields after zh normalization
echo "[$(date +%H:%M:%S)] Running backfill_product_en_fields.py..." >> "$LOG_DIR/daily_update.log"
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
