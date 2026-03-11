#!/bin/bash
# WeeklyAI Daily Update Script
# Runs AI global search and news updates daily

REPO_DIR="/Users/jun/Desktop/Projects/WeeklyAI"
PYTHON_BIN="/usr/bin/python3"
LOG_DIR="$REPO_DIR/crawler/logs"
REPORT_DIR="$LOG_DIR/reports"
OPENCLAW_DIR="$REPO_DIR/ops/openclaw"

cd "$REPO_DIR"

# Create logs directory if not exists
mkdir -p "$LOG_DIR"
mkdir -p "$REPORT_DIR"

# Load environment variables from .env if exists
if [ -f "$REPO_DIR/.env" ]; then
    export $(grep -v '^#' "$REPO_DIR/.env" | xargs)
fi

utc_now() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

log_line() {
    echo "[$(date +%H:%M:%S)] $1" >> "$LOG_DIR/daily_update.log"
}

append_step_event() {
    # step_id, name, required, status, exit_code, duration_seconds, started_at, finished_at
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" >> "$STEP_EVENTS_FILE"
}

run_step() {
    local step_id="$1"
    local step_name="$2"
    local required="$3"
    shift 3

    local started_epoch
    local finished_epoch
    local duration
    local started_at
    local finished_at
    local status

    started_epoch=$(date +%s)
    started_at=$(utc_now)
    log_line "Running ${step_name}..."

    "$@" >> "$LOG_DIR/daily_update.log" 2>&1
    LAST_STEP_EXIT_CODE=$?

    finished_epoch=$(date +%s)
    finished_at=$(utc_now)
    duration=$((finished_epoch - started_epoch))

    if [ "$LAST_STEP_EXIT_CODE" -eq 0 ]; then
        status="success"
        log_line "${step_name} completed successfully"
    else
        status="failed"
        log_line "${step_name} failed with exit code ${LAST_STEP_EXIT_CODE}"
    fi

    append_step_event "$step_id" "$step_name" "$required" "$status" "$LAST_STEP_EXIT_CODE" "$duration" "$started_at" "$finished_at"
    return 0
}

RUN_ID="daily_$(date +%Y%m%d_%H%M%S)_$$"
RUN_STARTED_AT_UTC=$(utc_now)
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
STEP_EVENTS_FILE="$REPORT_DIR/openclaw_steps_${RUN_ID}.tsv"
RUN_SUMMARY_FILE="$REPORT_DIR/openclaw_summary_${RUN_ID}.json"
LAST_STEP_EXIT_CODE=0
WEBSITE_REPORT="$REPORT_DIR/website_validation_$(date +%Y%m%d_%H%M%S).json"

echo "=== WeeklyAI Daily Update Started at $TIMESTAMP ===" >> "$LOG_DIR/daily_update.log"
log_line "Run ID: ${RUN_ID}"

# 1. AI Global Search (main task)
run_step "auto_discover" "auto_discover.py --region all" "true" \
    "$PYTHON_BIN" crawler/tools/auto_discover.py --region all

# 1.5 Auto publish to products_featured.json
run_step "auto_publish" "auto_publish.py" "true" \
    "$PYTHON_BIN" crawler/tools/auto_publish.py

# 1.6 Backfill source_url into featured (from weekly files)
run_step "backfill_source_urls" "backfill_source_urls.py" "true" \
    "$PYTHON_BIN" crawler/tools/backfill_source_urls.py

# 1.7 Resolve missing websites from source_url (aggressive mode)
run_step "resolve_websites" "resolve_websites.py --aggressive" "true" \
    "$PYTHON_BIN" crawler/tools/resolve_websites.py --input crawler/data/products_featured.json --aggressive

# 1.8 Validate auto-resolved websites (avoid wrong domains)
run_step "validate_websites" "validate_websites.py --scope provider --aggressive" "true" \
    "$PYTHON_BIN" crawler/tools/validate_websites.py --scope provider --aggressive --report "$WEBSITE_REPORT"
