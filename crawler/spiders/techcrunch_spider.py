"""
TechCrunch 融资新闻爬虫
专注获取刚融资的 AI 初创公司
"""

import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import feedparser
from .base_spider import BaseSpider


class TechCrunchSpider(BaseSpider):
    """TechCrunch 融资新闻爬虫 - 获取刚融资的 AI 初创公司"""

    # TechCrunch RSS feeds
    RSS_FEEDS = [
        "https://techcrunch.com/category/startups/feed/",
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://techcrunch.com/tag/funding/feed/",
    ]

    # AI 关键词
    AI_KEYWORDS = [
        'ai', 'artificial intelligence', 'machine learning', 'ml',
        'gpt', 'llm', 'deep learning', 'neural', 'nlp',
        'generative', 'chatbot', 'automation', 'robotics',
        'computer vision', 'speech', 'natural language'
    ]

    # 融资关键词
    FUNDING_KEYWORDS = [
        'raises', 'raised', 'funding', 'series a', 'series b', 'series c',
        'seed round', 'seed funding', 'million', 'billion', 'valuation',
        'investment', 'investors', 'led by', 'backed by', 'venture',
        '融资', '投资', 'funding round'
    ]

    def __init__(self):
        super().__init__()
        self.session.headers.update({
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        })

    def crawl(self) -> List[Dict[str, Any]]:
        """爬取 TechCrunch AI 融资新闻"""
        products = []
        seen_names = set()

        print("  [TechCrunch] 获取 AI 融资新闻...")

        for feed_url in self.RSS_FEEDS:
            try:
                feed_products = self._fetch_rss_feed(feed_url)
                for p in feed_products:
                    name = p.get('name', '').lower()
                    if name and name not in seen_names:
                        products.append(p)
                        seen_names.add(name)
                time.sleep(random.uniform(0.5, 1.0))
            except Exception as e:
                print(f"    ✗ RSS 获取失败 {feed_url}: {e}")

        print(f"  [TechCrunch] 共获取 {len(products)} 个融资产品")
        return products

    def _fetch_rss_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """解析 RSS Feed"""
        products = []
        since = datetime.utcnow() - timedelta(days=14)  # 最近14天

        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:30]:
                try:
                    product = self._parse_entry(entry, since)
                    if product:
                        products.append(product)
                except Exception:
                    continue

        except Exception as e:
            print(f"    解析 RSS 失败: {e}")

        return products

    def _parse_entry(self, entry: Dict, since: datetime) -> Dict[str, Any]:
        """解析单个 RSS 条目"""
        title = entry.get('title', '')
        summary = entry.get('summary', '') or entry.get('description', '')
        link = entry.get('link', '')

        if not title:
            return None

        # 检查发布日期
        pub_date = None
        if 'published_parsed' in entry and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6])
        elif 'updated_parsed' in entry and entry.updated_parsed:
            pub_date = datetime(*entry.updated_parsed[:6])

        if pub_date and pub_date < since:
            return None

        # 检查是否是 AI 相关
        text = f"{title} {summary}".lower()
        is_ai = any(kw in text for kw in self.AI_KEYWORDS)

        if not is_ai:
            return None

        # 检查是否是融资新闻
        is_funding = any(kw in text for kw in self.FUNDING_KEYWORDS)

        # 提取公司名称
        company_name = self._extract_company_name(title)
        if not company_name:
            return None

        # 提取融资金额
        funding_amount = self._extract_funding_amount(f"{title} {summary}")

        # 推断分类
        categories = self._infer_categories(text)

        # 计算评分 (融资新闻优先级更高)
        trending_score = 75
        if is_funding:
            trending_score = 85
            if funding_amount and funding_amount >= 10:  # $10M+
                trending_score = 90
            if funding_amount and funding_amount >= 50:  # $50M+
                trending_score = 95

        extra = {
            'funding_amount': funding_amount,
            'is_funding_news': is_funding,
            'original_title': title,
        }
        if pub_date:
            extra['published_at'] = pub_date.isoformat()

        return self.create_product(
            name=company_name,
            description=self._clean_description(summary),
            logo_url='',  # TechCrunch RSS 不提供 logo
            website=link,
            categories=categories if categories else ['other'],
            trending_score=trending_score,
            source='techcrunch',
            extra=extra,
            published_at=pub_date.isoformat() if pub_date else None
        )

    def _extract_company_name(self, title: str) -> str:
        """从标题中提取公司名称"""
        # 常见模式: "CompanyName raises $XM..." or "AI startup CompanyName..."

        # 移除常见的前缀后缀
        title = title.strip()

        # 模式1: "X raises/raised $Y"
        for keyword in ['raises', 'raised', 'secures', 'closes', 'lands', 'gets']:
            if keyword in title.lower():
                parts = title.split()
                for i, word in enumerate(parts):
                    if word.lower() == keyword:
                        # 公司名是 keyword 之前的部分
                        company = ' '.join(parts[:i])
                        # 清理
                        company = company.replace("'s", "").strip()
                        # 移除常见前缀
                        for prefix in ['AI startup', 'Startup', 'AI company', 'Company']:
                            if company.lower().startswith(prefix.lower()):
                                company = company[len(prefix):].strip()
                        if len(company) > 2 and len(company) < 50:
                            return company
                        break

        # 模式2: 用第一个单词/短语作为公司名
        parts = title.split(',')[0].split(':')[0].split(' - ')[0]
        parts = parts.split()
        if len(parts) >= 1 and len(parts) <= 4:
            company = ' '.join(parts)
            if len(company) > 2 and len(company) < 40:
                return company

        return ''

    def _extract_funding_amount(self, text: str) -> float:
        """提取融资金额 (单位: 百万美元)"""
        import re

        # 匹配 $XXM 或 $XX million
        patterns = [
            r'\$(\d+(?:\.\d+)?)\s*[Mm](?:illion)?',  # $10M, $10 million
            r'\$(\d+(?:\.\d+)?)\s*[Bb](?:illion)?',  # $1B, $1 billion (convert to M)
        ]

        for i, pattern in enumerate(patterns):
            match = re.search(pattern, text)
            if match:
                amount = float(match.group(1))
                if i == 1:  # billion
                    amount *= 1000
                return amount

        return None

    def _clean_description(self, text: str) -> str:
        """清理描述文本"""
        # 移除 HTML 标签
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()

        # 截断
        if len(text) > 300:
            text = text[:297] + '...'

        return text.strip()

    def _infer_categories(self, text: str) -> List[str]:
        """从文本推断分类"""
        text_lower = text.lower()
        categories = set()

        keyword_mapping = {
            'coding': ['code', 'developer', 'programming', 'api', 'github', 'ide', 'devops'],
            'image': ['image', 'photo', 'design', 'art', 'visual', 'graphics'],
            'video': ['video', 'animation', 'movie', 'film', 'streaming'],
            'voice': ['voice', 'audio', 'speech', 'music', 'sound', 'podcast'],
            'writing': ['write', 'writing', 'content', 'text', 'copy', 'document', 'editor'],
            'finance': ['finance', 'trading', 'invest', 'fintech', 'banking', 'payment'],
            'healthcare': ['health', 'medical', 'fitness', 'biotech', 'pharma', 'clinical'],
            'education': ['learn', 'education', 'study', 'course', 'edtech', 'training'],
            'hardware': ['chip', 'hardware', 'robotics', 'sensor', 'device', 'semiconductor'],
        }

        for category, keywords in keyword_mapping.items():
            if any(kw in text_lower for kw in keywords):
                categories.add(category)

        return list(categories)
