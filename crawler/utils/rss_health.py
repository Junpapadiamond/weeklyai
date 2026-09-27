"""Distinguish real feeds, stale feeds and HTML security/error pages."""
import calendar
from datetime import datetime, timedelta, timezone

import feedparser


def inspect_feed(data, now, days):
    parsed = feedparser.parse(data)
    dates = []
    for entry in parsed.entries:
        date = entry.get("published_parsed") or entry.get("updated_parsed")
        if date:
            try:
                dates.append(datetime.fromtimestamp(calendar.timegm(date), timezone.utc))
            except (ValueError, OverflowError, OSError):
                pass
    latest = max(dates) if dates else None
    if not parsed.get("version"):
        content = (data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data).lower()
        blocked = any(word in content for word in ("security checkpoint", "安全检测", "captcha", "verify you are human"))
        status = "blocked" if blocked else "not_feed"
    elif not parsed.entries:
        status = "empty"
    elif not dates:
        status = "undated"
    elif latest < now - timedelta(days=days):
        status = "stale"
    elif not any(now - timedelta(days=days) <= date <= now for date in dates):
        status = "future_dated"
    else:
        status = "ok"
    return parsed, {"status": status, "entries": len(parsed.entries),
                    "latest_published_at": latest.isoformat() if latest else None}
