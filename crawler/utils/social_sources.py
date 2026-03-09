"""
Shared source loaders for social signal spiders.

Priority order for all source configs:
1) Environment variables
2) crawler/data/source_watchlists.json
3) Built-in defaults
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Tuple


_UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
_CRAWLER_DIR = os.path.dirname(_UTILS_DIR)
_DATA_DIR = os.path.join(_CRAWLER_DIR, "data")
_DEFAULT_WATCHLIST_FILE = os.path.join(_DATA_DIR, "source_watchlists.json")


DEFAULT_YOUTUBE_CHANNEL_IDS: List[str] = [
    "UCbfYPyITQ-7l4upoX8nvctg",  # Two Minute Papers
    "UCNJ1Ymd5yFuUPtn21xtRbbw",  # AI Explained
    "UCJIfeSCssxSC_Dhc5s7woww",  # Matt Wolfe
    "UCsBjURrPoezykLs9EqgamOA",  # Fireship
    "UCZHmQk67mSJgfCCTn7xBfew",  # Yannic Kilcher
    "UCRJFAp0rewx8kzdhEqDHIlA",  # The AI Advantage
    "UCUyeluBRhGPCW4rPe_UvBZQ",  # All About AI
    "UC8WCW6C3BWLKSZ5cMzD8Gyw",  # 跟李沐学AI
]

DEFAULT_X_ACCOUNTS: List[str] = [
    "OpenAI",
    "OpenAIDevs",
    "AnthropicAI",
    "xai",
    "MistralAI",
    "Cohere",
    "perplexity_ai",
    "cursor_ai",
    "Replit",
    "RunwayML",
    "stabilityai",
    "huggingface",
    "LangChainAI",
    "GoogleDeepMind",
    "GoogleAI",
    "SakanaAILabs",
    "upstageai",
    "NVIDIAAI",
]

DEFAULT_REDDIT_SUBREDDITS: List[str] = [
    "LocalLLaMA",
    "MachineLearning",
    "artificial",
    "singularity",
    "OpenAI",
    "ClaudeAI",
    "LangChain",
]

DEFAULT_YOUTUBE_HEALTH_POLICY: Dict[str, Any] = {
    "consecutive_404_threshold": 3,
    "cooldown_days": 7,
}

DEFAULT_X_FALLBACK: Dict[str, Any] = {
    "timeline_provider": "auto",
    "tweet_provider": "x_syndication",
    "max_status_per_account": 5,
    "request_timeout_seconds": 20,
    "nitter_instances": [
        "https://nitter.net",
        "https://nitter.poast.org",
    ],
    "browser_enabled": True,
}


def _dedupe_preserve_order(values: List[str], *, lowercase_key: bool = True) -> List[str]:
    out: List[str] = []
    seen = set()
    for raw in values:
        value = str(raw).strip()
        if not value:
            continue
        key = value.lower() if lowercase_key else value
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _parse_csv_env(value: str, *, strip_at_prefix: bool = False) -> List[str]:
    parts = [x.strip() for x in (value or "").split(",") if x and x.strip()]
    if strip_at_prefix:
        parts = [p.lstrip("@") for p in parts]
    return _dedupe_preserve_order(parts)


def _safe_int(value: Any, default: int, *, min_value: int, max_value: int) -> int:
    try:
        parsed = int(str(value).strip())
    except Exception:
        return default
    return max(min_value, min(max_value, parsed))


def _safe_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _watchlist_path() -> str:
    env_path = (os.getenv("SOCIAL_SOURCE_WATCHLIST") or "").strip()
    if env_path:
        return env_path
    return _DEFAULT_WATCHLIST_FILE


def _load_watchlist_file() -> Dict[str, Any]:
    path = _watchlist_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _extract_youtube_channel_items_from_watchlist(watchlist: Dict[str, Any]) -> List[Any]:
    youtube_cfg = watchlist.get("youtube")
    if isinstance(youtube_cfg, dict):
        channels = youtube_cfg.get("channels")
        if isinstance(channels, list):
            return channels

    legacy = watchlist.get("youtube_channel_ids")
    if isinstance(legacy, list):
        return legacy
    return []


def _normalize_youtube_channel_configs(values: List[Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen = set()
    for raw in values:
        channel_id = ""
        name = ""
        enabled = True
        if isinstance(raw, str):
            channel_id = raw.strip()
        elif isinstance(raw, dict):
            channel_id = str(raw.get("channel_id") or raw.get("id") or "").strip()
            name = str(raw.get("name") or "").strip()
            enabled = _safe_bool(raw.get("enabled"), True)
        if not channel_id:
            continue
        key = channel_id.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({"channel_id": channel_id, "name": name, "enabled": enabled})
    return out


def load_youtube_channel_configs_with_source() -> Tuple[List[Dict[str, Any]], str]:
    env_value = (os.getenv("YOUTUBE_CHANNEL_IDS") or "").strip()
    if env_value:
        ids = _parse_csv_env(env_value)
        if ids:
            return _normalize_youtube_channel_configs(ids), "env:YOUTUBE_CHANNEL_IDS"

    watchlist = _load_watchlist_file()
    file_values = _extract_youtube_channel_items_from_watchlist(watchlist)
    if file_values:
        configs = _normalize_youtube_channel_configs(file_values)
        if configs:
            return configs, f"file:{_watchlist_path()}"

    return _normalize_youtube_channel_configs(DEFAULT_YOUTUBE_CHANNEL_IDS), "default:builtin"


def load_youtube_channel_ids_with_source() -> Tuple[List[str], str]:
    configs, source = load_youtube_channel_configs_with_source()
    ids = [cfg.get("channel_id", "") for cfg in configs if cfg.get("enabled", True)]
    ids = [x for x in ids if x]
    return ids, source


def load_youtube_channel_ids() -> List[str]:
    ids, _ = load_youtube_channel_ids_with_source()
    return ids


def load_youtube_health_policy() -> Dict[str, int]:
    cfg = dict(DEFAULT_YOUTUBE_HEALTH_POLICY)
    watchlist = _load_watchlist_file()
    youtube_cfg = watchlist.get("youtube") if isinstance(watchlist.get("youtube"), dict) else {}
    policy = youtube_cfg.get("health_policy") if isinstance(youtube_cfg, dict) else None
    if isinstance(policy, dict):
        cfg["consecutive_404_threshold"] = _safe_int(
            policy.get("consecutive_404_threshold"),
            cfg["consecutive_404_threshold"],
            min_value=1,
            max_value=10,
        )
        cfg["cooldown_days"] = _safe_int(
            policy.get("cooldown_days"),
            cfg["cooldown_days"],
            min_value=1,
            max_value=30,
        )

    cfg["consecutive_404_threshold"] = _safe_int(
        os.getenv("YOUTUBE_404_THRESHOLD"),
        cfg["consecutive_404_threshold"],
        min_value=1,
        max_value=10,
    )
    cfg["cooldown_days"] = _safe_int(
        os.getenv("YOUTUBE_CHANNEL_COOLDOWN_DAYS"),
        cfg["cooldown_days"],
        min_value=1,
        max_value=30,
    )
    return cfg


def load_x_accounts_with_source() -> Tuple[List[str], str]:
    env_value = (os.getenv("X_ACCOUNTS") or "").strip()
    if env_value:
        accounts = _parse_csv_env(env_value, strip_at_prefix=True)
        if accounts:
            return accounts, "env:X_ACCOUNTS"

    watchlist = _load_watchlist_file()
    x_cfg = watchlist.get("x") if isinstance(watchlist.get("x"), dict) else {}
    file_values = x_cfg.get("accounts") if isinstance(x_cfg, dict) else None
    if not isinstance(file_values, list):
        file_values = watchlist.get("x_accounts")
    if isinstance(file_values, list):
        accounts = [str(x).strip().lstrip("@") for x in file_values if str(x).strip()]
        accounts = _dedupe_preserve_order(accounts)
        if accounts:
            return accounts, f"file:{_watchlist_path()}"

    return list(DEFAULT_X_ACCOUNTS), "default:builtin"


def load_x_accounts() -> List[str]:
    accounts, _ = load_x_accounts_with_source()
    return accounts


def load_x_fallback_config() -> Dict[str, Any]:
    cfg: Dict[str, Any] = dict(DEFAULT_X_FALLBACK)

    watchlist = _load_watchlist_file()
    x_cfg = watchlist.get("x") if isinstance(watchlist.get("x"), dict) else {}
    file_cfg = x_cfg.get("fallback") if isinstance(x_cfg, dict) else None
    if not isinstance(file_cfg, dict):
        file_cfg = watchlist.get("x_fallback")
    if isinstance(file_cfg, dict):
        if isinstance(file_cfg.get("timeline_provider"), str) and file_cfg.get("timeline_provider"):
            cfg["timeline_provider"] = file_cfg["timeline_provider"].strip()
        if isinstance(file_cfg.get("tweet_provider"), str) and file_cfg.get("tweet_provider"):
            cfg["tweet_provider"] = file_cfg["tweet_provider"].strip()
        cfg["max_status_per_account"] = _safe_int(
            file_cfg.get("max_status_per_account"),
            cfg["max_status_per_account"],
            min_value=1,
            max_value=20,
        )
        cfg["request_timeout_seconds"] = _safe_int(
            file_cfg.get("request_timeout_seconds"),
            cfg["request_timeout_seconds"],
            min_value=5,
            max_value=60,
        )
        instances = file_cfg.get("nitter_instances")
        if isinstance(instances, list):
            parsed = [str(x).strip().rstrip("/") for x in instances if str(x).strip()]
            if parsed:
                cfg["nitter_instances"] = _dedupe_preserve_order(parsed, lowercase_key=True)
        if "browser_enabled" in file_cfg:
            cfg["browser_enabled"] = _safe_bool(
                file_cfg.get("browser_enabled"),
                bool(cfg.get("browser_enabled", True)),
            )

    env_timeline = (os.getenv("X_TIMELINE_PROVIDER") or "").strip()
    env_tweet_provider = (os.getenv("X_TWEET_PROVIDER") or "").strip()
    if env_timeline:
        cfg["timeline_provider"] = env_timeline
    if env_tweet_provider:
        cfg["tweet_provider"] = env_tweet_provider

    cfg["max_status_per_account"] = _safe_int(
        os.getenv("X_FALLBACK_MAX_STATUS_PER_ACCOUNT"),
        cfg["max_status_per_account"],
        min_value=1,
        max_value=20,
    )
    cfg["request_timeout_seconds"] = _safe_int(
        os.getenv("X_FALLBACK_TIMEOUT"),
        cfg["request_timeout_seconds"],
        min_value=5,
        max_value=60,
    )
    env_nitter = (os.getenv("X_NITTER_BASES") or "").strip()
    if env_nitter:
        instances = [x.strip().rstrip("/") for x in env_nitter.split(",") if x.strip()]
        if instances:
            cfg["nitter_instances"] = _dedupe_preserve_order(instances, lowercase_key=True)
    cfg["browser_enabled"] = _safe_bool(
        os.getenv("X_ENABLE_BROWSER_FALLBACK"),
        bool(cfg.get("browser_enabled", True)),
    )
    return cfg


def load_x_source_mode() -> str:
    mode = (os.getenv("X_SOURCE_MODE") or "hybrid").strip().lower()
    if mode not in {"hybrid", "perplexity_only", "fallback_only"}:
        return "hybrid"
    return mode


def load_reddit_subreddits_with_source() -> Tuple[List[str], str]:
    def _normalize_sub(value: str) -> str:
        text = str(value or "").strip()
        text = re.sub(r"^(?:r/)+", "", text, flags=re.IGNORECASE)
        return text.strip("/")

    env_value = (os.getenv("REDDIT_SUBREDDITS") or os.getenv("NEWS_REDDIT_SUBS") or "").strip()
    if env_value:
        subs = _parse_csv_env(env_value)
        subs = [_normalize_sub(s) for s in subs if s]
        subs = _dedupe_preserve_order(subs)
        if subs:
            return subs, "env:REDDIT_SUBREDDITS"

    watchlist = _load_watchlist_file()
    file_values = watchlist.get("reddit_subreddits")
    if isinstance(file_values, list):
        subs = [_normalize_sub(str(x)) for x in file_values if str(x).strip()]
        subs = _dedupe_preserve_order(subs)
        if subs:
            return subs, f"file:{_watchlist_path()}"

    return list(DEFAULT_REDDIT_SUBREDDITS), "default:builtin"


def load_reddit_subreddits() -> List[str]:
    subs, _ = load_reddit_subreddits_with_source()
    return subs
