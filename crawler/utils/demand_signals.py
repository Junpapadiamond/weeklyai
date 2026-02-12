#!/usr/bin/env python3
"""
Demand signal utilities (V1)

Signals:
- Hacker News comment depth and community verdict
- X non-official mention volume (strict official-handle mapping)
"""

from __future__ import annotations

import html
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

try:
    from utils.perplexity_client import PerplexityClient
except Exception:  # pragma: no cover - runtime fallback
    PerplexityClient = None  # type: ignore


HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"
HN_ITEM_URL = "https://hn.algolia.com/api/v1/items/{item_id}"

STATUS_URL_PATTERN = re.compile(
    r"https://(?:x|twitter|mobile\.twitter)\.com/(?:[A-Za-z0-9_]+/status/\d+|i/(?:web/)?status/\d+)",
    re.IGNORECASE,
)

_SENTIMENT_OPTIONS = {"positive", "mixed", "negative", "neutral"}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _strip_html(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = html.unescape(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _normalize_name_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _normalize_domain(url: str) -> str:
    if not url:
        return ""
    raw = str(url).strip()
    if not raw:
        return ""
    if not raw.startswith(("http://", "https://")) and "." in raw:
        raw = f"https://{raw}"
    try:
        parsed = urlparse(raw)
        host = (parsed.netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        host = host.split(":")[0]
        return host
    except Exception:
        return ""


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value)))
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value))
    except Exception:
        return default


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

        return handle.strip().lstrip("@"), tweet_id.strip()
    except Exception:
        return "", ""


def _canonical_status_url(handle: str, tweet_id: str) -> str:
    if not tweet_id:
        return ""
    if handle:
        return f"https://x.com/{handle}/status/{tweet_id}"
    return f"https://x.com/i/web/status/{tweet_id}"


def _extract_status_url(url: str) -> str:
    if not url:
        return ""
    match = STATUS_URL_PATTERN.search(url)
    if not match:
        return ""
    raw = match.group(0).strip().rstrip(".,;:!?)\"]'\"")
    handle, tweet_id = _extract_handle_and_id(raw)
    return _canonical_status_url(handle, tweet_id)


def _split_sentences(text: str) -> List[str]:
    if not text:
        return []
    parts = re.split(r"(?<=[。！？.!?])\s+", text.strip())
    out = []
    for p in parts:
        normalized = p.strip()
        if normalized:
            out.append(normalized)
    return out


def ensure_three_sentences(summary: str) -> str:
    fallback = [
        "社区讨论集中在产品价值与实际场景。",
        "用户反馈既包含认可，也提出了执行层面的质疑。",
        "对 PM 来说，关键是验证需求强度与可持续增长。",
    ]

    sentences = _split_sentences(summary)
    if len(sentences) >= 3:
        sentences = sentences[:3]
    else:
        while len(sentences) < 3:
            sentences.append(fallback[len(sentences)])

    normalized: List[str] = []
    for s in sentences:
        if re.search(r"[。！？.!?]$", s):
            normalized.append(s)
        else:
            normalized.append(f"{s}。")
    return " ".join(normalized)


def compute_hn_engagement_depth(points: int, comments: int) -> float:
    return round(float(comments) / max(float(points), 1.0), 4)


def is_hn_controversial(points: int, comments: int, ratio: Optional[float] = None) -> bool:
    if ratio is None:
        ratio = compute_hn_engagement_depth(points, comments)
    return comments >= 20 and ratio >= 1.0


