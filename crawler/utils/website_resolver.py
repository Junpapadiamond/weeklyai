"""
Website resolver utilities.

Goal: extract official product website from a source/news page.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import List, Tuple
from urllib.parse import urljoin, urlparse

import requests


SOCIAL_DOMAINS = {
    "twitter.com",
    "x.com",
    "facebook.com",
    "linkedin.com",
    "instagram.com",
    "youtube.com",
    "tiktok.com",
    # China-native social/content platforms (not official product websites)
    "mp.weixin.qq.com",
    "weixin.qq.com",
    "wechat.com",
    "zhihu.com",
    "xiaohongshu.com",
    "xhslink.com",
    "weibo.com",
    "reddit.com",
    "threads.net",
    "discord.com",
    "discord.gg",
    "t.me",
    "telegram.me",
    "medium.com",
    "substack.com",
    "news.ycombinator.com",
}

SHORTENER_DOMAINS = {
    "bit.ly",
    "t.co",
    "tinyurl.com",
    "goo.gl",
    "ow.ly",
    "buff.ly",
    "t.cn",
    "is.gd",
    "s.id",
    "rebrand.ly",
}

PLACEHOLDER_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
    "test.com",
    "test.org",
    "localhost",
    "127.0.0.1",
}


class _LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: List[Tuple[str, str]] = []
        self._current_href = ""
        self._current_text: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = ""
        for key, value in attrs:
            if key.lower() == "href":
                href = value or ""
                break
        if href:
            self._current_href = href
            self._current_text = []

    def handle_data(self, data):
        if self._current_href:
            text = (data or "").strip()
            if text:
                self._current_text.append(text)

    def handle_endtag(self, tag):
        if tag == "a" and self._current_href:
            text = " ".join(self._current_text).strip()
            self.links.append((self._current_href, text))
            self._current_href = ""
            self._current_text = []


def _normalize_name(value: str) -> str:
    # Keep ASCII alphanumerics and CJK ideographs; drop punctuation/whitespace.
    # This helps resolve Chinese product pages where the anchor text contains the product name.
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", (value or "").lower())


def _domain_from_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    domain = (parsed.netloc or "").lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def _is_placeholder_domain(domain: str) -> bool:
    if not domain:
        return True
    if domain in PLACEHOLDER_DOMAINS:
        return True
    if domain.endswith(".local"):
        return True
    return False


def _should_skip_domain(domain: str) -> bool:
    if not domain:
        return True
    if domain in SOCIAL_DOMAINS or domain in SHORTENER_DOMAINS:
        return True
    if _is_placeholder_domain(domain):
        return True
    return False


def _score_link(url: str, text: str, name_norm: str, source_domain: str) -> int:
    if not url:
        return -100

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return -100

    domain = _domain_from_url(url)
    if not domain or domain == source_domain or domain.endswith(f".{source_domain}"):
        return -100

    if _should_skip_domain(domain):
        return -100

    score = 0
    text_norm = _normalize_name(text)
    domain_norm = _normalize_name(domain.split(".")[0])
    url_norm = _normalize_name(url)

    name_hit = False
    if name_norm:
        if name_norm in text_norm:
            score += 40
            name_hit = True
        if name_norm in domain_norm:
            score += 30
            name_hit = True
        if name_norm in url_norm:
            score += 10
            name_hit = True

        tokens = re.findall(r"[a-z0-9]{3,}", name_norm)
        for token in tokens:
            if token in text_norm or token in domain_norm or token in url_norm:
                name_hit = True
                score += 5
                break

    official_hint = bool(re.search(r"(official|website|homepage|官网|官方网站|主页|官网链接|访问官网|进入官网|产品官网|公司官网)", text, re.IGNORECASE))

    # Chinese sources often link as "官网" without repeating the company name in the anchor text.
    # If the product name is CJK-only, allow a strong "official" hint to qualify the link.
    has_cjk_name = bool(re.search(r"[\u4e00-\u9fff]", name_norm))
    if not name_hit:
        if official_hint and (not name_norm or has_cjk_name):
            score += 18  # baseline so it can pass the threshold with other signals
            name_hit = True
        else:
            return -100

    if official_hint:
        score += 12

    tld = f".{domain.split('.')[-1]}"
    if tld in {".ai", ".io", ".com", ".co", ".app", ".dev", ".cn", ".jp", ".kr", ".sg", ".eu"}:
        score += 6

    if parsed.path in ("", "/"):
        score += 6
    elif len(parsed.path) > 40:
        score -= 4

    return score


def extract_official_website_from_source(
    source_url: str,
    product_name: str = "",
    timeout: int = 10,
    max_links: int = 200,
    min_score: int = 18,
    aggressive: bool = False,
) -> str:
    if not source_url:
        return ""

    try:
        resp = requests.get(
            source_url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
        )
    except Exception:
        return ""

    content_type = resp.headers.get("Content-Type", "")
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        return ""

    html = resp.text or ""
    if len(html) < 200:
        return ""

    parser = _LinkExtractor()
    parser.feed(html)

    if not parser.links:
        return ""

    source_domain = _domain_from_url(source_url)
    name_norm = _normalize_name(product_name)

    best_score = -100
    best_url = ""
    for href, text in parser.links[:max_links]:
        if not href or href.startswith("#"):
            continue
        if href.startswith("mailto:") or href.startswith("javascript:"):
            continue

        full_url = urljoin(source_url, href)
        score = _score_link(full_url, text, name_norm, source_domain)
        if score > best_score:
            best_score = score
            best_url = full_url

    threshold = min_score
    if aggressive:
        threshold = max(8, min_score - 8)

    if best_score < threshold:
        if aggressive and best_url and best_score > 0:
            return best_url
        return ""

    return best_url


def is_placeholder_url(url: str) -> bool:
    domain = _domain_from_url(url)
    return _is_placeholder_domain(domain)
