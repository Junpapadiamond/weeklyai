"""Bounded Exa retrieval. Search supplies evidence; it never scores products."""
import os
from datetime import datetime, timedelta, timezone

import requests


class ExaError(RuntimeError):
    pass


def search_articles(query, days=14, limit=8, now=None):
    key = os.getenv("EXA_API_KEY", "").strip()
    if not key:
        raise ExaError("EXA_API_KEY is missing")
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=max(1, min(30, days)))
    try:
        response = requests.post("https://api.exa.ai/search", headers={"x-api-key": key},
            json={"query": query, "type": "auto", "numResults": max(1, min(10, limit)),
                  "startPublishedDate": since.isoformat(), "endPublishedDate": now.isoformat(),
                  "contents": {"text": {"maxCharacters": 18000}, "extras": {"links": 30}}},
            timeout=(5, 25), allow_redirects=False)
        if response.status_code != 200:
            raise ExaError(f"Exa returned HTTP {response.status_code}")
        body = response.json()
        if not isinstance(body, dict) or not isinstance(body.get("results"), list):
            raise ExaError("Exa returned an invalid result envelope")
    except (requests.RequestException, ValueError):
        raise ExaError("Exa search unavailable or invalid JSON") from None
    # Do not infer dates or accept the crawl date as a publication date.
    articles = []
    for item in body["results"]:
        if not isinstance(item, dict):
            continue
        try:
            date = datetime.fromisoformat(item.get("publishedDate", "").replace("Z", "+00:00"))
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            if not since <= date <= now:
                continue
        except (ValueError, TypeError, AttributeError):
            continue
        if not all(isinstance(item.get(k), str) and item[k].strip() for k in ("url", "title", "text")):
            continue
        articles.append({"url": item["url"], "title": item["title"][:300],
                         "published_at": date.isoformat(), "summary": item["text"][:1500], "source": "Exa"})
    return articles[:limit]
