#!/bin/zsh
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

# 2. Update news (optional, continues even if auto_discover fails)
echo "[$(date +%H:%M:%S)] Running main.py --news-only..." >> "$LOG_DIR/daily_update.log"
if $PYTHON_BIN crawler/main.py --news-only >> "$LOG_DIR/daily_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] main.py --news-only completed successfully" >> "$LOG_DIR/daily_update.log"
else
    echo "[$(date +%H:%M:%S)] main.py --news-only failed with exit code $?" >> "$LOG_DIR/daily_update.log"
fi

echo "=== WeeklyAI Daily Update Completed at $(date +"%Y-%m-%d %H:%M:%S") ===" >> "$LOG_DIR/daily_update.log"
echo "" >> "$LOG_DIR/daily_update.log"
