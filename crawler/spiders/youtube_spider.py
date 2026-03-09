"""
YouTube signals spider.

Goal: Collect high-signal AI product mentions from YouTube sources.
Primary path: Channel RSS feed.
Fallback path: Channel videos page parsing (browser-style fallback).
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import requests

try:
    import feedparser

    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

from .base_spider import BaseSpider
from utils.social_health import load_social_health, update_source_health
from utils.social_sources import (
    load_youtube_channel_configs_with_source,
    load_youtube_health_policy,
)


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

_VIDEO_SNIPPET_PATTERN = re.compile(
    r'"videoId":"(?P<video_id>[A-Za-z0-9_-]{11})".{0,900}?"title":\{"runs":\[\{"text":"(?P<title>[^"]+)"',
    re.DOTALL,
)
_DESCRIPTION_SNIPPET_PATTERN = re.compile(
    r'"descriptionSnippet":\{"runs":\[\{"text":"(?P<desc>[^"]+)"',
    re.DOTALL,
)


def _truthy(value: str, default: bool = False) -> bool:
    if not value:
        return default
    raw = value.strip().lower()
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _to_iso(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _from_iso(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


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


def _classify_request_error(exc: Exception) -> str:
    if isinstance(exc, requests.HTTPError):
        code = getattr(exc.response, "status_code", None)
        if code:
            return f"http_{int(code)}"
    if isinstance(exc, requests.Timeout):
        return "timeout"
    if isinstance(exc, requests.ConnectionError):
        return "connection_error"
    return "request_error"


class YouTubeSpider(BaseSpider):
    """Collect AI signals from YouTube RSS feeds with resilient fallback."""

    def __init__(self):
        super().__init__()
        self.session.headers.update(
            {
                "Accept": "application/atom+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
            }
        )
        self.enable_browser_fallback = _truthy(
            os.getenv("YOUTUBE_ENABLE_BROWSER_FALLBACK", "true"),
            default=True,
        )
        self.max_items = max(20, min(120, int(os.getenv("SOCIAL_YOUTUBE_MAX_ITEMS", "60"))))

    def crawl(self) -> List[Dict[str, Any]]:
        channel_configs, channel_source = self._get_channel_configs_with_source()
        if not channel_configs:
            print("  [YouTube] No channel ids configured, skipping")
            print("    remediation: set YOUTUBE_CHANNEL_IDS in .env or add youtube.channels to crawler/data/source_watchlists.json")
            self._update_health(
                count=0,
                channel_total=0,
                fallback_hits=0,
                fallback_attempts=0,
                errors={"no_channels": 1},
                channels={},
                skipped_cooldown=0,
            )
            return []

        try:
            allowed_year = int(os.getenv("CONTENT_YEAR", str(datetime.now(timezone.utc).year)))
        except Exception:
            allowed_year = datetime.now(timezone.utc).year

        hours = int(os.getenv("SOCIAL_HOURS", "96"))
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        policy = load_youtube_health_policy()
        threshold = int(policy.get("consecutive_404_threshold", 3) or 3)
        cooldown_days = int(policy.get("cooldown_days", 7) or 7)
        now_utc = datetime.now(timezone.utc)

        items: List[Dict[str, Any]] = []
        seen_urls = set()
        errors: Dict[str, int] = {}
        channels_payload: Dict[str, Dict[str, Any]] = {}
        skipped_cooldown = 0
        fallback_hits = 0
        fallback_attempts = 0

        previous = self._load_previous_channel_health()

        print(
            f"  [YouTube] Collecting signals from {len(channel_configs)} channels "
            f"(last {hours}h, source={channel_source}, browser_fallback={self.enable_browser_fallback})..."
        )

        for channel_cfg in channel_configs[:80]:
            channel_id = str(channel_cfg.get("channel_id") or "").strip()
            if not channel_id:
                continue
            if not bool(channel_cfg.get("enabled", True)):
                channels_payload[channel_id] = dict(previous.get(channel_id) or {})
                channels_payload[channel_id]["status"] = "disabled"
                channels_payload[channel_id]["updated_at"] = _to_iso(now_utc)
                continue

            state = dict(previous.get(channel_id) or {})
            cooldown_until = _from_iso(str(state.get("cooldown_until") or ""))
            if cooldown_until and cooldown_until > now_utc:
                skipped_cooldown += 1
                state["status"] = "cooldown"
                state["updated_at"] = _to_iso(now_utc)
                channels_payload[channel_id] = state
                continue

            channel_items, meta = self._fetch_channel_with_fallback(
                channel_id=channel_id,
                channel_name=str(channel_cfg.get("name") or "").strip(),
                cutoff=cutoff,
                allowed_year=allowed_year,
            )
            if meta.get("fallback_attempted"):
                fallback_attempts += 1
            if meta.get("fallback_used"):
                fallback_hits += 1

            for item in channel_items:
                url = item.get("website") or ""
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                items.append(item)

            error_key = str(meta.get("error") or "").strip()
            if error_key:
                errors[error_key] = int(errors.get(error_key, 0)) + 1
                state["last_error"] = error_key
                if error_key == "http_404":
                    consecutive = int(state.get("consecutive_404", 0) or 0) + 1
                    state["consecutive_404"] = consecutive
                    if consecutive >= threshold:
                        state["cooldown_until"] = _to_iso(now_utc + timedelta(days=cooldown_days))
                        state["status"] = "invalid_channel"
                else:
                    state["status"] = "error"
            else:
                state["consecutive_404"] = 0
                state["cooldown_until"] = ""
                state["last_error"] = ""
                state["status"] = "ok"

            if meta.get("channel_title"):
                state["channel_title"] = meta["channel_title"]
            state["last_checked"] = _to_iso(now_utc)
            state["updated_at"] = _to_iso(now_utc)
            channels_payload[channel_id] = state

        print(f"  [YouTube] Collected {len(items)} items")
        self._update_health(
            count=len(items),
            channel_total=len(channel_configs),
            fallback_hits=fallback_hits,
            fallback_attempts=fallback_attempts,
            errors=errors,
            channels=channels_payload,
            skipped_cooldown=skipped_cooldown,
        )
        return items[: self.max_items]

    @staticmethod
    def _get_text_window() -> int:
        try:
            return max(200, min(4000, int(os.getenv("SOCIAL_TEXT_WINDOW", "800"))))
        except Exception:
            return 800

    @staticmethod
    def _get_signal_window(ai_window: int) -> int:
        try:
            requested = int(os.getenv("SOCIAL_SIGNAL_WINDOW", "500"))
        except Exception:
            requested = 500
        return min(ai_window, max(200, min(800, requested)))

    @staticmethod
    def _get_channel_configs_with_source() -> Tuple[List[Dict[str, Any]], str]:
        return load_youtube_channel_configs_with_source()

    def _passes_signal_filter(self, title: str, summary_full: str) -> bool:
        ai_window = self._get_text_window()
        signal_window = self._get_signal_window(ai_window)

        ai_text = f"{title} {summary_full[:ai_window]}".lower()
        signal_text = f"{title} {summary_full[:signal_window]}".lower()

        ai_hit = any(k in ai_text for k in AI_KEYWORDS)
        signal_hit = any(k in signal_text for k in SIGNAL_KEYWORDS)
        open_source_phrase_hit = any(p in signal_text for p in OPEN_SOURCE_PHRASES)
        return bool(ai_hit and (signal_hit or open_source_phrase_hit))

    def _build_item(
        self,
        *,
        channel_id: str,
        channel_title: str,
        title: str,
        link: str,
        summary_full: str,
        published: Optional[datetime],
    ) -> Dict[str, Any]:
        summary = summary_full[: self._get_text_window()]
        categories = _infer_categories(f"{title} {summary}".lower())
        return self.create_product(
            name=title,
            description=(summary or title)[:240],
            logo_url="",
            website=link,
            categories=categories,
            weekly_users=0,
            trending_score=80,
            source="youtube",
            published_at=_to_iso(published or datetime.now(timezone.utc)),
            extra={
                "channel": channel_title,
                "channel_id": channel_id,
                "video_id": _extract_video_id(link),
                "source_type": "youtube",
            },
        )

    def _fetch_channel_with_fallback(
        self,
        *,
        channel_id: str,
        channel_name: str,
        cutoff: datetime,
        allowed_year: int,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        rss_items, rss_meta = self._fetch_channel_rss(
            channel_id=channel_id,
            channel_name=channel_name,
            cutoff=cutoff,
            allowed_year=allowed_year,
        )
        if rss_items:
            return rss_items, rss_meta

        error = str(rss_meta.get("error") or "")
        fallback_attempted = bool(error) and self.enable_browser_fallback
        if fallback_attempted:
            fallback_items, fallback_meta = self._fetch_channel_videos_page(
                channel_id=channel_id,
                channel_name=channel_name,
                cutoff=cutoff,
                allowed_year=allowed_year,
            )
            if fallback_items:
                meta = dict(fallback_meta)
                meta["fallback_used"] = True
                meta["fallback_attempted"] = True
                meta["error"] = ""
                return fallback_items, meta
            merged = dict(rss_meta)
            if fallback_meta.get("error"):
                merged["error"] = fallback_meta["error"]
            merged["fallback_attempted"] = True
            return [], merged

        rss_meta["fallback_attempted"] = False
        return [], rss_meta

    def _fetch_channel_rss(
        self,
        *,
        channel_id: str,
        channel_name: str,
        cutoff: datetime,
        allowed_year: int,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if not HAS_FEEDPARSER:
            return [], {"error": "feedparser_missing", "channel_title": channel_name}

        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            resp = self.fetch(feed_url)
        except Exception as exc:
            return [], {"error": _classify_request_error(exc), "channel_title": channel_name}

        feed = feedparser.parse(resp.content)
        channel_title = (feed.feed.get("title") or "").replace("YouTube channel: ", "").strip() or channel_name or channel_id
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
            if not self._passes_signal_filter(title, summary_full):
                continue

            results.append(
                self._build_item(
                    channel_id=channel_id,
                    channel_title=channel_title,
                    title=title,
                    link=link,
                    summary_full=summary_full,
                    published=published,
                )
            )

        return results, {"error": "", "channel_title": channel_title, "fallback_used": False}

    def _fetch_channel_videos_page(
        self,
        *,
        channel_id: str,
        channel_name: str,
        cutoff: datetime,
        allowed_year: int,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        url = f"https://www.youtube.com/channel/{channel_id}/videos"
        try:
            resp = self.fetch(url)
        except Exception as exc:
            return [], {"error": _classify_request_error(exc), "channel_title": channel_name}

        text = (resp.text or "").replace("\\u0026", "&")
        results: List[Dict[str, Any]] = []
        seen_video_ids = set()
        channel_title = channel_name or channel_id

        for match in _VIDEO_SNIPPET_PATTERN.finditer(text):
            video_id = (match.group("video_id") or "").strip()
            title = (match.group("title") or "").strip()
            if not video_id or not title or video_id in seen_video_ids:
                continue
            seen_video_ids.add(video_id)

            chunk = text[match.start() : min(len(text), match.start() + 1200)]
            desc_match = _DESCRIPTION_SNIPPET_PATTERN.search(chunk)
            summary_full = (desc_match.group("desc") if desc_match else "").strip()
            summary_full = summary_full.replace("\\n", " ").strip()

            published = datetime.now(timezone.utc)
            if published.year != allowed_year:
                continue
            if published < cutoff:
                continue

            if not self._passes_signal_filter(title, summary_full):
                continue

            link = f"https://www.youtube.com/watch?v={video_id}"
            results.append(
                self._build_item(
                    channel_id=channel_id,
                    channel_title=channel_title,
                    title=title,
                    link=link,
                    summary_full=summary_full,
                    published=published,
                )
            )
            if len(results) >= 20:
                break

        if not results:
            return [], {"error": "browser_fallback_empty", "channel_title": channel_title}
        return results, {"error": "", "channel_title": channel_title, "fallback_used": True}

    @staticmethod
    def _load_previous_channel_health() -> Dict[str, Dict[str, Any]]:
        report = load_social_health()
        sources = report.get("sources") if isinstance(report, dict) else {}
        youtube = sources.get("youtube") if isinstance(sources, dict) else {}
        channels = youtube.get("channels") if isinstance(youtube, dict) else {}
        return channels if isinstance(channels, dict) else {}

    def _update_health(
        self,
        *,
        count: int,
        channel_total: int,
        fallback_hits: int,
        fallback_attempts: int,
        errors: Dict[str, int],
        channels: Dict[str, Dict[str, Any]],
        skipped_cooldown: int,
    ) -> None:
        hit_rate = 0.0
        if fallback_attempts > 0:
            hit_rate = round(float(fallback_hits) / float(fallback_attempts), 4)
        update_source_health(
            "youtube",
            {
                "count": int(count),
                "channel_total": int(channel_total),
                "skipped_cooldown": int(skipped_cooldown),
                "fallback_hits": int(fallback_hits),
                "fallback_attempts": int(fallback_attempts),
                "fallback_hit_rate": hit_rate,
                "errors": {k: int(v) for k, v in (errors or {}).items()},
                "channels": channels,
            },
        )
