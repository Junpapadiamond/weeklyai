import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_TIMEOUT = 20
USER_AGENT = "WeeklyAIImporter/1.0"

ALLOWED_CATEGORIES = {
    "coding",
    "voice",
    "finance",
    "image",
    "video",
    "writing",
    "healthcare",
    "education",
    "hardware",
    "other",
}

KEYWORD_CATEGORIES = {
    "hardware": ["hardware", "device", "robot", "chip", "sensor", "wearable", "appliance"],
    "voice": ["voice", "speech", "audio", "tts", "asr", "call center"],
    "finance": ["finance", "fintech", "bank", "trading", "payments", "credit"],
    "image": ["image", "vision", "photo", "camera", "visual", "render"],
    "video": ["video", "film", "cinema", "animation", "motion"],
    "writing": ["writing", "copy", "content", "marketing", "blog"],
    "healthcare": ["health", "medical", "diagnostic", "clinical", "patient"],
    "education": ["education", "learning", "classroom", "course", "tutor"],
    "coding": ["developer", "code", "api", "sdk", "software", "workflow"],
}


def fetch_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.text


def extract_meta_description(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return meta["content"].strip()
    meta = soup.find("meta", attrs={"property": "og:description"})
    if meta and meta.get("content"):
        return meta["content"].strip()
    return ""


def extract_text(html: str, max_chars: int = 2000) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(soup.stripped_strings)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def infer_categories(text: str) -> List[str]:
    if not text:
        return ["other"]
    text_lower = text.lower()
    categories = []
    for category, keywords in KEYWORD_CATEGORIES.items():
        if any(keyword in text_lower for keyword in keywords):
            categories.append(category)
    return categories or ["other"]


def normalize_categories(categories: List[str]) -> List[str]:
    cleaned = []
    for cat in categories:
        if not cat:
            continue
        cat = cat.strip().lower()
        if cat not in ALLOWED_CATEGORIES:
            continue
        if cat not in cleaned:
            cleaned.append(cat)
    return cleaned or ["other"]


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "unknown"


def get_domain(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    host = parsed.netloc or ""
    return host.replace("www.", "")


def logo_url_for_site(url: str) -> str:
    domain = get_domain(url)
    if not domain:
        return ""
    return f"https://logo.clearbit.com/{domain}"


def get_llm_settings(provider: Optional[str] = None, model: Optional[str] = None) -> Optional[Tuple[str, str, str]]:
    provider = (provider or "").lower().strip()
    if not provider:
        if os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        elif os.getenv("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        else:
            return None

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        model = model or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        model = model or os.getenv("ANTHROPIC_MODEL") or "claude-3-5-sonnet-20241022"
    else:
        return None

    return provider, model, api_key


def request_llm_json(prompt: str, settings: Tuple[str, str, str]) -> Optional[Any]:
    provider, model, api_key = settings
    if provider == "openai":
        return request_openai(prompt, model, api_key)
    if provider == "anthropic":
        return request_anthropic(prompt, model, api_key)
    return None


def request_openai(prompt: str, model: str, api_key: str) -> Optional[Any]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json=payload,
        timeout=DEFAULT_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    return parse_json_from_text(content)


def request_anthropic(prompt: str, model: str, api_key: str) -> Optional[Any]:
    payload = {
        "model": model,
        "max_tokens": 500,
        "temperature": 0.2,
        "messages": [
            {"role": "user", "content": prompt},
        ],
    }
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json=payload,
        timeout=DEFAULT_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    content = ""
    for item in data.get("content", []):
        if item.get("type") == "text":
            content += item.get("text", "")
    return parse_json_from_text(content)


def parse_json_from_text(text: str) -> Optional[Any]:
    if not text:
        return None
    fence_match = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    text = text.strip()

    start_candidates = [text.find("["), text.find("{")]
    start_candidates = [s for s in start_candidates if s != -1]
    if start_candidates:
        start = min(start_candidates)
        text = text[start:]

    end_candidates = [text.rfind("]"), text.rfind("}")]
    end_candidates = [e for e in end_candidates if e != -1]
    if end_candidates:
        end = max(end_candidates)
        text = text[:end + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def dedupe_by_name(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    unique = []
    for item in items:
        name = (item.get("name") or "").strip().lower()
        if not name or name in seen:
            continue
        seen.add(name)
        unique.append(item)
    return unique
