#!/bin/zsh
set -euo pipefail

REPO_DIR="/Users/jun/Desktop/WeeklyAI"
PYTHON_BIN="/usr/bin/python3"
INTERVAL_HOURS="${CRAWLER_INTERVAL_HOURS:-}"
ENABLE_SLACK="${ENABLE_SLACK_NOTIFICATIONS:-true}"

cd "$REPO_DIR"

# Load environment variables from .env if exists
if [ -f "$REPO_DIR/.env" ]; then
    export $(grep -v '^#' "$REPO_DIR/.env" | xargs)
fi

# Build arguments
ARGS=""

if [ "${1:-}" = "--interval-hours" ] && [ -n "${2:-}" ]; then
    ARGS="$ARGS --interval-hours $2"
fi

# Add Slack flag if enabled and webhook is configured
if [ "$ENABLE_SLACK" = "true" ] && [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    ARGS="$ARGS --slack --slack-top 10"
fi

# Create logs directory if not exists
mkdir -p "$REPO_DIR/crawler/logs"

# Run crawler
$PYTHON_BIN crawler/main.py $ARGS >> "$REPO_DIR/crawler/logs/crawler.log" 2>&1
