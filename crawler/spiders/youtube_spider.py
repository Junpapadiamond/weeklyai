"""
YouTube signals spider.

Goal: Collect high-signal AI product mentions from YouTube channel RSS feeds.
Output items are treated as "blog/news" (source="youtube") and later classified
into blogs_news.json by tools/data_classifier.py.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

from .base_spider import BaseSpider
from utils.social_sources import load_youtube_channel_ids_with_source


AI_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "machine learning",
    "ml",
    "llm",
    "gpt",
    "agent",
    "rag",
    "diffusion",
    "transformer",
    "openai",
    "anthropic",
    "claude",
    "gemini",
    "copilot",
]

SIGNAL_KEYWORDS = [
    "introducing",
    "launch",
    "launched",
    "release",
    "released",
    "announcing",
    "announce",
    "unveil",
    "unveiled",
    "demo",
    "open source",
    "funding",
    "raises",
    "raised",
    "seed",
    "series a",
    "series b",
    "beta",
    "update",
    "v2",
    "v3",
    "v4",
]

OPEN_SOURCE_PHRASES = [
    "open source",
    "open-source",
    "open sourced",
    "open-sourced",
    "开源",
]


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _to_iso(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _parse_feed_datetime(entry: Any) -> Optional[datetime]:
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if parsed:
        try:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
        except Exception:
            pass

    value = entry.get("published") or entry.get("updated")
    if not value:
        return None

    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.astimezone(timezone.utc)
        except Exception:
            continue
    return None


def _extract_video_id(url: str) -> str:
    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query or "")
        vid = (qs.get("v") or [""])[0]
        return vid
    except Exception:
        return ""


def _infer_categories(text: str) -> List[str]:
    lower = (text or "").lower()
    mapping = {
        "agent": ["agent", "autonomous", "assistant"],
        "coding": ["code", "coding", "developer", "ide", "github"],
        "image": ["image", "vision", "diffusion", "midjourney", "stable diffusion"],
        "video": ["video", "sora", "runway", "pika"],
        "voice": ["voice", "audio", "speech", "tts"],
        "hardware": ["robot", "chip", "hardware", "device", "wearable", "glasses"],
        "writing": ["writing", "text", "document", "copy"],
    }
    categories: List[str] = []
    for cat, kws in mapping.items():
        if any(k in lower for k in kws):
            categories.append(cat)
    return categories or ["other"]


class YouTubeSpider(BaseSpider):
    """Collect AI signals from YouTube channel RSS feeds."""

    def __init__(self):
        super().__init__()
        self.session.headers.update({
            "Accept": "application/atom+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
        })

    def crawl(self) -> List[Dict[str, Any]]:
        if not HAS_FEEDPARSER:
            print("  [YouTube] feedparser not installed, skipping")
            return []

        channel_ids, channel_source = self._get_channel_ids_with_source()
        if not channel_ids:
            print("  [YouTube] No channel ids configured, skipping")
            print("    remediation: set YOUTUBE_CHANNEL_IDS in .env or add youtube_channel_ids to crawler/data/source_watchlists.json")
            return []

        try:
            allowed_year = int(os.getenv("CONTENT_YEAR", str(datetime.now(timezone.utc).year)))
        except Exception:
            allowed_year = datetime.now(timezone.utc).year

        hours = int(os.getenv("SOCIAL_HOURS", "96"))
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        items: List[Dict[str, Any]] = []
        seen_urls = set()

        print(f"  [YouTube] Collecting signals from {len(channel_ids)} channels (last {hours}h, source={channel_source})...")

        for channel_id in channel_ids[:50]:
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            channel_items = self._fetch_channel(feed_url, cutoff=cutoff, allowed_year=allowed_year)
            for item in channel_items:
                url = item.get("website") or ""
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                items.append(item)

        print(f"  [YouTube] Collected {len(items)} items")
        return items[:60]

    @staticmethod
    def _get_text_window() -> int:
        """How many chars of the video description to use for keyword filtering."""
        try:
            return max(200, min(4000, int(os.getenv("SOCIAL_TEXT_WINDOW", "800"))))
        except Exception:
            return 800

    @staticmethod
    def _get_signal_window(ai_window: int) -> int:
        """Signal keywords should match early (title + first 300–500 chars)."""
        try:
            requested = int(os.getenv("SOCIAL_SIGNAL_WINDOW", "500"))
        except Exception:
            requested = 500
        return min(ai_window, max(200, min(800, requested)))

    @staticmethod
    def _get_channel_ids_with_source() -> tuple[List[str], str]:
        return load_youtube_channel_ids_with_source()

    def _fetch_channel(self, feed_url: str, cutoff: datetime, allowed_year: int) -> List[Dict[str, Any]]:
        try:
            resp = self.session.get(feed_url, timeout=20)
            resp.raise_for_status()
        except Exception as exc:
            print(f"    ⚠ YouTube feed failed: {exc}")
            return []

        feed = feedparser.parse(resp.content)
        channel_title = (feed.feed.get("title") or "").replace("YouTube channel: ", "").strip()
        results: List[Dict[str, Any]] = []

        for entry in feed.entries[:20]:
            published = _parse_feed_datetime(entry)
            if not published:
                continue
            if published.year != allowed_year:
                continue
            if published < cutoff:
                continue

            title = (entry.get("title") or "").strip()
            link = (entry.get("link") or "").strip()
            if not title or not link:
                continue

            summary_full = _strip_html(entry.get("summary") or "")
            ai_window = self._get_text_window()
            signal_window = self._get_signal_window(ai_window)

            # Signal keywords must appear early (title + description head) to reduce false positives
            # from long sponsor/link dumps.
            ai_text = f"{title} {summary_full[:ai_window]}".lower()
            signal_text = f"{title} {summary_full[:signal_window]}".lower()

            ai_hit = any(k in ai_text for k in AI_KEYWORDS)
            signal_hit = any(k in signal_text for k in SIGNAL_KEYWORDS)
            open_source_phrase_hit = any(p in signal_text for p in OPEN_SOURCE_PHRASES)

            # github.com alone is NOT considered a signal; it must be accompanied by open-source phrasing.
            if not (ai_hit and (signal_hit or open_source_phrase_hit)):
                continue

            video_id = _extract_video_id(link)
            summary = summary_full[:ai_window]
            categories = _infer_categories(f"{title} {summary}".lower())

            results.append(self.create_product(
                name=title,
                description=(summary or title)[:240],
                logo_url="",
                website=link,
                categories=categories,
                weekly_users=0,
                trending_score=80,
                source="youtube",
                published_at=_to_iso(published) or _to_iso(datetime.now(timezone.utc)),
                extra={
                    "channel": channel_title,
                    "channel_id": self._extract_channel_id_from_feed_url(feed_url),
                    "video_id": video_id,
                    "source_type": "youtube",
                },
            ))

        return results

    @staticmethod
    def _extract_channel_id_from_feed_url(url: str) -> str:
        try:
            parsed = urlparse(url)
            qs = parse_qs(parsed.query or "")
            return (qs.get("channel_id") or [""])[0]
        except Exception:
            return ""
