"""
CN news spider.

Collect AI signals from China-native RSS sources for blogs_news.json.
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


CN_RSS_FEEDS = [
    {"name": "36kr", "url": "https://36kr.com/feed"},
    {"name": "jiqizhixin", "url": "https://www.jiqizhixin.com/rss"},
    {"name": "tmtpost", "url": "https://www.tmtpost.com/rss"},
    {"name": "qbitai", "url": "https://www.qbitai.com/rss"},
    {"name": "leiphone", "url": "https://www.leiphone.com/feed"},
    {"name": "huxiu", "url": "https://www.huxiu.com/rss/0.xml"},
    {"name": "ifanr", "url": "https://www.ifanr.com/feed"},
    {"name": "ithome", "url": "https://www.ithome.com/rss"},
    {"name": "sspai", "url": "https://sspai.com/feed"},
]


AI_KEYWORDS = [
    "ai",
    "llm",
    "gpt",
    "agent",
    "aigc",
    "生成式",
    "人工智能",
    "大模型",
    "智能体",
    "具身智能",
    "机器人",
    "自动驾驶",
    "芯片",
    "算力",
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
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        try:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
        except Exception:
            pass

    value = entry.get("published") or entry.get("updated")
    if not value:
        return None

    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        except Exception:
            continue
    return None


class CNNewsSpider(BaseSpider):
    """Collect AI signals from China-native RSS feeds."""

    def __init__(self):
        super().__init__()
        self.session.headers.update({
            "Accept": "application/xml,text/xml,application/rss+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.5",
        })

    def crawl(self) -> List[Dict[str, Any]]:
        if not HAS_FEEDPARSER:
            print("  [CNNews] feedparser not installed, skipping")
            return []

        try:
            allowed_year = int(os.getenv("CONTENT_YEAR", str(datetime.now(timezone.utc).year)))
        except Exception:
            allowed_year = datetime.now(timezone.utc).year

        hours_raw = os.getenv("CN_NEWS_HOURS", os.getenv("SOCIAL_HOURS", "96"))
        try:
            hours = max(12, min(240, int(hours_raw)))
        except Exception:
            hours = 96
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        print(f"  [CNNews] Collecting from {len(CN_RSS_FEEDS)} CN sources (last {hours}h)...")
        results: List[Dict[str, Any]] = []
        seen_urls = set()

        for feed_cfg in CN_RSS_FEEDS:
            name = feed_cfg["name"]
            url = feed_cfg["url"]
            items = self._fetch_feed(name=name, feed_url=url, cutoff=cutoff, allowed_year=allowed_year)
            for item in items:
                website = (item.get("website") or "").strip()
                if not website or website in seen_urls:
                    continue
                seen_urls.add(website)
                results.append(item)

        results.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        print(f"  [CNNews] Collected {len(results)} items")
        return results[:180]

    def _fetch_feed(self, *, name: str, feed_url: str, cutoff: datetime, allowed_year: int) -> List[Dict[str, Any]]:
        try:
            resp = self.session.get(feed_url, timeout=20)
            resp.raise_for_status()
        except Exception as exc:
            print(f"    ⚠ {name} feed failed: {exc}")
            return []

        feed = feedparser.parse(resp.content)
        items: List[Dict[str, Any]] = []

        for entry in feed.entries[:40]:
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

            summary = _strip_html(entry.get("summary") or entry.get("description") or "")
            text = f"{title} {summary}".lower()
            if not any(keyword in text for keyword in AI_KEYWORDS):
                continue

            items.append(self.create_product(
                name=title[:160],
                description=(summary or title)[:240],
                logo_url="",
                website=link,
                categories=["other"],
                weekly_users=0,
                trending_score=70,
                rating=3.8,
                source="cn_news",
                published_at=_to_iso(published) or _to_iso(datetime.now(timezone.utc)),
                extra={
                    "source_type": "cn_rss",
                    "cn_source": name,
                    "feed_url": feed_url,
                },
            ))

        if items:
            print(f"    • {name}: {len(items)} items")
        return items