def summarize_hn_comments(comments: List[str], llm_client: Any = None) -> Dict[str, Any]:
    if not comments:
        return {
            "summary": ensure_three_sentences("HN 暂无足够评论样本用于形成社区结论。"),
            "sentiment": "neutral",
            "confidence": 0.3,
        }

    cleaned = []
    for c in comments[:10]:
        text = _strip_html(c)
        if text:
            cleaned.append(text[:600])

    if not cleaned:
        return {
            "summary": ensure_three_sentences("HN 评论样本文本不可用，暂无法形成稳定判断。"),
            "sentiment": "neutral",
            "confidence": 0.25,
        }

    if llm_client:
        prompt = (
            "你是 WeeklyAI 的社区分析助手。根据以下 Hacker News 评论，输出 JSON："
            '{"summary":"三句话总结","sentiment":"positive|mixed|negative|neutral","confidence":0-1}。'
            "要求：summary 必须恰好三句话，不要夸张，不要编造数据。\n\n"
            + "\n".join(f"- {c}" for c in cleaned)
        )
        try:
            parsed = llm_client.analyze(prompt=prompt, temperature=0.2, max_tokens=512)
            if isinstance(parsed, dict):
                sentiment = str(parsed.get("sentiment") or "neutral").strip().lower()
                if sentiment not in _SENTIMENT_OPTIONS:
                    sentiment = "neutral"
                confidence = _clamp01(_safe_float(parsed.get("confidence"), 0.55))
                summary = ensure_three_sentences(str(parsed.get("summary") or ""))
                return {
                    "summary": summary,
                    "sentiment": sentiment,
                    "confidence": round(confidence, 2),
                }
        except Exception:
            pass

    positive_terms = {
        "great", "love", "useful", "impressive", "promising", "good", "amazing",
        "喜欢", "有用", "靠谱", "强", "看好", "不错", "惊艳",
    }
    negative_terms = {
        "bad", "hate", "weak", "overhyped", "problem", "issue", "worse",
        "差", "不行", "吹过", "问题", "担心", "质疑", "失望",
    }

    text_blob = " ".join(cleaned).lower()
    pos = sum(1 for t in positive_terms if t in text_blob)
    neg = sum(1 for t in negative_terms if t in text_blob)

    if pos == 0 and neg == 0:
        sentiment = "neutral"
        confidence = 0.45
    elif abs(pos - neg) <= 2:
        sentiment = "mixed"
        confidence = 0.6
    elif pos > neg:
        sentiment = "positive"
        confidence = 0.66
    else:
        sentiment = "negative"
        confidence = 0.66

    summary = ensure_three_sentences(
        "社区重点讨论了产品价值与落地细节。"
        f"评论情绪整体偏{('正向' if sentiment == 'positive' else '负向' if sentiment == 'negative' else '中性分歧')}，"
        "并反复提及可用性与真实场景。"
        "这类反馈可用于判断短期需求强度是否能转化为持续增长。"
    )

    return {
        "summary": summary,
        "sentiment": sentiment,
        "confidence": round(confidence, 2),
    }


def _empty_hn(window_days: int) -> Dict[str, Any]:
    return {
        "story_count": 0,
        "top_story_id": "",
        "points": 0,
        "comments": 0,
        "engagement_depth_ratio": 0.0,
        "is_controversial": False,
        "top_comments_sample": [],
        "status": "ok",
        "window_days": window_days,
    }


def _empty_x(window_days: int) -> Dict[str, Any]:
    return {
        "official_handle": "",
        "non_official_mentions_7d": 0,
        "unique_authors_7d": 0,
        "status_urls_sample": [],
        "query": "",
        "status": "ok",
        "window_days": window_days,
    }


def _extract_comment_samples(node: Dict[str, Any], limit: int = 10) -> List[str]:
    out: List[str] = []
    queue: List[Dict[str, Any]] = [node]

    while queue and len(out) < limit:
        current = queue.pop(0)
        children = current.get("children") or []
        if isinstance(children, list):
            for child in children:
                if not isinstance(child, dict):
                    continue
                text = _strip_html(str(child.get("text") or ""))
                if text and len(out) < limit:
                    out.append(text[:700])
                queue.append(child)
    return out[:limit]


