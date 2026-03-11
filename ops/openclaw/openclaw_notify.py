#!/usr/bin/env python3
"""Send daily update summary payload to an OpenClaw webhook."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def read_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send OpenClaw webhook notification.")
    parser.add_argument("--summary-file", required=True, help="Path to run summary JSON.")
    parser.add_argument(
        "--webhook-url",
        default=os.getenv("OPENCLAW_WEBHOOK_URL", ""),
        help="OpenClaw webhook URL (defaults to OPENCLAW_WEBHOOK_URL).",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("OPENCLAW_WEBHOOK_TOKEN", ""),
        help="Webhook bearer token (defaults to OPENCLAW_WEBHOOK_TOKEN).",
    )
    parser.add_argument(
        "--event-type",
        default="weeklyai.daily_update",
        help="Event type field for the webhook envelope.",
    )
    parser.add_argument(
        "--source",
        default="weeklyai.daily_update.sh",
        help="Source field for the webhook envelope.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("OPENCLAW_WEBHOOK_TIMEOUT", "10")),
        help="HTTP timeout in seconds.",
    )
    return parser.parse_args()


def load_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def send_webhook(
    *,
    webhook_url: str,
    token: str,
    envelope: dict[str, Any],
    timeout: float,
) -> tuple[int, str]:
    payload = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(
        webhook_url,
        data=payload,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")
        return response.status, body


def main() -> int:
    if not read_bool_env("OPENCLAW_NOTIFY_ENABLED", default=False):
        print("[openclaw] notify disabled (OPENCLAW_NOTIFY_ENABLED is false)")
        return 0

    args = parse_args()
    if not args.webhook_url:
        print("[openclaw] OPENCLAW_WEBHOOK_URL is empty, skipping notify")
        return 0

    summary_path = Path(args.summary_file)
    if not summary_path.exists():
        print(f"[openclaw] summary file not found: {summary_path}")
        return 2

    summary = load_summary(summary_path)
    envelope = {
        "event_type": args.event_type,
        "source": args.source,
        "sent_at": datetime.now(UTC).isoformat(),
        "payload": summary,
    }

    try:
        status, body = send_webhook(
            webhook_url=args.webhook_url,
            token=args.token,
            envelope=envelope,
            timeout=args.timeout,
        )
    except urllib.error.HTTPError as error:
        print(f"[openclaw] webhook HTTP error: {error.code} {error.reason}")
        return 3
    except urllib.error.URLError as error:
        print(f"[openclaw] webhook URL error: {error.reason}")
        return 4
    except Exception as error:  # pragma: no cover - defensive
        print(f"[openclaw] webhook unknown error: {error}")
        return 5

    print(f"[openclaw] webhook sent: status={status}, run_id={summary.get('run_id')}")
    if body.strip():
        print(f"[openclaw] webhook response: {body[:500]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
