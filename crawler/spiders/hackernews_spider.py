"""
Hacker News AI crawler using Algolia search_by_date.
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .base_spider import BaseSpider


class HackerNewsSpider(BaseSpider):
    """Hacker News Algolia 爬虫"""

    API_BASE = "https://hn.algolia.com/api/v1"

    def crawl(self) -> List[Dict[str, Any]]:
        """Fetch recent AI-related HN posts."""
        products = []
        seen = set()

        print("  [HackerNews] Searching recent AI posts...")

        queries = [
            "ai",
            "gpt",
            "llm",
            "machine learning",
            "ai agent",
        ]

        for query in queries[:4]:
            try:
                hits = self._fetch_query(query, days_back=7)
                for hit in hits:
                    product = self._parse_hit(hit)
                    if not product:
                        continue
                    name = product.get('name')
                    if name and name not in seen:
                        products.append(product)
                        seen.add(name)
                time.sleep(0.4)
            except Exception as e:
                print(f"    ⚠ HN search failed '{query}': {e}")
                continue

        print(f"  [HackerNews] Collected {len(products)} posts")
        return products

    def _fetch_query(self, query: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Call Algolia Search API (search_by_date)."""
        since = datetime.utcnow() - timedelta(days=days_back)
        params = {
            'query': query,
            'tags': 'story',
            'hitsPerPage': 50,
            'numericFilters': f"created_at_i>{int(since.timestamp())}",
        }

        response = self.session.get(f"{self.API_BASE}/search_by_date", params=params, timeout=10)
        if response.status_code != 200:
            return []
        data = response.json()
        return data.get('hits', [])

    def _parse_hit(self, hit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse HN hit."""
        title = hit.get('title') or ''
        if not title:
            return None

        text = f"{title} {hit.get('story_text') or ''}".lower()
        if not self._is_ai_related(text):
            return None

        is_show_hn = 'show hn' in title.lower()
        is_launch = 'launch' in title.lower() or 'introducing' in title.lower()

        url = hit.get('url')
        if not url:
            url = f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"

        points = hit.get('points', 0) or 0
        comments = hit.get('num_comments', 0) or 0

        trending_score = min(100, int(30 + points * 0.6 + comments * 0.8))
        if is_show_hn:
            trending_score = min(100, trending_score + 15)
        elif is_launch:
            trending_score = min(100, trending_score + 8)

        categories = self._infer_categories(text)

        return self.create_product(
            name=title.replace('Show HN:', '').replace('Show HN -', '').strip(),
            description=(hit.get('story_text') or title)[:200],
            logo_url='',
            website=url,
            categories=categories if categories else ['other'],
            weekly_users=points * 20,
            trending_score=trending_score,
            source='hackernews',
            published_at=hit.get('created_at'),
            extra={
                'points': points,
                'votes': points,
                'comments': comments,
                'hn_id': hit.get('objectID', ''),
                'is_show_hn': is_show_hn,
                'is_launch': is_launch,
            }
        )

    @staticmethod
    def _is_ai_related(text: str) -> bool:
        keywords = [
            'ai',
            'gpt',
            'llm',
            'machine learning',
            'artificial intelligence',
            'neural',
            'agent',
            'rag',
            'diffusion',
        ]
        return any(kw in text for kw in keywords)

    @staticmethod
    def _infer_categories(text: str) -> List[str]:
        """Infer categories from text."""
        categories = set()
        keyword_mapping = {
            'coding': ['code', 'developer', 'api', 'sdk', 'repo'],
            'image': ['image', 'vision', 'diffusion', 'art'],
            'video': ['video', 'animation'],
            'voice': ['voice', 'audio', 'speech'],
            'writing': ['write', 'writing', 'text', 'summarize'],
            'finance': ['finance', 'trading', 'invest'],
            'healthcare': ['health', 'medical'],
            'education': ['learn', 'education', 'course'],
        }

        for category, keywords in keyword_mapping.items():
            if any(kw in text for kw in keywords):
                categories.add(category)

        return list(categories)
