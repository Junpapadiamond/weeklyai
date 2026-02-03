#!/bin/bash
# WeeklyAI News Update Script

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
echo "=== WeeklyAI News Update Started at $TIMESTAMP ===" >> "$LOG_DIR/news_update.log"

# Build arguments from env overrides
ARGS=""
if [ -n "${NEWS_HOURS:-}" ]; then
    ARGS="$ARGS --hours $NEWS_HOURS"
fi
if [ -n "${NEWS_SOURCES:-}" ]; then
    ARGS="$ARGS --sources $NEWS_SOURCES"
fi
if [ -n "${NEWS_LIMIT_RSS:-}" ]; then
    ARGS="$ARGS --limit-rss $NEWS_LIMIT_RSS"
fi
if [ -n "${NEWS_LIMIT_HN:-}" ]; then
    ARGS="$ARGS --limit-hn $NEWS_LIMIT_HN"
fi
if [ -n "${NEWS_LIMIT_REDDIT:-}" ]; then
    ARGS="$ARGS --limit-reddit $NEWS_LIMIT_REDDIT"
fi
if [ -n "${NEWS_LIMIT_X:-}" ]; then
    ARGS="$ARGS --limit-x $NEWS_LIMIT_X"
fi

echo "[$(date +%H:%M:%S)] Running news_discover.py $ARGS" >> "$LOG_DIR/news_update.log"
if $PYTHON_BIN crawler/tools/news_discover.py $ARGS >> "$LOG_DIR/news_update.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] news_discover.py completed successfully" >> "$LOG_DIR/news_update.log"
else
    echo "[$(date +%H:%M:%S)] news_discover.py failed with exit code $?" >> "$LOG_DIR/news_update.log"
fi

echo "=== WeeklyAI News Update Completed at $(date +"%Y-%m-%d %H:%M:%S") ===" >> "$LOG_DIR/news_update.log"
echo "" >> "$LOG_DIR/news_update.log"
