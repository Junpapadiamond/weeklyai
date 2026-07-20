#!/usr/bin/env python3
"""
WeeklyAI v2 search prompt/query module.

Fish for weird products and surprising launches, not press releases. Funding is
kept as a small residual side-channel for context, never as the main pond.
"""

from datetime import datetime
from typing import Optional
import random


def get_current_year() -> int:
    return datetime.now().year


def get_current_month() -> str:
    return datetime.now().strftime("%Y-%m")


WEIRD_OBJECTS = [
    "pendant",
    "frame",
    "plant",
    "mirror",
    "lamp",
    "sticker",
    "plush",
    "collar",
    "ring",
    "glasses",
    "doorbell",
    "badge",
]

UNUSUAL_CATEGORIES = [
    "hardware",
    "wearable",
    "home device",
    "companion",
    "robot",
    "agent",
    "ambient",
    "voice device",
    "local first",
]

WEIRDNESS_PONDS = {
    "global": [
        *[f"site:kickstarter.com AI {obj} {{year}}" for obj in WEIRD_OBJECTS],
        "site:indiegogo.com AI device {year}",
        "site:indiegogo.com AI wearable {year}",
        "site:producthunt.com AI {category} {year}",
        "site:news.ycombinator.com Show HN AI {year}",
        "site:news.ycombinator.com AI hardware {year}",
    ],
    "cn": [
        "site:makuake.com AI {year}",
        "site:zhongchou.modian.com AI {year}",
        "site:youpin.mi.com 智能 AI {year}",
        "site:36kr.com AI硬件 创新形态 {year}",
        "site:36kr.com AI 可穿戴 创新 {year}",
        "site:36kr.com 智能硬件 新形态 {year}",
        "AI 盆栽 相框 镜子 台灯 智能硬件 {year}",
    ],
    "jp": [
        "site:makuake.com AI {year}",
        "site:campfire.jp AI {year}",
        "site:producthunt.com AI Japan hardware {year}",
        "AI ウェアラブル デバイス Makuake {year}",
    ],
}

BIG_LAB_RELEASE_RADAR = {
    "global": [
        "site:openai.com/blog AI product launch {year}",
        "site:anthropic.com/news Claude new capability {year}",
        "site:deepmind.google/discover AI product {year}",
        "site:ai.meta.com AI product release {year}",
        "site:apple.com/newsroom AI {year}",
        "site:simonwillison.net AI agent launch {year}",
        "site:news.ycombinator.com OpenAI Anthropic Google AI launch {year}",
    ],
    "cn": [
        "site:mi.com newsroom AI {year}",
        "site:tencent.com AI 新能力 {year}",
        "site:alibabacloud.com news AI {year}",
        "site:bytedance.com news AI {year}",
        "site:36kr.com 大厂 AI 新能力 {year}",
    ],
}

FUNDING_SIDE_CHANNELS = {
    "us": [
        "site:techcrunch.com AI startup funding unusual product {year}",
        "site:venturebeat.com AI startup launches funding product {year}",
        "AI startup funding weird hardware product {year}",
    ],
    "cn": [
        "site:36kr.com AI融资 创新产品 {year}",
        "site:tmtpost.com 人工智能 融资 新产品 {year}",
        "AI创业公司 融资 创新硬件 {year}",
    ],
    "eu": [
        "site:sifted.eu AI funding product launch {year}",
        "site:tech.eu AI startup product launch {year}",
    ],
    "jp": [
        "Japan AI startup funding product launch {year}",
        "site:thebridge.jp AI 資金調達 product {year}",
    ],
    "kr": [
        "Korean AI startup funding product launch {year}",
        "site:platum.kr AI 스타트업 제품 {year}",
    ],
    "sea": [
        "Southeast Asia AI startup funding product launch {year}",
        "site:techinasia.com AI startup product launch {year}",
    ],
}

SEARCH_QUERIES_BY_REGION = {
    "us": {
        "name": "🇺🇸 美国",
        "language": "en",
        "queries": WEIRDNESS_PONDS["global"],
        "site_searches": BIG_LAB_RELEASE_RADAR["global"],
        "funding_side_channel": FUNDING_SIDE_CHANNELS["us"],
    },
    "cn": {
        "name": "🇨🇳 中国",
        "language": "zh",
        "queries": WEIRDNESS_PONDS["cn"],
        "site_searches": BIG_LAB_RELEASE_RADAR["cn"],
        "funding_side_channel": FUNDING_SIDE_CHANNELS["cn"],
    },
    "eu": {
        "name": "🇪🇺 欧洲",
        "language": "en",
        "queries": [
            *WEIRDNESS_PONDS["global"],
            "European AI hardware gadget {year}",
            "site:producthunt.com AI Europe {year}",
        ],
        "site_searches": BIG_LAB_RELEASE_RADAR["global"],
        "funding_side_channel": FUNDING_SIDE_CHANNELS["eu"],
    },
    "jp": {
        "name": "🇯🇵 日本",
        "language": "ja",
        "queries": [*WEIRDNESS_PONDS["jp"], *WEIRDNESS_PONDS["global"][:6]],
        "site_searches": BIG_LAB_RELEASE_RADAR["global"],
        "funding_side_channel": FUNDING_SIDE_CHANNELS["jp"],
    },
    "kr": {
        "name": "🇰🇷 韩国",
        "language": "ko",
        "queries": [
            *WEIRDNESS_PONDS["global"][:8],
            "Korean AI wearable device {year}",
            "Korean AI hardware product {year}",
        ],
        "site_searches": BIG_LAB_RELEASE_RADAR["global"],
        "funding_side_channel": FUNDING_SIDE_CHANNELS["kr"],
    },
    "sea": {
        "name": "🇸🇬 东南亚",
        "language": "en",
        "queries": [
            *WEIRDNESS_PONDS["global"][:8],
            "Singapore AI hardware product {year}",
            "Southeast Asia AI device {year}",
        ],
        "site_searches": BIG_LAB_RELEASE_RADAR["global"],
        "funding_side_channel": FUNDING_SIDE_CHANNELS["sea"],
    },
}