def collect_hn_signal(
    product_name: str,
    website: str,
    window_days: int,
    session: Optional[requests.Session] = None,
    llm_client: Any = None,
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    signal = _empty_hn(window_days=window_days)
    product_name = (product_name or "").strip()
    if not product_name:
        signal["status"] = "skipped"
        signal["skipped_reason"] = "missing_product_name"
        return signal, None

    sess = session or requests.Session()
    since_ts = int((_now_utc() - timedelta(days=max(window_days, 1))).timestamp())

    def _fetch_hits(query: str) -> List[Dict[str, Any]]:
        params = {
            "query": query,
            "tags": "story",
            "hitsPerPage": 30,
            "numericFilters": f"created_at_i>{since_ts}",
        }
        resp = sess.get(HN_SEARCH_URL, params=params, timeout=12)
        resp.raise_for_status()
        data = resp.json()
        return data.get("hits", []) if isinstance(data, dict) else []

    try:
        hits = _fetch_hits(product_name)
    except Exception as exc:
        signal["status"] = "error"
        signal["error"] = f"hn_search_failed:{exc}"
        return signal, None

    domain = _normalize_domain(website)
    name_key = _normalize_name_key(product_name)
    matched: List[Dict[str, Any]] = []

    for hit in hits:
        title = str(hit.get("title") or "")
        text = str(hit.get("story_text") or "")
        url = str(hit.get("url") or "")
        merged = f"{title} {text} {url}".lower()

        title_key = _normalize_name_key(title)
        url_domain = _normalize_domain(url)

        name_match = bool(name_key and (name_key in _normalize_name_key(merged) or name_key in title_key))
        domain_match = bool(domain and (domain == url_domain or domain in merged))

        if name_match or domain_match:
            matched.append(hit)

    if not matched:
        return signal, None

    matched.sort(
        key=lambda x: (
            _safe_int(x.get("num_comments"), 0),
            _safe_int(x.get("points"), 0),
            _safe_int(x.get("created_at_i"), 0),
        ),
        reverse=True,
    )

    top = matched[0]
    points = _safe_int(top.get("points"), 0)
    comments = _safe_int(top.get("num_comments"), 0)
    ratio = compute_hn_engagement_depth(points, comments)
    top_story_id = str(top.get("objectID") or "").strip()

    signal.update(
        {
            "story_count": len(matched),
            "top_story_id": top_story_id,
            "points": points,
            "comments": comments,
            "engagement_depth_ratio": ratio,
            "is_controversial": is_hn_controversial(points, comments, ratio),
        }
    )

    comment_samples: List[str] = []
    if top_story_id:
        try:
            item_resp = sess.get(HN_ITEM_URL.format(item_id=top_story_id), timeout=12)
            item_resp.raise_for_status()
            item_data = item_resp.json()
            if isinstance(item_data, dict):
                comment_samples = _extract_comment_samples(item_data, limit=10)
        except Exception as exc:
            signal["comment_fetch_error"] = str(exc)

    signal["top_comments_sample"] = comment_samples

    verdict_payload = summarize_hn_comments(comment_samples, llm_client=llm_client)
    community_verdict = {
        "source": "hackernews",
        "window_days": window_days,
        "summary": verdict_payload["summary"],
        "sentiment": verdict_payload["sentiment"],
        "confidence": verdict_payload["confidence"],
    }

    return signal, community_verdict


def load_official_handle_map(path: str) -> Dict[str, Dict[str, str]]:
    out = {"by_domain": {}, "by_name": {}}
    if not path or not os.path.exists(path):
        return out

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return out

    if not isinstance(data, dict):
        return out

    by_domain = data.get("by_domain") if isinstance(data.get("by_domain"), dict) else {}
    by_name = data.get("by_name") if isinstance(data.get("by_name"), dict) else {}

    for k, v in by_domain.items():
        key = _normalize_domain(str(k))
        val = str(v or "").strip().lstrip("@")
        if key and val:
            out["by_domain"][key] = val

    for k, v in by_name.items():
        key = _normalize_name_key(str(k))
        val = str(v or "").strip().lstrip("@")
        if key and val:
            out["by_name"][key] = val

    # Backward compatible flat map: {"cursor.com": "cursor_ai"}
    if not out["by_domain"] and not out["by_name"]:
        for k, v in data.items():
            if not isinstance(v, str):
                continue
            key_domain = _normalize_domain(str(k))
            key_name = _normalize_name_key(str(k))
            value = v.strip().lstrip("@")
            if key_domain and value:
                out["by_domain"][key_domain] = value
            elif key_name and value:
                out["by_name"][key_name] = value

    return out


def resolve_official_handle(product_name: str, website: str, mapping: Dict[str, Dict[str, str]]) -> str:
    mapping = mapping or {"by_domain": {}, "by_name": {}}
    by_domain = mapping.get("by_domain") or {}
    by_name = mapping.get("by_name") or {}

    domain = _normalize_domain(website)
    if domain and domain in by_domain:
        return str(by_domain[domain]).strip().lstrip("@")

    name_key = _normalize_name_key(product_name)
    if name_key and name_key in by_name:
        return str(by_name[name_key]).strip().lstrip("@")

    return ""


def collect_x_non_official_signal(
    *,
    product_name: str,
    website: str,
    official_handle: str,
    window_days: int,
    perplexity_client: Any = None,
    strict_official: bool = True,
) -> Dict[str, Any]:
    signal = _empty_x(window_days=window_days)
    signal["official_handle"] = (official_handle or "").strip().lstrip("@")

    if strict_official and not signal["official_handle"]:
        signal["status"] = "skipped"
        signal["skipped_reason"] = "official_handle_missing"
        return signal

    if not perplexity_client:
        signal["status"] = "skipped"
        signal["skipped_reason"] = "perplexity_unavailable"
        return signal

    domain = _normalize_domain(website)
    if domain:
        query = (
            f'("{product_name}" OR "{domain}") '
            f'(site:x.com OR site:twitter.com) -from:{signal["official_handle"]}'
        )
    else:
        query = (
            f'"{product_name}" (site:x.com OR site:twitter.com) '
            f'-from:{signal["official_handle"]}'
        )

    signal["query"] = query

    recency_filter = "day" if window_days <= 1 else "week"
    try:
        results = perplexity_client.search(
            query=query,
            max_results=20,
            country="US",
            domain_filter=["x.com", "twitter.com", "mobile.twitter.com"],
            recency_filter=recency_filter,
            max_tokens_per_page=512,
        )
    except Exception as exc:
        signal["status"] = "error"
        signal["error"] = f"x_search_failed:{exc}"
        return signal

    official = signal["official_handle"].lower()
    seen_urls = set()
    authors = set()

    for item in results or []:
        raw_url = str(getattr(item, "url", "") or "")
        status_url = _extract_status_url(raw_url)
        if not status_url:
            continue

        handle, tweet_id = _extract_handle_and_id(status_url)
        if not tweet_id:
            continue
        if handle and handle.lower() == official:
            continue

        if status_url in seen_urls:
            continue
        seen_urls.add(status_url)

        if handle:
            authors.add(handle.lower())

    signal["non_official_mentions_7d"] = len(seen_urls)
    signal["unique_authors_7d"] = len(authors)
    signal["status_urls_sample"] = sorted(seen_urls)[:5]
    return signal


def calculate_demand_score(hn_signal: Dict[str, Any], x_signal: Dict[str, Any]) -> Tuple[float, str]:
    hn_ratio_score = min(_safe_float(hn_signal.get("engagement_depth_ratio"), 0.0) / 1.5, 1.0)
    hn_comment_score = min(_safe_float(hn_signal.get("comments"), 0.0) / 200.0, 1.0)
    x_mention_score = min(_safe_float(x_signal.get("non_official_mentions_7d"), 0.0) / 50.0, 1.0)
    x_author_score = min(_safe_float(x_signal.get("unique_authors_7d"), 0.0) / 30.0, 1.0)

    score = (
        0.35 * hn_ratio_score
        + 0.25 * hn_comment_score
        + 0.25 * x_mention_score
        + 0.15 * x_author_score
    )
    score = round(_clamp01(score), 4)

    if score >= 0.7:
        tier = "high"
    elif score >= 0.35:
        tier = "medium"
    else:
        tier = "low"

    return score, tier


def apply_demand_guardrail(
    llm_score: int,
    demand_payload: Dict[str, Any],
    *,
    has_strong_supply_signal: bool,
    mode: str = "medium",
) -> Tuple[int, str, str]:
    llm_score = max(1, min(5, _safe_int(llm_score, 2)))
    mode = (mode or "medium").strip().lower()

    thresholds = {
        "conservative": {"upgrade": 0.8, "downgrade": 0.15},
        "medium": {"upgrade": 0.75, "downgrade": 0.20},
        "aggressive": {"upgrade": 0.65, "downgrade": 0.25},
    }
    cfg = thresholds.get(mode, thresholds["medium"])

    score = _safe_float(demand_payload.get("demand_score_raw"), 0.0)

    hn_status = str((demand_payload.get("hn") or {}).get("status") or "")
    x_status = str((demand_payload.get("x") or {}).get("status") or "")

    # 升分允许在部分信号场景发生；降分仅在双信号可用时触发，避免数据缺失导致误伤。
    can_upgrade = (
        (_safe_int((demand_payload.get("hn") or {}).get("story_count"), 0) > 0)
        or (_safe_int((demand_payload.get("x") or {}).get("non_official_mentions_7d"), 0) > 0)
    )
    can_downgrade = hn_status == "ok" and x_status == "ok"

    if llm_score <= 3 and can_upgrade and score >= cfg["upgrade"]:
        return min(5, llm_score + 1), "upgraded", f"demand_score_raw={score:.2f} >= {cfg['upgrade']:.2f}"

    if llm_score == 5 and can_downgrade and (not has_strong_supply_signal) and score < cfg["downgrade"]:
        return 4, "downgraded", (
            f"demand_score_raw={score:.2f} < {cfg['downgrade']:.2f} and strong_supply_signal=false"
        )

    if not can_upgrade and not can_downgrade:
        return llm_score, "none", "insufficient_demand_data"

    return llm_score, "none", "threshold_not_met"


@dataclass
class DemandSignalEngine:
    window_days: int = 7
    strict_x_official: bool = True
    official_handles_path: str = ""
    perplexity_api_key: str = ""

    def __post_init__(self) -> None:
        self.window_days = max(1, int(self.window_days or 7))
        self.session = requests.Session()
        self.official_mapping = load_official_handle_map(self.official_handles_path)

        self.perplexity_client = None
        if self.perplexity_api_key and PerplexityClient:
            try:
                client = PerplexityClient(api_key=self.perplexity_api_key)
                if client.is_available():
                    self.perplexity_client = client
            except Exception:
                self.perplexity_client = None

        self._hn_cache: Dict[str, Tuple[Dict[str, Any], Optional[Dict[str, Any]]]] = {}
        self._x_cache: Dict[str, Dict[str, Any]] = {}

    def _cache_key(self, product_name: str, website: str) -> str:
        return f"{_normalize_name_key(product_name)}::{_normalize_domain(website)}"

    def collect_for_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        name = str(product.get("name") or "").strip()
        website = str(product.get("website") or "").strip()

        demand_payload = {
            "version": "v1",
            "computed_at": _to_iso(_now_utc()),
            "window_days": self.window_days,
            "hn": _empty_hn(self.window_days),
            "x": _empty_x(self.window_days),
            "demand_score_raw": 0.0,
            "demand_tier": "low",
            "guardrail_applied": "none",
            "guardrail_reason": "",
        }

        if not name:
            demand_payload["hn"]["status"] = "skipped"
            demand_payload["hn"]["skipped_reason"] = "missing_product_name"
            demand_payload["x"]["status"] = "skipped"
            demand_payload["x"]["skipped_reason"] = "missing_product_name"
            demand_payload["guardrail_reason"] = "missing_product_name"
            return {
                "demand": demand_payload,
                "community_verdict": None,
                "criteria_tags": [],
            }

        cache_key = self._cache_key(name, website)

        if cache_key in self._hn_cache:
            hn_signal, community_verdict = self._hn_cache[cache_key]
        else:
            hn_signal, community_verdict = collect_hn_signal(
                name,
                website,
                window_days=self.window_days,
                session=self.session,
                llm_client=self.perplexity_client,
            )
            self._hn_cache[cache_key] = (hn_signal, community_verdict)

        official_handle = resolve_official_handle(name, website, self.official_mapping)
        x_cache_key = f"{cache_key}::{official_handle.lower()}"

        if x_cache_key in self._x_cache:
            x_signal = self._x_cache[x_cache_key]
        else:
            x_signal = collect_x_non_official_signal(
                product_name=name,
                website=website,
                official_handle=official_handle,
                window_days=self.window_days,
                perplexity_client=self.perplexity_client,
                strict_official=self.strict_x_official,
            )
            self._x_cache[x_cache_key] = x_signal

        score, tier = calculate_demand_score(hn_signal, x_signal)

        demand_payload["hn"] = hn_signal
        demand_payload["x"] = x_signal
        demand_payload["demand_score_raw"] = score
        demand_payload["demand_tier"] = tier

        tags: List[str] = []
        if _safe_int(hn_signal.get("story_count"), 0) > 0:
            if _safe_float(hn_signal.get("engagement_depth_ratio"), 0.0) >= 0.7 or _safe_int(hn_signal.get("comments"), 0) >= 80:
                tags.append("demand_signal_hn")
        if _safe_int(x_signal.get("non_official_mentions_7d"), 0) >= 10 or _safe_int(x_signal.get("unique_authors_7d"), 0) >= 6:
            tags.append("demand_signal_x_non_official")

        return {
            "demand": demand_payload,
            "community_verdict": community_verdict,
            "criteria_tags": tags,
        }
