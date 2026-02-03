#!/usr/bin/env python3
"""
Daily news collector for WeeklyAI.

Phase 1: RSS + Hacker News
Phase 2: Reddit + X (via Nitter RSS)

Output: crawler/data/news_daily.json
Schema (per item):
  - title
  - source
  - source_url
  - published_at (ISO 8601)
  - snippet
  - author
  - tags (list)
  - raw_score (number)
  - discovered_at (ISO 8601)
  - extra (dict)
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

import requests

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

# Add project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DEFAULT_OUTPUT = os.path.join(DATA_DIR, "news_daily.json")

USER_AGENT = os.getenv(
    "NEWS_USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
)

# ----------------------------
# Source configs
# ----------------------------

RSS_FEEDS = [
    {
        "id": "techcrunch_ai",
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "tags": ["tech_news", "ai"],
    },
    {
        "id": "theverge_ai",
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "tags": ["tech_news", "ai"],
    },
    {
        "id": "wired_ai",
        "name": "Wired AI",
        "url": "https://www.wired.com/feed/tag/ai/latest/rss",
        "tags": ["tech_news", "ai"],
    },
    {
        "id": "venturebeat_ai",
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/",
        "tags": ["tech_news", "ai"],
    },
    {
        "id": "arstechnica_tech",
        "name": "Ars Technica",
        "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "tags": ["tech_news"],
    },
    {
        "id": "mit_tech_review",
        "name": "MIT Tech Review",
        "url": "https://www.technologyreview.com/feed/",
        "tags": ["tech_news"],
    },
    {
        "id": "producthunt_ai",
        "name": "Product Hunt AI",
        "url": "https://www.producthunt.com/topics/artificial-intelligence/feed",
        "tags": ["producthunt", "launch"],
    },
]

HN_QUERIES = [
    "ai",
    "gpt",
    "llm",
    "machine learning",
    "ai agent",
]

DEFAULT_REDDIT_SUBS = [
    "MachineLearning",
    "LocalLLaMA",
    "AI",
    "ClaudeAI",
    "OpenAI",
]

DEFAULT_X_ACCOUNTS: List[str] = []


TAG_RULES = {
    "launch": ["launch", "released", "release", "announc", "introduc", "rollout", "unveil"],
    "funding": ["funding", "seed", "series a", "series b", "raises", "round"],
    "model": ["model", "llm", "gpt", "gemini", "claude", "mistral"],
    "agent": ["agent", "assistant"],
    "open_source": ["open source", "github", "repo"],
    "hardware": ["robot", "chip", "hardware", "device", "wearable"],
    "api": ["api", "sdk", "developer"],
}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        cleaned = value.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    except Exception:
        return None


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (title or "").lower())


def ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def load_json(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []


def save_json(path: str, data: List[Dict[str, Any]]) -> None:
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_tags(text: str, base_tags: Optional[Iterable[str]] = None) -> List[str]:
    tags = set(base_tags or [])
    text_lower = (text or "").lower()
    for tag, keywords in TAG_RULES.items():
        if any(k in text_lower for k in keywords):
            tags.add(tag)
    return sorted(tags)


def dedupe_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    unique = []
    for item in items:
        source = item.get("source") or ""
        source_url = item.get("source_url") or ""
        title = item.get("title") or ""
        key = source_url or f"{source}:{normalize_title(title)}"
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def sort_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def sort_key(item: Dict[str, Any]) -> str:
        published = item.get("published_at") or item.get("discovered_at") or ""
        return published
    return sorted(items, key=sort_key, reverse=True)


def parse_entry_date(entry: Any) -> Optional[datetime]:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

    for field in ("published", "updated", "created"):
        value = entry.get(field)
        if not value:
            continue
        for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(value, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                continue
    return None


def fetch_rss_feed(feed_config: Dict[str, Any], cutoff: datetime, limit: int) -> List[Dict[str, Any]]:
    if not HAS_FEEDPARSER:
        return []

    url = feed_config.get("url")
    if not url:
        return []

    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[rss] failed {feed_config.get('name', url)}: {exc}")
        return []

    feed = feedparser.parse(resp.content)
    items: List[Dict[str, Any]] = []

    for entry in feed.entries[:limit]:
        published = parse_entry_date(entry)
        if published and published < cutoff:
            continue

        title = (entry.get("title") or "").strip()
        if not title:
            continue

        summary = entry.get("summary") or ""
        if not summary and entry.get("content"):
            try:
                summary = entry.content[0].value
            except Exception:
                summary = ""
        summary = strip_html(summary)
        if len(summary) > 280:
            summary = summary[:277] + "..."

        link = entry.get("link") or ""
        author = entry.get("author") or ""

        entry_tags = []
        if entry.get("tags"):
            entry_tags = [t.get("term") for t in entry.get("tags") if t.get("term")]

        item = {
            "title": title,
            "source": feed_config.get("id") or "rss",
            "source_url": link,
            "published_at": to_iso(published) or to_iso(now_utc()),
            "snippet": summary,
            "author": author,
            "tags": extract_tags(f"{title} {summary}", base_tags=(feed_config.get("tags") or []) + entry_tags),
            "raw_score": 0,
            "discovered_at": to_iso(now_utc()),
            "extra": {
                "source_name": feed_config.get("name"),
                "source_type": "rss",
                "feed_url": url,
            },
        }
        items.append(item)

    return items


def collect_rss(cutoff: datetime, limit_per_feed: int) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for feed in RSS_FEEDS:
        items.extend(fetch_rss_feed(feed, cutoff=cutoff, limit=limit_per_feed))
    return items


def is_ai_related(text: str) -> bool:
    keywords = [
        "ai",
        "gpt",
        "llm",
        "machine learning",
        "artificial intelligence",
        "agent",
        "diffusion",
        "transformer",
        "chatbot",
        "assistant",
    ]
    lower = (text or "").lower()
    return any(k in lower for k in keywords)


def collect_hackernews(cutoff: datetime, limit_per_query: int) -> List[Dict[str, Any]]:
    api_base = "https://hn.algolia.com/api/v1/search_by_date"
    items: List[Dict[str, Any]] = []
    seen_titles = set()
    since_ts = int(cutoff.timestamp())
    headers = {"User-Agent": USER_AGENT}

    for query in HN_QUERIES:
        params = {
            "query": query,
            "tags": "story",
            "hitsPerPage": limit_per_query,
            "numericFilters": f"created_at_i>{since_ts}",
        }
        try:
            resp = requests.get(api_base, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
        except Exception as exc:
            print(f"[hn] query failed {query}: {exc}")
            continue

        data = resp.json()
        for hit in data.get("hits", []):
            title = hit.get("title") or ""
            if not title or title in seen_titles:
                continue
            text = f"{title} {hit.get('story_text') or ''}"
            if not is_ai_related(text):
                continue

            created_at = hit.get("created_at")
            published = None
            if created_at:
                try:
                    published = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except Exception:
                    published = None

            url = hit.get("url") or ""
            hn_id = hit.get("objectID") or ""
            hn_url = f"https://news.ycombinator.com/item?id={hn_id}" if hn_id else url

            points = hit.get("points") or 0
            comments = hit.get("num_comments") or 0
            raw_score = int(points) if points else 0

            item = {
                "title": title,
                "source": "hackernews",
                "source_url": hn_url,
                "published_at": to_iso(published) or to_iso(now_utc()),
                "snippet": strip_html(hit.get("story_text") or "")[:280],
                "author": hit.get("author") or "",
                "tags": extract_tags(title, base_tags=["hackernews"]),
                "raw_score": raw_score,
                "discovered_at": to_iso(now_utc()),
                "extra": {
                    "source_type": "hackernews",
                    "hn_id": hn_id,
                    "points": points,
                    "comments": comments,
                    "external_url": url,
                },
            }
            items.append(item)
            seen_titles.add(title)

    return items


def fetch_reddit_json(subreddit: str, cutoff: datetime, limit: int) -> List[Dict[str, Any]]:
    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[reddit] json failed r/{subreddit}: {exc}")
        return []

    data = resp.json()
    items: List[Dict[str, Any]] = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        if post.get("stickied"):
            continue

        created_utc = post.get("created_utc")
        if not created_utc:
            continue
        published = datetime.fromtimestamp(created_utc, tz=timezone.utc)
        if published < cutoff:
            continue

        title = post.get("title") or ""
        if not title:
            continue

        permalink = post.get("permalink") or ""
        source_url = f"https://www.reddit.com{permalink}" if permalink else ""

        summary = post.get("selftext") or ""
        summary = strip_html(summary)
        if not summary:
            summary = post.get("url") or ""
        if len(summary) > 280:
            summary = summary[:277] + "..."

        flair = post.get("link_flair_text") or ""
        tags = ["reddit", f"r/{subreddit}"]
        if flair:
            tags.append(flair)

        item = {
            "title": title,
            "source": "reddit",
            "source_url": source_url,
            "published_at": to_iso(published),
            "snippet": summary,
            "author": post.get("author") or "",
            "tags": extract_tags(title, base_tags=tags),
            "raw_score": int(post.get("score") or 0),
            "discovered_at": to_iso(now_utc()),
            "extra": {
                "source_type": "reddit",
                "subreddit": subreddit,
                "comments": int(post.get("num_comments") or 0),
                "external_url": post.get("url"),
            },
        }
        items.append(item)

    return items


def fetch_reddit_rss(subreddit: str, cutoff: datetime, limit: int) -> List[Dict[str, Any]]:
    if not HAS_FEEDPARSER:
        return []
    url = f"https://www.reddit.com/r/{subreddit}/.rss"
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception:
        return []
    feed = feedparser.parse(resp.content)
    items: List[Dict[str, Any]] = []

    for entry in feed.entries[:limit]:
        published = parse_entry_date(entry)
        if published and published < cutoff:
            continue
        title = (entry.get("title") or "").strip()
        if not title:
            continue
        summary = strip_html(entry.get("summary") or "")
        if len(summary) > 280:
            summary = summary[:277] + "..."
        link = entry.get("link") or ""

        item = {
            "title": title,
            "source": "reddit",
            "source_url": link,
            "published_at": to_iso(published) or to_iso(now_utc()),
            "snippet": summary,
            "author": entry.get("author") or "",
            "tags": extract_tags(title, base_tags=["reddit", f"r/{subreddit}"]),
            "raw_score": 0,
            "discovered_at": to_iso(now_utc()),
            "extra": {
                "source_type": "reddit",
                "subreddit": subreddit,
            },
        }
        items.append(item)

    return items


def collect_reddit(cutoff: datetime, limit_per_sub: int) -> List[Dict[str, Any]]:
    subs_env = os.getenv("NEWS_REDDIT_SUBS")
    subreddits = [s.strip() for s in subs_env.split(",") if s.strip()] if subs_env else DEFAULT_REDDIT_SUBS

    items: List[Dict[str, Any]] = []
    for subreddit in subreddits:
        sub_items = fetch_reddit_json(subreddit, cutoff=cutoff, limit=limit_per_sub)
        if not sub_items:
            sub_items = fetch_reddit_rss(subreddit, cutoff=cutoff, limit=limit_per_sub)
        items.extend(sub_items)
    return items


def extract_tweet_id(url: str) -> Optional[str]:
    match = re.search(r"/status/(\d+)", url or "")
    return match.group(1) if match else None


def collect_x(cutoff: datetime, limit_per_account: int) -> List[Dict[str, Any]]:
    if not HAS_FEEDPARSER:
        return []

    accounts_env = os.getenv("NEWS_X_ACCOUNTS")
    accounts = [a.strip().lstrip("@") for a in accounts_env.split(",") if a.strip()] if accounts_env else DEFAULT_X_ACCOUNTS
    if not accounts:
        return []

    nitter_base = os.getenv("NITTER_BASE", "https://nitter.net").rstrip("/")
    items: List[Dict[str, Any]] = []

    headers = {"User-Agent": USER_AGENT}
    for handle in accounts:
        rss_url = f"{nitter_base}/{handle}/rss"
        try:
            resp = requests.get(rss_url, headers=headers, timeout=20)
            resp.raise_for_status()
        except Exception as exc:
            print(f"[x] rss failed @{handle}: {exc}")
            continue
        feed = feedparser.parse(resp.content)

        for entry in feed.entries[:limit_per_account]:
            published = parse_entry_date(entry)
            if published and published < cutoff:
                continue

            title = (entry.get("title") or "").strip()
            if not title:
                continue
            # Nitter titles often include "User: tweet"
            title_clean = re.sub(r"^[^:]+:\s*", "", title).strip()

            link = entry.get("link") or ""
            tweet_id = extract_tweet_id(link)
            twitter_url = f"https://twitter.com/{handle}/status/{tweet_id}" if tweet_id else link

            summary = strip_html(entry.get("summary") or "")
            if len(summary) > 280:
                summary = summary[:277] + "..."

            item = {
                "title": title_clean or title,
                "source": "x",
                "source_url": twitter_url,
                "published_at": to_iso(published) or to_iso(now_utc()),
                "snippet": summary,
                "author": handle,
                "tags": extract_tags(title_clean or title, base_tags=["x", f"@{handle}"]),
                "raw_score": 0,
                "discovered_at": to_iso(now_utc()),
                "extra": {
                    "source_type": "x",
                    "account": handle,
                    "nitter_url": link,
                },
            }
            items.append(item)

    return items


def filter_recent(items: List[Dict[str, Any]], cutoff: datetime) -> List[Dict[str, Any]]:
    filtered = []
    for item in items:
        published = parse_iso(item.get("published_at") or "")
        if published and published < cutoff:
            continue
        filtered.append(item)
    return filtered


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="WeeklyAI daily news collector")
    parser.add_argument("--hours", type=int, default=int(os.getenv("NEWS_HOURS", "48")))
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT)
    parser.add_argument("--limit-rss", type=int, default=30)
    parser.add_argument("--limit-hn", type=int, default=50)
    parser.add_argument("--limit-reddit", type=int, default=50)
    parser.add_argument("--limit-x", type=int, default=50)
    parser.add_argument("--sources", default="rss,hn,reddit,x", help="comma list: rss,hn,reddit,x")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if not HAS_FEEDPARSER:
        print("feedparser not installed. Run: pip install feedparser")

    cutoff = now_utc() - timedelta(hours=args.hours)
    sources = {s.strip().lower() for s in args.sources.split(",") if s.strip()}

    new_items: List[Dict[str, Any]] = []

    if "rss" in sources:
        rss_items = collect_rss(cutoff=cutoff, limit_per_feed=args.limit_rss)
        print(f"[rss] collected {len(rss_items)} items")
        new_items.extend(rss_items)

    if "hn" in sources:
        hn_items = collect_hackernews(cutoff=cutoff, limit_per_query=args.limit_hn)
        print(f"[hn] collected {len(hn_items)} items")
        new_items.extend(hn_items)

    if "reddit" in sources:
        reddit_items = collect_reddit(cutoff=cutoff, limit_per_sub=args.limit_reddit)
        print(f"[reddit] collected {len(reddit_items)} items")
        new_items.extend(reddit_items)

    if "x" in sources:
        x_items = collect_x(cutoff=cutoff, limit_per_account=args.limit_x)
        print(f"[x] collected {len(x_items)} items")
        new_items.extend(x_items)

    # Merge with existing data unless overwrite
    combined = new_items
    if not args.overwrite:
        existing = load_json(args.output)
        combined = existing + new_items

    combined = filter_recent(combined, cutoff=cutoff)
    combined = dedupe_items(combined)
    combined = sort_items(combined)

    if args.dry_run:
        print(f"[dry-run] total items after merge: {len(combined)}")
        return

    save_json(args.output, combined)
    print(f"[done] saved {len(combined)} items to {args.output}")


if __name__ == "__main__":
    main()
