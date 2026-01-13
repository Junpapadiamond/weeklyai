"""
Tech News Spider - Crawl AI news from The Verge, TechCrunch, Wired, etc.
Focus on NEW features, launches, and updates rather than reviews of old products.
"""

import re
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .base_spider import BaseSpider


class TechNewsSpider(BaseSpider):
    """Crawl AI-related news from tech publications"""

    # RSS feeds for AI news
    RSS_FEEDS = [
        # The Verge - AI section
        ('https://www.theverge.com/rss/ai-artificial-intelligence/index.xml', 'theverge'),
        # TechCrunch - AI category
        ('https://techcrunch.com/category/artificial-intelligence/feed/', 'techcrunch'),
        # Wired - AI section
        ('https://www.wired.com/feed/tag/ai/latest/rss', 'wired'),
        # Ars Technica - AI
        ('https://feeds.arstechnica.com/arstechnica/technology-lab', 'arstechnica'),
        # VentureBeat - AI
        ('https://venturebeat.com/category/ai/feed/', 'venturebeat'),
        # MIT Tech Review - AI
        ('https://www.technologyreview.com/feed/', 'mit_tech_review'),
    ]

    # Keywords that indicate NEW product/feature (not just review/opinion)
    LAUNCH_KEYWORDS = [
        'launch', 'launches', 'launched', 'releasing', 'released', 'release',
        'announce', 'announces', 'announced', 'announcing',
        'introduce', 'introduces', 'introduced', 'introducing',
        'unveil', 'unveils', 'unveiled', 'unveiling',
        'debut', 'debuts', 'debuted',
        'rolls out', 'rolling out', 'now available', 'is here',
        'new feature', 'new tool', 'new model', 'new version',
        'update', 'updates', 'updated', 'upgrade', 'upgrades',
        'beta', 'preview', 'early access',
        'api', 'sdk', 'plugin', 'extension', 'integration',
    ]

    # AI-related keywords to filter relevant articles
    AI_KEYWORDS = [
        'ai', 'artificial intelligence', 'machine learning', 'ml', 'llm',
        'gpt', 'chatgpt', 'claude', 'gemini', 'copilot', 'openai', 'anthropic',
        'google ai', 'meta ai', 'microsoft ai', 'amazon ai',
        'neural', 'deep learning', 'generative', 'transformer',
        'chatbot', 'assistant', 'agent', 'model', 'diffusion',
        'stable diffusion', 'midjourney', 'dall-e', 'sora',
        'llama', 'mistral', 'phi', 'qwen', 'deepseek',
        'hugging face', 'langchain', 'vector', 'embedding', 'rag',
        'text-to-image', 'text-to-video', 'text-to-speech', 'speech-to-text',
        'computer vision', 'nlp', 'natural language',
    ]

    def __init__(self):
        super().__init__()
        self.seen_urls = set()

    def crawl(self) -> List[Dict[str, Any]]:
        """Crawl all RSS feeds for AI news"""
        products = []

        for feed_url, source_name in self.RSS_FEEDS:
            try:
                feed_products = self._crawl_feed(feed_url, source_name)
                products.extend(feed_products)
            except Exception as e:
                print(f"  ⚠ {source_name} RSS爬取失败: {e}")

        # Sort by date (most recent first)
        products.sort(
            key=lambda x: x.get('published_at', ''),
            reverse=True
        )

        return products[:30]  # Return top 30 most recent

    def _crawl_feed(self, feed_url: str, source_name: str) -> List[Dict[str, Any]]:
        """Crawl a single RSS feed"""
        products = []

        try:
            feed = feedparser.parse(feed_url)

            # Filter entries from last 7 days
            cutoff_date = datetime.now() - timedelta(days=7)

            for entry in feed.entries[:50]:  # Check top 50 entries
                try:
                    # Parse date
                    published = self._parse_entry_date(entry)
                    if not published or published < cutoff_date:
                        continue

                    title = entry.get('title', '').strip()
                    summary = entry.get('summary', '') or entry.get('description', '')
                    link = entry.get('link', '')

                    # Skip if already seen
                    if link in self.seen_urls:
                        continue

                    # Check if AI-related
                    text = f"{title} {summary}".lower()
                    if not self._is_ai_related(text):
                        continue

                    # Check if it's about a launch/update (not just news/opinion)
                    if not self._is_launch_news(text):
                        continue

                    # Extract product name from title
                    product_name = self._extract_product_name(title)
                    if not product_name:
                        continue

                    self.seen_urls.add(link)

                    # Clean description
                    description = self._clean_description(summary)

                    # Determine categories
                    categories = self._infer_categories(text)

                    # Create product entry
                    product = self.create_product(
                        name=product_name,
                        description=description,
                        logo_url=self._get_source_logo(source_name),
                        website=link,
                        categories=categories,
                        source='tech_news',
                        trending_score=85,  # High for news items
                        rating=4.0,
                        weekly_users=0,
                        published_at=published.isoformat() + 'Z',
                        extra={
                            'news_source': source_name,
                            'original_title': title,
                            'published_at': published.isoformat() + 'Z',
                            'is_news': True,
                        }
                    )

                    products.append(product)

                except Exception as e:
                    continue

            if products:
                print(f"  📰 {source_name}: 获取 {len(products)} 条AI新闻")

        except Exception as e:
            print(f"  ⚠ 解析 {source_name} RSS失败: {e}")

        return products

    def _parse_entry_date(self, entry) -> datetime:
        """Parse publication date from RSS entry"""
        date_fields = ['published_parsed', 'updated_parsed', 'created_parsed']

        for field in date_fields:
            parsed = entry.get(field)
            if parsed:
                try:
                    return datetime(*parsed[:6])
                except Exception:
                    continue

        # Try string parsing
        date_str = entry.get('published') or entry.get('updated')
        if date_str:
            try:
                # Common RSS date formats
                for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%S%z']:
                    try:
                        dt = datetime.strptime(date_str[:25], fmt[:len(date_str)])
                        return dt.replace(tzinfo=None)
                    except Exception:
                        continue
            except Exception:
                pass

        return None

    def _is_ai_related(self, text: str) -> bool:
        """Check if text is AI-related"""
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.AI_KEYWORDS)

    def _is_launch_news(self, text: str) -> bool:
        """Check if text is about a product launch/update"""
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.LAUNCH_KEYWORDS)

    def _extract_product_name(self, title: str) -> str:
        """Extract product/feature name from news title"""
        # Common patterns: "X launches Y", "X announces Y", "X's new Y"
        patterns = [
            r"(?:launches?|announces?|unveils?|introduces?|debuts?)\s+['\"]?([A-Z][A-Za-z0-9\s\-\.]+)['\"]?",
            r"([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*)\s+(?:launches?|announces?|unveils?|is here)",
            r"['\"]([^'\"]+)['\"]",  # Quoted product names
            r"new\s+([A-Z][A-Za-z0-9\s\-]+)",  # "new ProductName"
        ]

        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up
                name = re.sub(r'\s+', ' ', name)
                if len(name) > 3 and len(name) < 50:
                    return name

        # Fallback: use key parts of title
        # Remove common prefixes
        title_clean = re.sub(
            r'^(how|why|what|when|the|a|an|exclusive|breaking|report|review)\s+',
            '', title, flags=re.IGNORECASE
        )

        # Take first meaningful part
        parts = title_clean.split(':')[0].split('|')[0].split('—')[0]
        if len(parts) > 3 and len(parts) < 60:
            return parts.strip()

        return None

    def _clean_description(self, summary: str) -> str:
        """Clean HTML and truncate description"""
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', summary)
        # Remove extra whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        # Truncate
        if len(clean) > 200:
            clean = clean[:197] + '...'
        return clean

    def _infer_categories(self, text: str) -> List[str]:
        """Infer categories from text"""
        categories = []
        text_lower = text.lower()

        category_keywords = {
            'coding': ['code', 'coding', 'programming', 'developer', 'github', 'copilot', 'cursor', 'ide'],
            'image': ['image', 'photo', 'picture', 'diffusion', 'midjourney', 'dall-e', 'stable diffusion'],
            'video': ['video', 'sora', 'runway', 'pika', 'animation'],
            'voice': ['voice', 'speech', 'audio', 'whisper', 'eleven', 'tts'],
            'writing': ['writing', 'text', 'content', 'copywriting', 'document'],
            'education': ['education', 'learning', 'course', 'tutor', 'student'],
            'healthcare': ['health', 'medical', 'clinical', 'diagnosis'],
            'finance': ['finance', 'trading', 'investment', 'fintech'],
        }

        for cat, keywords in category_keywords.items():
            if any(kw in text_lower for kw in keywords):
                categories.append(cat)

        if not categories:
            categories = ['other']

        return categories[:2]  # Max 2 categories

    def _get_source_logo(self, source_name: str) -> str:
        """Get logo URL for news source"""
        logos = {
            'theverge': 'https://cdn.vox-cdn.com/uploads/chorus_asset/file/7395367/favicon-64x64.0.png',
            'techcrunch': 'https://techcrunch.com/wp-content/uploads/2015/02/cropped-cropped-favicon-gradient.png',
            'wired': 'https://www.wired.com/apple-touch-icon.png',
            'arstechnica': 'https://cdn.arstechnica.net/favicon.ico',
            'venturebeat': 'https://venturebeat.com/wp-content/themes/flavor/flavor-flavor/flavor_flavor/flavor/flavor/_starter-flavors/flavor/flavor/flavor/flavor/flavor_flavor/flavor/flavor/flavor-flavor/flavor-flavor/flavor-flavor-flavor/flavor_starter/flavor/flavors/flavor-flavor-starter/flavors/flavors/flavor-starter/assets/images/fav/favicon.png',
            'mit_tech_review': 'https://www.technologyreview.com/favicon.ico',
        }
        return logos.get(source_name, '')
