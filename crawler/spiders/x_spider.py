"""
X/Twitter signals spider.

Primary path:
- Perplexity Search (query-driven discovery)

Fallback path:
- Account watchlist timeline fetch via r.jina.ai
- Tweet metadata fetch via syndication API
"""

from __future__ import annotations

import os
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from .base_spider import BaseSpider
from utils.social_sources import (
    load_x_accounts_with_source,
    load_x_fallback_config,
    load_x_source_mode,
)

try:
    from utils.perplexity_client import PerplexityClient
except Exception:
    PerplexityClient = None  # type: ignore


AI_KEYWORDS = [
    "ai",
    "llm",
    "gpt",
    "agent",
    "diffusion",
    "transformer",
    "openai",
    "anthropic",
    "claude",
    "gemini",
]

STATUS_URL_PATTERN = re.compile(
    r"https://(?:x|twitter)\.com/(?:[A-Za-z0-9_]+/status/\d+|i/(?:web/)?status/\d+)",
    re.IGNORECASE,
)


def _to_iso(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _parse_iso_or_date(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        cleaned = value.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned).astimezone(timezone.utc)
    except Exception:
        pass
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _extract_handle_and_id(url: str) -> Tuple[str, str]:
    # Expected:
    # - https://x.com/<handle>/status/<id>
    # - https://twitter.com/<handle>/status/<id>
    # - https://twitter.com/i/web/status/<id>
    try:
        parsed = urlparse(url)
        parts = [p for p in (parsed.path or "").split("/") if p]
        handle = ""
        tweet_id = ""
        if len(parts) >= 4 and parts[0] == "i" and parts[1] == "web" and parts[2] == "status":
            tweet_id = parts[3]
        elif len(parts) >= 3 and parts[0] == "i" and parts[1] == "status":
            tweet_id = parts[2]
        elif len(parts) >= 3 and parts[1] == "status":
            handle = parts[0]
            tweet_id = parts[2]
        return handle, tweet_id
    except Exception:
        return "", ""


def _infer_categories(text: str) -> List[str]:
    lower = (text or "").lower()
    mapping = {
        "agent": ["agent", "assistant", "autonomous"],
        "coding": ["code", "coding", "developer", "ide", "github", "api", "sdk"],
        "image": ["image", "vision", "diffusion", "midjourney", "stable diffusion"],
        "video": ["video", "sora", "runway", "pika"],
        "voice": ["voice", "audio", "speech", "tts"],
        "hardware": ["robot", "chip", "hardware", "device", "wearable", "glasses"],
        "writing": ["writing", "text", "document", "copy"],
        "finance": ["funding", "seed", "series", "raises", "raised", "valuation"],
    }
    categories: List[str] = []
    for cat, kws in mapping.items():
        if any(k in lower for k in kws):
            categories.append(cat)
    return categories or ["other"]


def _sanitize_status_url(url: str) -> str:
    return (url or "").strip().rstrip(".,;:!?)\"]'")


def _canonical_status_url(handle: str, tweet_id: str) -> str:
    if handle:
        return f"https://x.com/{handle}/status/{tweet_id}"
    return f"https://x.com/i/web/status/{tweet_id}"


class XSpider(BaseSpider):
    """Collect X signals via Perplexity search plus account-based fallback."""

    QUERIES = [
        '("introducing" OR "launched" OR "now live" OR "demo") (AI OR LLM OR agent) (site:x.com OR site:twitter.com)',
        '("open-sourced" OR "open source" OR "released") (AI OR agent) (site:x.com OR site:twitter.com)',
        '("seed" OR "Series A" OR "raised" OR "raises") AI startup (site:x.com OR site:twitter.com)',
        '("launch" OR "release" OR "beta" OR "preview") AI (agent OR tool) (site:x.com OR site:twitter.com)',
        '("thread" OR "here is" OR "demo") AI agent (site:x.com OR site:twitter.com)',
        '(("open source" OR "open-sourced") AND "github.com") AI (site:x.com OR site:twitter.com)',
    ]

    def crawl(self) -> List[Dict[str, Any]]:
        mode = load_x_source_mode()
        try:
            allowed_year = int(os.getenv("CONTENT_YEAR", str(datetime.now(timezone.utc).year)))
        except Exception:
            allowed_year = datetime.now(timezone.utc).year

        hours = int(os.getenv("SOCIAL_HOURS", "96"))
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recency = "day" if hours <= 24 else "week"

        max_results = int(os.getenv("SOCIAL_X_MAX_RESULTS", "20"))
        max_results = max(1, min(20, max_results))
        languages_env = (os.getenv("SOCIAL_X_LANGUAGES") or "").strip()
        language_filter = None
        if languages_env:
            language_filter = [x.strip() for x in languages_env.split(",") if x.strip()][:10]

        print(
            f"  [X] Source mode={mode} (recency={recency}, last {hours}h, max_results={max_results})..."
        )

        items: List[Dict[str, Any]] = []
        seen_status_urls = set()
        counters: Dict[str, int] = defaultdict(int)
        primary_added = 0

        if mode in {"hybrid", "perplexity_only"}:
            primary_added = self._crawl_via_perplexity(
                items=items,
                seen_status_urls=seen_status_urls,
                counters=counters,
                cutoff=cutoff,
                allowed_year=allowed_year,
                recency=recency,
                max_results=max_results,
                language_filter=language_filter,
            )

        should_run_fallback = mode == "fallback_only" or (mode == "hybrid" and primary_added == 0)
        if should_run_fallback:
            self._crawl_via_account_fallback(
                items=items,
                seen_status_urls=seen_status_urls,
                counters=counters,
                cutoff=cutoff,
                allowed_year=allowed_year,
            )

        ordered_keys = [
            "host_rejected",
            "status_url_rejected",
            "published_at_missing",
            "year_rejected",
            "freshness_rejected",
            "ai_rejected",
            "fallback_added",
        ]
        counter_summary = {k: int(counters.get(k, 0)) for k in ordered_keys if int(counters.get(k, 0)) > 0}
        print(f"  [X] Counters: {counter_summary or {}}")
        print(f"  [X] Collected {len(items)} items")
        return items[:60]

    def _crawl_via_perplexity(
        self,
        *,
        items: List[Dict[str, Any]],
        seen_status_urls: set,
        counters: Dict[str, int],
        cutoff: datetime,
        allowed_year: int,
        recency: str,
        max_results: int,
        language_filter: Optional[List[str]],
    ) -> int:
        api_key = os.getenv("PERPLEXITY_API_KEY", "").strip()
        if not api_key or not PerplexityClient:
            print("  [X] Primary search disabled: PERPLEXITY_API_KEY not set or client unavailable")
            return 0

        client = PerplexityClient(api_key=api_key)
        if not client.is_available():
            print("  [X] Primary search disabled: Perplexity client unavailable")
            return 0

        print("  [X] Primary: Perplexity query path")
        total_added = 0

        for query in self.QUERIES:
            query_key = (query or "").replace("\n", " ")
            try:
                results = client.search(
                    query=query,
                    max_results=max_results,
                    country="US",
                    language_filter=language_filter,
                    domain_filter=["x.com", "twitter.com", "mobile.twitter.com"],
                    recency_filter=recency,
                    max_tokens_per_page=1024,
                )
            except Exception as exc:
                print(f"    ⚠ Search failed: {exc}")
                continue

            total = len(results)
            status_ok = 0
            fresh_ok = 0
            ai_ok = 0
            added = 0

            for r in results:
                raw_url = (r.url or "").strip()
                if not raw_url:
                    continue

                status_check = self._status_url_check(raw_url)
                if status_check != "ok":
                    counters[status_check] += 1
                    continue

                handle, tweet_id = _extract_handle_and_id(raw_url)
                canonical = _canonical_status_url(handle, tweet_id)
                if not tweet_id or canonical in seen_status_urls:
                    continue
                seen_status_urls.add(canonical)
                status_ok += 1

                published = _parse_iso_or_date(r.date or "") or _parse_iso_or_date(getattr(r, "last_updated", "") or "")
                if not published:
                    counters["published_at_missing"] += 1
                    continue
                if published.year != allowed_year:
                    counters["year_rejected"] += 1
                    continue
                if published < cutoff:
                    counters["freshness_rejected"] += 1
                    continue
                fresh_ok += 1

                title = (r.title or "").strip()
                snippet = (r.snippet or "").strip()
                text = f"{title} {snippet}".lower()
                if not self._is_ai_relevant(text):
                    counters["ai_rejected"] += 1
                    continue
                ai_ok += 1

                items.append(
                    self._build_item(
                        title=title,
                        description=snippet or title,
                        website=canonical,
                        published=published,
                        query=query,
                        author_handle=handle,
                        tweet_id=tweet_id,
                    )
                )
                added += 1
                total_added += 1

            print(
                f"    • {query_key[:70]}... → results={total}, status={status_ok}, fresh={fresh_ok}, ai={ai_ok}, added={added}"
            )

        return total_added

    def _crawl_via_account_fallback(
        self,
        *,
        items: List[Dict[str, Any]],
        seen_status_urls: set,
        counters: Dict[str, int],
        cutoff: datetime,
        allowed_year: int,
    ) -> None:
        accounts, accounts_source = load_x_accounts_with_source()
        if not accounts:
            print("  [X] Fallback skipped: no accounts configured")
            return

        cfg = load_x_fallback_config()
        timeline_provider = str(cfg.get("timeline_provider") or "r_jina")
        tweet_provider = str(cfg.get("tweet_provider") or "x_syndication")
        max_status = int(cfg.get("max_status_per_account") or 5)
        timeout = int(cfg.get("request_timeout_seconds") or 20)

        print(
            f"  [X] Fallback: account watchlist path (accounts={len(accounts)}, source={accounts_source}, "
            f"timeline={timeline_provider}, tweet={tweet_provider})"
        )

        for account in accounts[:50]:
            handle = (account or "").strip().lstrip("@")
            if not handle:
                continue
            try:
                timeline_text = self._fetch_account_timeline_markdown(handle=handle, timeout=timeout)
            except Exception as exc:
                print(f"    ⚠ Fallback timeline failed @{handle}: {exc}")
                continue

            status_urls = self._extract_status_urls_from_timeline(
                timeline_text,
                account=handle,
                max_items=max_status,
            )
            if not status_urls:
                continue

            account_added = 0
            for status_url in status_urls:
                cleaned = _sanitize_status_url(status_url)
                status_check = self._status_url_check(cleaned)
                if status_check != "ok":
                    counters[status_check] += 1
                    continue

                url_handle, tweet_id = _extract_handle_and_id(cleaned)
                canonical = _canonical_status_url(url_handle, tweet_id)
                if not tweet_id or canonical in seen_status_urls:
                    continue
                seen_status_urls.add(canonical)

                payload = self._fetch_tweet_payload(tweet_id=tweet_id, timeout=timeout)
                created_at = str(payload.get("created_at") or "")
                published = _parse_iso_or_date(created_at)
                if not published:
                    counters["published_at_missing"] += 1
                    continue
                if published.year != allowed_year:
                    counters["year_rejected"] += 1
                    continue
                if published < cutoff:
                    counters["freshness_rejected"] += 1
                    continue

                text = str(payload.get("text") or "").strip()
                if not self._is_ai_relevant(text.lower()):
                    counters["ai_rejected"] += 1
                    continue

                user = payload.get("user") if isinstance(payload.get("user"), dict) else {}
                author_handle = str((user or {}).get("screen_name") or url_handle or handle).strip().lstrip("@")
                title = (text[:90] + "...") if len(text) > 90 else (text or f"X post by @{author_handle}")

                items.append(
                    self._build_item(
                        title=title,
                        description=text or title,
                        website=canonical,
                        published=published,
                        query=f"account_fallback:{handle}",
                        author_handle=author_handle,
                        tweet_id=tweet_id,
                    )
                )
                account_added += 1
                counters["fallback_added"] += 1

            if account_added:
                print(f"    • @{handle} → statuses={len(status_urls)}, added={account_added}")

    def _fetch_account_timeline_markdown(self, *, handle: str, timeout: int) -> str:
        urls = [
            f"https://r.jina.ai/http://x.com/{handle}",
            f"https://r.jina.ai/http://twitter.com/{handle}",
        ]
        last_error: Optional[Exception] = None
        for url in urls:
            try:
                resp = self.session.get(url, timeout=timeout)
                resp.raise_for_status()
                text = resp.text or ""
                if text.strip():
                    return text
            except Exception as exc:
                last_error = exc
                continue
        if last_error:
            raise last_error
        raise RuntimeError("empty timeline response")

    def _fetch_tweet_payload(self, *, tweet_id: str, timeout: int) -> Dict[str, Any]:
        url = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&token=a"
        try:
            resp = self.session.get(url, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return {}
        if isinstance(data, dict):
            return data
        return {}

    @staticmethod
    def _extract_status_urls_from_timeline(text: str, *, account: str, max_items: int) -> List[str]:
        out: List[str] = []
        seen = set()
        expected = (account or "").strip().lstrip("@").lower()

        for raw in STATUS_URL_PATTERN.findall(text or ""):
            cleaned = _sanitize_status_url(raw)
            handle, tweet_id = _extract_handle_and_id(cleaned)
            if not tweet_id:
                continue
            if expected and handle and handle.lower() != expected:
                continue
            canonical = _canonical_status_url(handle, tweet_id)
            if canonical in seen:
                continue
            seen.add(canonical)
            out.append(canonical)
            if len(out) >= max_items:
                break
        return out

    @staticmethod
    def _is_ai_relevant(text: str) -> bool:
        lower = (text or "").lower()
        return any(k in lower for k in AI_KEYWORDS)

    def _build_item(
        self,
        *,
        title: str,
        description: str,
        website: str,
        published: datetime,
        query: str,
        author_handle: str,
        tweet_id: str,
    ) -> Dict[str, Any]:
        clean_title = (title or "X post").strip()
        clean_description = re.sub(r"\s+", " ", (description or clean_title)).strip()[:240]
        categories = _infer_categories(f"{clean_title} {clean_description}".lower())

        return self.create_product(
            name=clean_title[:120],
            description=clean_description,
            logo_url="",
            website=website,
            categories=categories,
            weekly_users=0,
            trending_score=78,
            source="x",
            published_at=_to_iso(published),
            extra={
                "author_handle": (author_handle or "").strip().lstrip("@"),
                "tweet_id": tweet_id,
                "query": query,
                "source_type": "x",
            },
        )

    @staticmethod
    def _status_url_check(url: str) -> str:
        try:
            parsed = urlparse(url)
            host = (parsed.netloc or "").lower()
            if host.startswith("www."):
                host = host[4:]
            if host not in {"x.com", "twitter.com", "mobile.twitter.com"}:
                return "host_rejected"

            path = parsed.path or ""
            if re.search(r"/[^/]+/status/\d+", path):
                return "ok"
            if re.search(r"/i/web/status/\d+", path):
                return "ok"
            if re.search(r"/i/status/\d+", path):
                return "ok"
            return "status_url_rejected"
        except Exception:
            return "status_url_rejected"

    @staticmethod
    def _is_status_url(url: str) -> bool:
        return XSpider._status_url_check(url) == "ok"
