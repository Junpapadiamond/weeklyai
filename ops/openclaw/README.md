# OpenClaw Enhancement Layer (POC)

This folder contains the integration layer that augments the existing
`launchd + daily_update.sh` pipeline without replacing it.

## What is implemented

- `run_summary.py`: parse step events into normalized JSON payload.
- `openclaw_notify.py`: send run summary to OpenClaw webhook.
- `safe_rerun.py`: rerun approved commands only (no arbitrary shell).

## Payload contract

`run_summary.py` writes a JSON payload with stable fields:

- `run_id`
- `started_at`
- `finished_at`
- `overall_status`
- `steps[]`
- `report_paths[]`
- `error_summary`

## Environment variables

- `OPENCLAW_NOTIFY_ENABLED=true|false`
- `OPENCLAW_WEBHOOK_URL=https://...`
- `OPENCLAW_WEBHOOK_TOKEN=...`
- `OPENCLAW_WEBHOOK_TIMEOUT=10` (optional)
- `OPENCLAW_ACTOR=...` (used by `safe_rerun.py` audit logs)

## OpenClaw-side baseline (example)

1. Keep your current 3:00 AM launchd schedule as the source of truth.
2. Use OpenClaw cron only for health checks/monitoring loops.
3. Use hooks to route `command:new` and `command:failed` to your ops channel.
4. Start with minimal tool permissions (`tools.profile=messaging`) and expose
   only webhook/notification + safe rerun entrypoints.

See:

- `cron_jobs.example.json`
- `hooks.example.json`
- `tools_profile.example.toml`

## Manual commands

```bash
# Build summary from a step events file
python3 ops/openclaw/run_summary.py \
  --run-id demo_run \
  --started-at 2026-03-11T03:00:00Z \
  --finished-at 2026-03-11T03:30:00Z \
  --events-file crawler/logs/reports/openclaw_steps_demo.tsv \
  --output crawler/logs/reports/openclaw_summary_demo.json \
  --report-path crawler/logs/daily_update.log

# Notify OpenClaw with existing summary
OPENCLAW_NOTIFY_ENABLED=true \
OPENCLAW_WEBHOOK_URL=https://example.com/hook \
python3 ops/openclaw/openclaw_notify.py \
  --summary-file crawler/logs/reports/openclaw_summary_demo.json

# Allowed rerun command preview
python3 ops/openclaw/safe_rerun.py --list
python3 ops/openclaw/safe_rerun.py rss_to_products --dry-run
```