if [ "$LAST_STEP_EXIT_CODE" -eq 0 ]; then
    log_line "website validation report: $WEBSITE_REPORT"
fi

# 1.9 Remove unknown websites + duplicates
run_step "cleanup_unknowns_and_duplicates" "cleanup_unknowns_and_duplicates.py" "true" \
    "$PYTHON_BIN" crawler/tools/cleanup_unknowns_and_duplicates.py

# 1.10 Fix logos
run_step "fix_logos" "fix_logos.py" "true" \
    "$PYTHON_BIN" crawler/tools/fix_logos.py --input data/products_featured.json

# 2. Update news (optional, continues even if auto_discover fails)
run_step "news_only" "main.py --news-only" "false" \
    "$PYTHON_BIN" crawler/main.py --news-only

# 3. Social signals → candidates / enrich featured
run_step "rss_to_products" "rss_to_products.py (sources=youtube,x)" "true" \
    "$PYTHON_BIN" crawler/tools/rss_to_products.py --input crawler/data/blogs_news.json --sources youtube,x --enrich-featured

# 3.5 Backfill English fields before Mongo sync
run_step "backfill_product_en_fields" "backfill_product_en_fields.py" "true" \
    "$PYTHON_BIN" crawler/tools/backfill_product_en_fields.py --provider auto --only-missing --batch-size 8

# 4. Sync to MongoDB (when MONGO_URI is configured)
if [ -n "${MONGO_URI:-}" ]; then
    run_step "sync_to_mongodb" "sync_to_mongodb.py --all" "true" \
        "$PYTHON_BIN" crawler/tools/sync_to_mongodb.py --all
else
    log_line "MONGO_URI not set, skipping MongoDB sync"
    now_utc=$(utc_now)
    append_step_event "sync_to_mongodb" "sync_to_mongodb.py --all" "false" "skipped" "0" "0" "$now_utc" "$now_utc"
fi

RUN_FINISHED_AT_UTC=$(utc_now)

# Build OpenClaw run summary
SUMMARY_CMD=(
    "$PYTHON_BIN" "$OPENCLAW_DIR/run_summary.py"
    --run-id "$RUN_ID"
    --started-at "$RUN_STARTED_AT_UTC"
    --finished-at "$RUN_FINISHED_AT_UTC"
    --events-file "$STEP_EVENTS_FILE"
    --output "$RUN_SUMMARY_FILE"
    --report-path "$LOG_DIR/daily_update.log"
    --report-path "$LOG_DIR/launchd.out.log"
    --report-path "$LOG_DIR/launchd.err.log"
)
if [ -n "$WEBSITE_REPORT" ]; then
    SUMMARY_CMD+=(--report-path "$WEBSITE_REPORT")
fi

if "${SUMMARY_CMD[@]}" >> "$LOG_DIR/daily_update.log" 2>&1; then
    log_line "OpenClaw summary generated: $RUN_SUMMARY_FILE"
else
    log_line "OpenClaw summary generation failed with exit code $?"
fi

# Notify OpenClaw (never blocks the pipeline completion)
if [ -f "$RUN_SUMMARY_FILE" ]; then
    if "$PYTHON_BIN" "$OPENCLAW_DIR/openclaw_notify.py" --summary-file "$RUN_SUMMARY_FILE" >> "$LOG_DIR/daily_update.log" 2>&1; then
        log_line "OpenClaw webhook notify completed successfully"
    else
        log_line "OpenClaw webhook notify failed with exit code $?"
    fi
else
    log_line "OpenClaw webhook notify skipped because summary file is missing"
fi

echo "=== WeeklyAI Daily Update Completed at $(date +"%Y-%m-%d %H:%M:%S") ===" >> "$LOG_DIR/daily_update.log"
echo "" >> "$LOG_DIR/daily_update.log"
