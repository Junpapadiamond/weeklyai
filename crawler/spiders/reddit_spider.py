"""
Reddit signals spider.

Collects high-signal AI discussions from configured subreddit watchlists.
Output items use source="reddit" and are classified into blogs_news.json.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

from .base_spider import BaseSpider
from utils.social_sources import load_reddit_subreddits_with_source


AI_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "llm",
    "gpt",
    "agent",
    "openai",
    "anthropic",
    "claude",
    "gemini",
    "copilot",
    "rag",
    "embedding",
    "inference",
    "transformer",
    "diffusion",
    "machine learning",
]

SIGNAL_KEYWORDS = [
    "launch",
    "launched",
    "release",
    "released",
    "demo",
    "open source",
    "open-source",
    "github",
    "funding",
    "seed",
    "series a",
    "series b",
    "showcase",
    "introducing",
    "benchmark",
    "paper",
]


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


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
    return None


def _infer_categories(text: str) -> List[str]:
    lower = (text or "").lower()
    mapping = {
        "agent": ["agent", "assistant", "autonomous"],
        "coding": ["code", "coding", "developer", "github", "sdk", "api", "repo"],
        "image": ["image", "vision", "diffusion", "stable diffusion", "midjourney"],
        "video": ["video", "sora", "runway", "pika"],
        "voice": ["voice", "audio", "speech", "tts"],
        "hardware": ["robot", "chip", "hardware", "device", "wearable", "glasses"],
        "writing": ["writing", "text", "copy"],
        "finance": ["funding", "seed", "series", "valuation", "raises", "raised"],
    }
    categories: List[str] = []
    for cat, keywords in mapping.items():
        if any(keyword in lower for keyword in keywords):
            categories.append(cat)
    return categories or ["other"]


def _score_to_trending(score: int, comments: int) -> int:
    magnitude = (max(score, 0) + max(comments, 0) * 1.2) ** 0.5
    trending = 66 + int(min(28, magnitude * 3.2))
    return max(68, min(95, trending))


class RedditSpider(BaseSpider):
    """Collect AI social signals from Reddit subreddits."""

    def __init__(self):
        super().__init__()
        self.user_agent = os.getenv(
            "REDDIT_USER_AGENT",
            "WeeklyAI/1.0 (https://weeklyai.app)",
        )
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "application/json,text/plain,*/*",
            }
        )

    def crawl(self) -> List[Dict[str, Any]]:
        subreddits, sub_source = load_reddit_subreddits_with_source()
        if not subreddits:
            print("  [Reddit] No subreddits configured, skipping")
            return []

        try:
            allowed_year = int(os.getenv("CONTENT_YEAR", str(datetime.now(timezone.utc).year)))
        except Exception:
            allowed_year = datetime.now(timezone.utc).year

        try:
            hours = max(24, min(240, int(os.getenv("SOCIAL_HOURS", "96"))))
        except Exception:
            hours = 96
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        try:
            limit_per_sub = max(10, min(100, int(os.getenv("SOCIAL_REDDIT_LIMIT_PER_SUB", "35"))))
        except Exception:
            limit_per_sub = 35

        print(
            f"  [Reddit] Collecting signals from {len(subreddits)} subreddits "
            f"(last {hours}h, source={sub_source}, per_sub={limit_per_sub})..."
        )

        items: List[Dict[str, Any]] = []
        seen_urls = set()

        for subreddit in subreddits[:30]:
            sub_items = self._fetch_subreddit_json(
                subreddit=subreddit,
                cutoff=cutoff,
                allowed_year=allowed_year,
                limit=limit_per_sub,
            )

            if not sub_items and HAS_FEEDPARSER:
                sub_items = self._fetch_subreddit_rss(
                    subreddit=subreddit,
                    cutoff=cutoff,
                    allowed_year=allowed_year,
                    limit=min(limit_per_sub, 25),
                )

            for item in sub_items:
                website = (item.get("website") or "").strip()
                if not website or website in seen_urls:
                    continue
                seen_urls.add(website)
                items.append(item)

        print(f"  [Reddit] Collected {len(items)} items")
        return items[:80]

    def _is_ai_relevant(self, text: str) -> bool:
        lower = (text or "").lower()
        ai_hit = any(keyword in lower for keyword in AI_KEYWORDS)
        signal_hit = any(keyword in lower for keyword in SIGNAL_KEYWORDS)
        return ai_hit and signal_hit

    def _fetch_subreddit_json(self, subreddit: str, cutoff: datetime, allowed_year: int, limit: int) -> List[Dict[str, Any]]:
        url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
        try:
            resp = self.session.get(url, timeout=20)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:
            print(f"    ⚠ Reddit JSON failed r/{subreddit}: {exc}")
            return []

        results: List[Dict[str, Any]] = []

        for child in payload.get("data", {}).get("children", []):
            post = child.get("data", {}) if isinstance(child, dict) else {}
            if not post:
                continue
            if post.get("stickied"):
                continue

            created_utc = post.get("created_utc")
            if not created_utc:
                continue
            published = datetime.fromtimestamp(float(created_utc), tz=timezone.utc)
            if published.year != allowed_year:
                continue
            if published < cutoff:
                continue

            title = _normalize_spaces(post.get("title") or "")
            if not title:
                continue

            body = _normalize_spaces(post.get("selftext") or "")
            flair = _normalize_spaces(post.get("link_flair_text") or "")
            if not self._is_ai_relevant(f"{title} {body} {flair}"):
                continue

            permalink = (post.get("permalink") or "").strip()
            source_url = f"https://www.reddit.com{permalink}" if permalink else ""
            if not source_url:
                continue

            external_url = _normalize_spaces(post.get("url_overridden_by_dest") or post.get("url") or "")
            summary = body or external_url or title
            if len(summary) > 240:
                summary = f"{summary[:237]}..."

            score = int(post.get("score") or 0)
            comments = int(post.get("num_comments") or 0)

            results.append(
                self.create_product(
                    name=title,
                    description=summary,
                    logo_url="",
                    website=source_url,
                    categories=_infer_categories(f"{title} {body} {flair}"),
                    weekly_users=0,
                    trending_score=_score_to_trending(score, comments),
                    source="reddit",
                    published_at=_to_iso(published) or _to_iso(datetime.now(timezone.utc)),
                    extra={
                        "source_type": "reddit",
                        "subreddit": subreddit,
                        "author": _normalize_spaces(post.get("author") or ""),
                        "upvotes": score,
                        "comments": comments,
                        "external_url": external_url,
                        "flair": flair,
                    },
                )
            )

        return results

    def _fetch_subreddit_rss(self, subreddit: str, cutoff: datetime, allowed_year: int, limit: int) -> List[Dict[str, Any]]:
        url = f"https://www.reddit.com/r/{subreddit}/.rss"
        try:
            resp = self.session.get(url, timeout=20)
            resp.raise_for_status()
        except Exception:
            return []

        feed = feedparser.parse(resp.content)
        results: List[Dict[str, Any]] = []

        for entry in feed.entries[:limit]:
            published = _parse_feed_datetime(entry)
            if not published:
                continue
            if published.year != allowed_year:
                continue
            if published < cutoff:
                continue

            title = _normalize_spaces(entry.get("title") or "")
            link = _normalize_spaces(entry.get("link") or "")
            summary = _normalize_spaces(_strip_html(entry.get("summary") or ""))
            if not title or not link:
                continue
            if not self._is_ai_relevant(f"{title} {summary}"):
                continue
            if len(summary) > 240:
                summary = f"{summary[:237]}..."

            results.append(
                self.create_product(
                    name=title,
                    description=summary or title,
                    logo_url="",
                    website=link,
                    categories=_infer_categories(f"{title} {summary}"),
                    weekly_users=0,
                    trending_score=72,
                    source="reddit",
                    published_at=_to_iso(published) or _to_iso(datetime.now(timezone.utc)),
                    extra={
                        "source_type": "reddit",
                        "subreddit": subreddit,
                    },
                )
            )

        return results
