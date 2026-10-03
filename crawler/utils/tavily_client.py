"""Bounded Tavily news retrieval; original pages still supply publication evidence."""
import os
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import requests


class TavilyError(RuntimeError):
    pass


def parse_date(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        date = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        try:
            date = parsedate_to_datetime(value)
        except (ValueError, TypeError, OverflowError):
            return None
    return date.replace(tzinfo=timezone.utc) if date.tzinfo is None else date.astimezone(timezone.utc)


def search_articles(query, days=14, limit=10, now=None, topic='news'):
    key = os.getenv("TAVILY_API_KEY", "").strip()
    if not key:
        raise TavilyError("TAVILY_API_KEY is missing")
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=max(1, min(30, days)))
    limit = max(1, min(10, limit))
    try:
        response = requests.post("https://api.tavily.com/search",
            headers={"Authorization": f"Bearer {key}"},
            json={"query": query, "topic": topic, "search_depth": "basic", "max_results": limit,
                  "start_date": since.date().isoformat(), "end_date": (now + timedelta(days=1)).date().isoformat(),
                  "include_published_date": True, "filter_by_published_date": topic == 'news',
                  "include_answer": False, "include_raw_content": False, "auto_parameters": False},
            timeout=(5, 25), allow_redirects=False)
        if response.status_code != 200:
            raise TavilyError(f"Tavily returned HTTP {response.status_code}")
        body = response.json()
        if not isinstance(body, dict) or not isinstance(body.get("results"), list):
            raise TavilyError("Tavily returned an invalid result envelope")
    except (requests.RequestException, ValueError):
        raise TavilyError("Tavily search unavailable or invalid JSON") from None
    articles, seen = [], set()
    for item in body["results"]:
        if not isinstance(item, dict):
            continue
        date = parse_date(item.get("published_date"))
        # General search can discover small local publishers without an indexed
        # date. They remain candidates until original-page publication validation.
        if (date and not since <= date <= now) or (not date and topic == 'news'):
            continue
        if not all(isinstance(item.get(k), str) and item[k].strip() for k in ("url", "title", "content")):
            continue
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        articles.append({"url": item["url"], "title": item["title"][:300], "source": "Tavily",
                         "published_at": date.isoformat() if date else '', "search_published_at": date.isoformat() if date else '',
                         "summary": item["content"][:1500]})
    return articles[:limit]
