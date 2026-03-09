"""
X/Twitter signals spider.

Primary path:
- Perplexity Search (query-driven discovery)

Fallback path (free):
- Nitter RSS
- Browser-style timeline scraping
- Optional r.jina.ai timeline fetch
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

try:
    import feedparser

    HAS_FEEDPARSER = True
except Exception:
    HAS_FEEDPARSER = False

from .base_spider import BaseSpider
from utils.social_health import update_source_health
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
_SPIDER_DIR = os.path.dirname(os.path.abspath(__file__))
_CRAWLER_DIR = os.path.dirname(_SPIDER_DIR)
DEFAULT_X_STATE_FILE = os.path.join(_CRAWLER_DIR, "data", "x_spider_state.json")


def _truthy(value: str, default: bool = False) -> bool:
    if not value:
        return default
    raw = value.strip().lower()
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    return default


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


def _parse_feed_datetime(entry: Any) -> Optional[datetime]:
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if parsed:
        try:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
        except Exception:
            pass
    value = (entry.get("published") or entry.get("updated") or "").strip()
    return _parse_iso_or_date(value)


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _state_write_disabled() -> bool:
    return _truthy(os.getenv("X_SPIDER_DISABLE_STATE_WRITE", "false"), default=False)


def _state_file_path() -> str:
    override = (os.getenv("X_SPIDER_STATE_FILE") or "").strip()
    return override or DEFAULT_X_STATE_FILE


def _load_state() -> Dict[str, Any]:
    path = _state_file_path()
    if not os.path.exists(path):
        return {
            "last_primary_run_at": "",
            "consecutive_fallback_empty_days": 0,
            "last_fallback_run_at": "",
            "updated_at": "",
        }
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {
        "last_primary_run_at": "",
        "consecutive_fallback_empty_days": 0,
        "last_fallback_run_at": "",
        "updated_at": "",
    }


def _save_state(state: Dict[str, Any]) -> None:
    if _state_write_disabled():
        return
    path = _state_file_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = dict(state or {})
    payload["updated_at"] = _to_iso(datetime.now(timezone.utc)) or ""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _should_run_primary(
    state: Dict[str, Any],
    *,
    mode: str,
    now: datetime,
    interval_days: int,
    force_primary_after_empty: bool,
) -> Tuple[bool, str]:
    if mode == "perplexity_only":
        return True, "mode_perplexity_only"
    if mode != "hybrid":
        return False, "mode_no_primary"

    try:
        streak = int(state.get("consecutive_fallback_empty_days", 0) or 0)
    except Exception:
        streak = 0
    if force_primary_after_empty and streak >= 1:
        return True, "force_after_empty"
    if streak >= 2:
        return True, "fallback_empty_streak"

    last_primary = _parse_iso_or_date(str(state.get("last_primary_run_at") or ""))
    if not last_primary:
        return True, "no_previous_primary"

    elapsed = now - last_primary
    if elapsed.total_seconds() >= max(1, interval_days) * 86400:
        return True, "interval_elapsed"
    return False, "interval_not_elapsed"


def _extract_handle_and_id(url: str) -> Tuple[str, str]:
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
    """Collect X signals via Perplexity plus multi-provider fallback."""

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
        now_utc = datetime.now(timezone.utc)
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

        primary_interval_days = max(1, int(os.getenv("X_PRIMARY_INTERVAL_DAYS", "1")))
        force_primary_after_empty = _truthy(os.getenv("X_FORCE_PRIMARY_AFTER_EMPTY", "true"), default=True)
        state = _load_state()
        run_primary, primary_reason = _should_run_primary(
            state,
            mode=mode,
            now=now_utc,
            interval_days=primary_interval_days,
            force_primary_after_empty=force_primary_after_empty,
        )

        print(f"  [X] Source mode={mode} (recency={recency}, last {hours}h, max_results={max_results})...")
        if mode in {"hybrid", "perplexity_only"}:
            print(f"  [X] Primary interval={primary_interval_days}d, decision={run_primary} ({primary_reason})")

        items: List[Dict[str, Any]] = []
        seen_status_urls = set()
        counters: Dict[str, int] = defaultdict(int)
        provider_stats: Dict[str, Dict[str, int]] = {}
        primary_added = 0
        primary_ran = False
        fallback_ran = False
        fallback_added = 0
        fallback_attempted_accounts = 0
        fallback_success_accounts = 0

        if mode in {"hybrid", "perplexity_only"} and run_primary:
            primary_ran = True
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
        elif mode in {"hybrid", "perplexity_only"}:
            print("  [X] Primary skipped due to interval policy")

        should_run_fallback = mode == "fallback_only" or (mode == "hybrid" and primary_added == 0)
        if should_run_fallback:
            fallback_ran = True
            before = len(items)
            fallback_attempted_accounts, fallback_success_accounts = self._crawl_via_account_fallback(
                items=items,
                seen_status_urls=seen_status_urls,
                counters=counters,
                cutoff=cutoff,
                allowed_year=allowed_year,
                provider_stats=provider_stats,
            )
            fallback_added = max(0, len(items) - before)

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

        if primary_ran:
            state["last_primary_run_at"] = _to_iso(now_utc) or ""
            state["consecutive_fallback_empty_days"] = 0
        if fallback_ran:
            state["last_fallback_run_at"] = _to_iso(now_utc) or ""
            try:
                current_streak = int(state.get("consecutive_fallback_empty_days", 0) or 0)
            except Exception:
                current_streak = 0
            state["consecutive_fallback_empty_days"] = 0 if fallback_added > 0 else current_streak + 1
        _save_state(state)

        fallback_hit_rate = 0.0
        if fallback_attempted_accounts > 0:
            fallback_hit_rate = round(float(fallback_success_accounts) / float(fallback_attempted_accounts), 4)
        update_source_health(
            "x",
            {
                "count": len(items),
                "mode": mode,
                "primary_ran": bool(primary_ran),
                "primary_reason": primary_reason,
                "primary_added": int(primary_added),
                "fallback_ran": bool(fallback_ran),
                "fallback_added": int(fallback_added),
                "fallback_attempted_accounts": int(fallback_attempted_accounts),
                "fallback_success_accounts": int(fallback_success_accounts),
                "fallback_hit_rate": fallback_hit_rate,
                "errors": {k: int(v) for k, v in counter_summary.items()},
                "providers": provider_stats,
            },
        )
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
        provider_stats: Dict[str, Dict[str, int]],
    ) -> Tuple[int, int]:
        accounts, accounts_source = load_x_accounts_with_source()
        if not accounts:
            print("  [X] Fallback skipped: no accounts configured")
            return 0, 0

        cfg = load_x_fallback_config()
        timeline_provider = str(cfg.get("timeline_provider") or "auto").strip().lower()
        tweet_provider = str(cfg.get("tweet_provider") or "x_syndication").strip().lower()
        max_status = int(cfg.get("max_status_per_account") or 5)
        timeout = int(cfg.get("request_timeout_seconds") or 20)
        nitter_instances = list(cfg.get("nitter_instances") or [])
        browser_enabled = bool(cfg.get("browser_enabled", True))

        print(
            f"  [X] Fallback: account watchlist path (accounts={len(accounts)}, source={accounts_source}, "
            f"timeline={timeline_provider}, tweet={tweet_provider}, browser={browser_enabled})"
        )

        attempted_accounts = 0
        success_accounts = 0
        for account in accounts[:50]:
            handle = (account or "").strip().lstrip("@")
            if not handle:
                continue
            attempted_accounts += 1
            candidates, provider_used, errors = self._fetch_account_candidates(
                handle=handle,
                timeline_provider=timeline_provider,
                max_status=max_status,
                timeout=timeout,
                nitter_instances=nitter_instances,
                browser_enabled=browser_enabled,
            )

            for provider_name, err_count in errors.items():
                stats = provider_stats.setdefault(provider_name, {"ok": 0, "error": 0})
                stats["error"] += int(err_count)

            if not candidates:
                continue
            provider_stats.setdefault(provider_used, {"ok": 0, "error": 0})
            provider_stats[provider_used]["ok"] += 1

            account_added = 0
            for candidate in candidates:
                cleaned = _sanitize_status_url(str(candidate.get("url") or ""))
                status_check = self._status_url_check(cleaned)
                if status_check != "ok":
                    counters[status_check] += 1
                    continue

                url_handle, tweet_id = _extract_handle_and_id(cleaned)
                canonical = _canonical_status_url(url_handle, tweet_id)
                if not tweet_id or canonical in seen_status_urls:
                    continue
                seen_status_urls.add(canonical)

                resolved = self._resolve_candidate_payload(
                    candidate=candidate,
                    tweet_id=tweet_id,
                    fallback_handle=handle,
                    fallback_url_handle=url_handle,
                    tweet_provider=tweet_provider,
                    timeout=timeout,
                    provider=provider_used,
                )
                published = resolved.get("published")
                if not isinstance(published, datetime):
                    counters["published_at_missing"] += 1
                    continue
                if published.year != allowed_year:
                    counters["year_rejected"] += 1
                    continue
                if published < cutoff:
                    counters["freshness_rejected"] += 1
                    continue

                text = str(resolved.get("text") or "").strip()
                if not self._is_ai_relevant(text.lower()):
                    counters["ai_rejected"] += 1
                    continue

                author_handle = str(resolved.get("author_handle") or handle).strip().lstrip("@")
                title = str(resolved.get("title") or "").strip()
                if not title:
                    title = (text[:90] + "...") if len(text) > 90 else (text or f"X post by @{author_handle}")

                items.append(
                    self._build_item(
                        title=title,
                        description=text or title,
                        website=canonical,
                        published=published,
                        query=f"account_fallback:{handle}:{provider_used}",
                        author_handle=author_handle,
                        tweet_id=tweet_id,
                    )
                )
                account_added += 1
                counters["fallback_added"] += 1

            if account_added:
                success_accounts += 1
                print(f"    • @{handle} ({provider_used}) → candidates={len(candidates)}, added={account_added}")
        return attempted_accounts, success_accounts

    def _fetch_account_candidates(
        self,
        *,
        handle: str,
        timeline_provider: str,
        max_status: int,
        timeout: int,
        nitter_instances: List[str],
        browser_enabled: bool,
    ) -> Tuple[List[Dict[str, Any]], str, Dict[str, int]]:
        providers = self._provider_order(timeline_provider=timeline_provider, browser_enabled=browser_enabled)
        errors: Dict[str, int] = defaultdict(int)

        for provider in providers:
            try:
                if provider == "nitter_rss":
                    candidates = self._fetch_account_candidates_via_nitter(
                        handle=handle,
                        max_status=max_status,
                        timeout=timeout,
                        instances=nitter_instances,
                    )
                elif provider == "r_jina":
                    candidates = self._fetch_account_candidates_via_r_jina(
                        handle=handle,
                        max_status=max_status,
                        timeout=timeout,
                    )
                elif provider == "browser":
                    candidates = self._fetch_account_candidates_via_browser(
                        handle=handle,
                        max_status=max_status,
                        timeout=timeout,
                    )
                else:
                    candidates = []
            except Exception:
                candidates = []

            if candidates:
                return candidates, provider, dict(errors)
            errors[provider] += 1
        return [], "none", dict(errors)

    @staticmethod
    def _provider_order(*, timeline_provider: str, browser_enabled: bool) -> List[str]:
        provider = (timeline_provider or "auto").strip().lower()
        if provider == "nitter_rss":
            ordered = ["nitter_rss", "browser"]
        elif provider == "r_jina":
            ordered = ["r_jina", "nitter_rss", "browser"]
        elif provider == "browser":
            ordered = ["browser"]
        else:
            ordered = ["nitter_rss", "browser"]

        if not browser_enabled:
            ordered = [x for x in ordered if x != "browser"]
        out = []
        seen = set()
        for p in ordered:
            if p not in seen:
                out.append(p)
                seen.add(p)
        return out

    def _fetch_account_candidates_via_nitter(
        self,
        *,
        handle: str,
        max_status: int,
        timeout: int,
        instances: List[str],
    ) -> List[Dict[str, Any]]:
        if not HAS_FEEDPARSER:
            return []
        bases = [str(x).strip().rstrip("/") for x in instances if str(x).strip()]
        if not bases:
            bases = ["https://nitter.net"]

        for base in bases[:5]:
            rss_url = f"{base}/{handle}/rss"
            try:
                resp = self.fetch(rss_url, timeout=timeout)
            except Exception:
                continue

            feed = feedparser.parse(resp.content)
            out: List[Dict[str, Any]] = []
            seen = set()
            for entry in feed.entries[: max_status * 2]:
                link = str(entry.get("link") or "").strip()
                raw_title = str(entry.get("title") or "").strip()
                snippet = _strip_html(str(entry.get("summary") or ""))
                published = _parse_feed_datetime(entry)
                if not link:
                    continue
                url_handle, tweet_id = _extract_handle_and_id(link)
                canonical = _canonical_status_url(url_handle, tweet_id)
                if not tweet_id or canonical in seen:
                    continue
                seen.add(canonical)
                title = re.sub(r"^[^:]+:\s*", "", raw_title).strip()
                out.append(
                    {
                        "url": canonical,
                        "title": title or raw_title,
                        "snippet": snippet,
                        "published_at": _to_iso(published),
                        "author_handle": handle,
                    }
                )
                if len(out) >= max_status:
                    break
            if out:
                return out
        return []

    def _fetch_account_candidates_via_r_jina(
        self,
        *,
        handle: str,
        max_status: int,
        timeout: int,
    ) -> List[Dict[str, Any]]:
        timeline_text = self._fetch_account_timeline_markdown(handle=handle, timeout=timeout)
        urls = self._extract_status_urls_from_timeline(
            timeline_text,
            account=handle,
            max_items=max_status,
        )
        return [{"url": x, "title": "", "snippet": "", "published_at": "", "author_handle": handle} for x in urls]

    def _fetch_account_candidates_via_browser(
        self,
        *,
        handle: str,
        max_status: int,
        timeout: int,
    ) -> List[Dict[str, Any]]:
        urls = [
            f"https://x.com/{handle}",
            f"https://twitter.com/{handle}",
        ]
        for url in urls:
            try:
                resp = self.fetch(url, timeout=timeout)
            except Exception:
                continue
            status_urls = self._extract_status_urls_from_timeline(
                resp.text or "",
                account=handle,
                max_items=max_status,
            )
            if status_urls:
                return [
                    {"url": x, "title": "", "snippet": "", "published_at": "", "author_handle": handle}
                    for x in status_urls
                ]
        return []

    def _resolve_candidate_payload(
        self,
        *,
        candidate: Dict[str, Any],
        tweet_id: str,
        fallback_handle: str,
        fallback_url_handle: str,
        tweet_provider: str,
        timeout: int,
        provider: str,
    ) -> Dict[str, Any]:
        title = str(candidate.get("title") or "").strip()
        text = str(candidate.get("snippet") or "").strip()
        author_handle = str(candidate.get("author_handle") or fallback_url_handle or fallback_handle).strip().lstrip("@")
        published = _parse_iso_or_date(str(candidate.get("published_at") or ""))

        use_syndication = tweet_provider in {"x_syndication", "auto"}
        if use_syndication:
            payload = self._fetch_tweet_payload(tweet_id=tweet_id, timeout=timeout)
            if payload:
                created_at = str(payload.get("created_at") or "")
                payload_published = _parse_iso_or_date(created_at)
                if payload_published:
                    published = payload_published
                payload_text = str(payload.get("text") or "").strip()
                if payload_text:
                    text = payload_text
                user = payload.get("user") if isinstance(payload.get("user"), dict) else {}
                author = str((user or {}).get("screen_name") or "").strip().lstrip("@")
                if author:
                    author_handle = author

        if not published:
            published = _parse_iso_or_date(str(candidate.get("published_at") or ""))
        if not title:
            title = (text[:90] + "...") if len(text) > 90 else text
        return {
            "title": title,
            "text": text,
            "published": published,
            "author_handle": author_handle,
            "provider": provider,
        }

    def _fetch_account_timeline_markdown(self, *, handle: str, timeout: int) -> str:
        urls = [
            f"https://r.jina.ai/http://x.com/{handle}",
            f"https://r.jina.ai/http://twitter.com/{handle}",
        ]
        last_error: Optional[Exception] = None
        for url in urls:
            try:
                resp = self.fetch(url, timeout=timeout)
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
            resp = self.fetch(url, timeout=timeout)
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