HARDWARE_SITE_SEARCHES = {
    "global": WEIRDNESS_PONDS["global"],
    "cn": WEIRDNESS_PONDS["cn"],
}

KEYWORDS_HARDWARE = {
    "en": [
        "AI pendant",
        "AI frame",
        "AI plant",
        "AI mirror",
        "AI lamp",
        "AI sticker",
        "AI plush",
        "AI collar",
        "AI ring",
        "AI glasses",
        "AI doorbell",
        "AI badge",
    ],
    "zh": [
        "AI盆栽",
        "AI相框",
        "AI镜子",
        "AI台灯",
        "AI贴纸",
        "AI玩偶",
        "AI宠物项圈",
        "AI戒指",
        "AI眼镜",
        "AI门铃",
        "AI徽章",
    ],
}


def _fill(query: str, *, year: int, month: str, category: str = "") -> str:
    category = category or random.choice(UNUSUAL_CATEGORIES)
    return query.format(year=year, month=month, category=category)


def _weighted_queries(config: dict, *, year: int, month: str) -> list[str]:
    main = [_fill(q, year=year, month=month) for q in config.get("queries", [])]
    big_lab = [_fill(q, year=year, month=month) for q in config.get("site_searches", [])]
    funding = [_fill(q, year=year, month=month) for q in config.get("funding_side_channel", [])]

    # Intended slot mix: weirdness ~65%, big lab radar ~20%, funding side-channel ~15%.
    weighted = (main * 4) + (big_lab * 2) + funding
    random.shuffle(weighted)
    return weighted


def generate_search_queries(
    region: str,
    query_type: str = "general",
    limit: int = 5,
    include_sites: bool = True,
    product_type: str = "mixed",
) -> list[str]:
    """Generate v2 discovery queries for weird products and surprising releases."""
    config = SEARCH_QUERIES_BY_REGION.get(region, SEARCH_QUERIES_BY_REGION["us"])
    year = get_current_year()
    month = get_current_month()

    if query_type == "sites":
        queries = [_fill(q, year=year, month=month) for q in config.get("site_searches", [])]
    elif query_type == "funding":
        queries = [_fill(q, year=year, month=month) for q in config.get("funding_side_channel", [])]
    elif query_type == "hardware" or product_type == "hardware":
        base = config.get("queries", []) + HARDWARE_SITE_SEARCHES.get("global", [])
        if region == "cn":
            base += HARDWARE_SITE_SEARCHES.get("cn", [])
        queries = [_fill(q, year=year, month=month) for q in base]
    else:
        queries = _weighted_queries(config, year=year, month=month)
        if not include_sites:
            site_queries = {_fill(q, year=year, month=month) for q in config.get("site_searches", [])}
            queries = [q for q in queries if q not in site_queries]

    seen = []
    used = set()
    for query in queries:
        if query in used:
            continue
        seen.append(query)
        used.add(query)
        if len(seen) >= limit:
            break
    return seen


def generate_discovery_query(
    region: str,
    category: Optional[str] = None,
    funding_stage: Optional[str] = None,
) -> str:
    """Return one v2 discovery query. `funding_stage` is accepted for compatibility."""
    config = SEARCH_QUERIES_BY_REGION.get(region, SEARCH_QUERIES_BY_REGION["us"])
    year = get_current_year()
    month = get_current_month()
    pool = list(config.get("queries", []))
    if category:
        pool.insert(0, f"site:producthunt.com AI {category} {{year}}")
    query = random.choice(pool or WEIRDNESS_PONDS["global"])
    return _fill(query, year=year, month=month, category=category or "")


def get_search_params(region: str, recency: str = "week") -> dict:
    """Return conservative search API params for current product discovery."""
    region_params = {
        "us": {"country": "US", "search_language_filter": ["en"]},
        "cn": {"country": "CN", "search_language_filter": ["zh"]},
        "eu": {"country": "GB", "search_language_filter": ["en", "de", "fr"]},
        "jp": {"country": "JP", "search_language_filter": ["ja", "en"]},
        "kr": {"country": "KR", "search_language_filter": ["ko", "en"]},
        "sea": {"country": "SG", "search_language_filter": ["en"]},
    }
    params = dict(region_params.get(region, region_params["us"]))
    params["max_results"] = 10
    params["max_tokens_per_page"] = 2048
    params["max_tokens"] = 25000
    if recency in {"day", "week", "month", "year"}:
        params["search_recency_filter"] = recency
    return params


def get_funding_search_params(region: str) -> dict:
    """Compatibility helper for the residual funding side-channel."""
    return get_search_params(region, recency="week")


__all__ = [
    "SEARCH_QUERIES_BY_REGION",
    "HARDWARE_SITE_SEARCHES",
    "KEYWORDS_HARDWARE",
    "WEIRDNESS_PONDS",
    "BIG_LAB_RELEASE_RADAR",
    "FUNDING_SIDE_CHANNELS",
    "generate_search_queries",
    "generate_discovery_query",
    "get_search_params",
    "get_funding_search_params",
]
