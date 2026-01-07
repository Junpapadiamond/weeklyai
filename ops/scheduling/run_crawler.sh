#!/bin/zsh
set -euo pipefail

REPO_DIR="/Users/jun/Desktop/WeeklyAI"
PYTHON_BIN="/usr/bin/python3"
INTERVAL_HOURS="${CRAWLER_INTERVAL_HOURS:-}"

cd "$REPO_DIR"

if [ "${1:-}" = "--interval-hours" ] && [ -n "${2:-}" ]; then
    INTERVAL_HOURS="$2"
fi

if [ -n "$INTERVAL_HOURS" ] && [ "$INTERVAL_HOURS" != "0" ]; then
    $PYTHON_BIN crawler/main.py --interval-hours "$INTERVAL_HOURS" >> "$REPO_DIR/crawler/logs/crawler.log" 2>&1
else
    $PYTHON_BIN crawler/main.py >> "$REPO_DIR/crawler/logs/crawler.log" 2>&1
fi
