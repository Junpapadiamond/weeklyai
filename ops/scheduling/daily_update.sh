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

# 1.10 Fix logos
echo "[$(date +%H:%M:%S)] Running fix_logos.py..." >> "$LOG_DIR/daily_update.log"
if $PYTHON_BIN crawler/tools/fix_logos.py --input data/products_featured.json >> "$LOG_DIR/daily_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] fix_logos.py completed successfully" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] fix_logos.py failed with exit code $?" >> "$LOG_DIR/daily_update.log"
fi

# 2. Update news (optional, continues even if auto_discover fails)
echo "[$(date +%H:%M:%S)] Running main.py --news-only..." >> "$LOG_DIR/daily_update.log"
if $PYTHON_BIN crawler/main.py --news-only >> "$LOG_DIR/daily_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] main.py --news-only completed successfully" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] main.py --news-only failed with exit code $?" >> "$LOG_DIR/daily_update.log"
fi

echo "=== WeeklyAI Daily Update Completed at $(date +"%Y-%m-%d %H:%M:%S") ===" >> "$LOG_DIR/daily_update.log"
echo "" >> "$LOG_DIR/daily_update.log"
