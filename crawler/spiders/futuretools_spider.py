"""
FutureTools.io AI 工具目录爬虫
获取最新上架的 AI 工具
"""

import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base_spider import BaseSpider


class FutureToolsSpider(BaseSpider):
    """FutureTools.io 爬虫 - AI 工具目录"""

    BASE_URL = "https://www.futuretools.io"

    # 分类映射
    CATEGORY_MAPPING = {
        'copywriting': 'writing',
        'text': 'writing',
        'content': 'writing',
        'code': 'coding',
        'developer': 'coding',
        'programming': 'coding',
        'image': 'image',
        'art': 'image',
        'design': 'image',
        'video': 'video',
        'audio': 'voice',
        'music': 'voice',
        'voice': 'voice',
        'speech': 'voice',
        'finance': 'finance',
        'education': 'education',
        'learning': 'education',
        'health': 'healthcare',
        'medical': 'healthcare',
        'productivity': 'other',
        'assistant': 'other',
    }

    def __init__(self):
        super().__init__()
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': self.BASE_URL,
        })

    def crawl(self) -> List[Dict[str, Any]]:
        """爬取 FutureTools.io AI 工具"""
        products = []
        seen_names = set()

        print("  [FutureTools] 获取 AI 工具目录...")

        # 获取最新工具页面
        try:
            page_products = self._fetch_tools_page()
            for p in page_products:
                name = p.get('name', '').lower()
                if name and name not in seen_names:
                    products.append(p)
                    seen_names.add(name)
        except Exception as e:
            print(f"    ✗ 获取工具页面失败: {e}")

        # 也可以尝试获取 "New" 分类
        try:
            new_products = self._fetch_new_tools()
            for p in new_products:
                name = p.get('name', '').lower()
                if name and name not in seen_names:
                    products.append(p)
                    seen_names.add(name)
        except Exception as e:
            print(f"    ✗ 获取新工具失败: {e}")

        print(f"  [FutureTools] 共获取 {len(products)} 个 AI 工具")
        return products

    def _fetch_tools_page(self) -> List[Dict[str, Any]]:
        """获取工具主页"""
        products = []

        try:
            # FutureTools 主页会显示一些工具
            response = self.session.get(f"{self.BASE_URL}/tools", timeout=15)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找工具卡片 (根据页面结构调整选择器)
            tool_cards = soup.select('.tool-card, .card, [class*="tool"], article')

            for card in tool_cards[:50]:
                try:
                    product = self._parse_tool_card(card)
                    if product:
                        products.append(product)
                except Exception:
                    continue

            time.sleep(random.uniform(1, 2))

        except Exception as e:
            print(f"    解析页面失败: {e}")

        return products

    def _fetch_new_tools(self) -> List[Dict[str, Any]]:
        """获取新上架的工具"""
        products = []

        try:
            # 尝试获取新工具页面
            response = self.session.get(f"{self.BASE_URL}/tools?sort=new", timeout=15)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找工具卡片
            tool_cards = soup.select('.tool-card, .card, [class*="tool"], article')

            for card in tool_cards[:30]:
                try:
                    product = self._parse_tool_card(card)
                    if product:
                        products.append(product)
                except Exception:
                    continue

        except Exception as e:
            pass

        return products

    def _parse_tool_card(self, card) -> Dict[str, Any]:
        """解析工具卡片"""
        # 提取名称
        name_elem = card.select_one('h2, h3, h4, .title, .name, [class*="title"]')
        name = name_elem.get_text(strip=True) if name_elem else ''

        if not name or len(name) < 2:
            return None

        # 提取描述
        desc_elem = card.select_one('p, .description, .desc, [class*="description"]')
        description = desc_elem.get_text(strip=True) if desc_elem else ''

        # 提取链接
        link_elem = card.select_one('a[href]')
        website = ''
        if link_elem:
            href = link_elem.get('href', '')
            if href.startswith('http'):
                website = href
            elif href.startswith('/'):
                website = f"{self.BASE_URL}{href}"

        # 提取 logo
        img_elem = card.select_one('img')
        logo_url = ''
        if img_elem:
            logo_url = img_elem.get('src', '') or img_elem.get('data-src', '')
            if logo_url and not logo_url.startswith('http'):
                if logo_url.startswith('/'):
                    logo_url = f"{self.BASE_URL}{logo_url}"

        # 提取分类
        category_elem = card.select_one('.category, .tag, [class*="category"]')
        category_text = category_elem.get_text(strip=True).lower() if category_elem else ''
        categories = self._map_category(category_text)

        if not categories:
            categories = self._infer_categories(f"{name} {description}")

        # 基础评分
        trending_score = 70  # FutureTools 收录的工具有一定质量

        return self.create_product(
            name=name,
            description=description[:300] if description else '',
            logo_url=logo_url,
            website=website,
            categories=categories if categories else ['other'],
            trending_score=trending_score,
            source='futuretools',
            extra={
                'discovered_at': datetime.utcnow().isoformat(),
            }
        )

    def _map_category(self, category_text: str) -> List[str]:
        """映射分类"""
        categories = []
        text_lower = category_text.lower()

        for keyword, category in self.CATEGORY_MAPPING.items():
            if keyword in text_lower and category not in categories:
                categories.append(category)

        return categories

    def _infer_categories(self, text: str) -> List[str]:
        """从文本推断分类"""
        text_lower = text.lower()
        categories = set()

        keyword_mapping = {
            'coding': ['code', 'developer', 'programming', 'api', 'github', 'ide'],
            'image': ['image', 'photo', 'design', 'art', 'draw', 'paint', 'graphic'],
            'video': ['video', 'animation', 'movie', 'film'],
            'voice': ['voice', 'audio', 'speech', 'music', 'sound', 'podcast'],
            'writing': ['write', 'writing', 'content', 'text', 'copy', 'blog', 'article'],
            'finance': ['finance', 'trading', 'invest', 'stock'],
            'healthcare': ['health', 'medical', 'fitness'],
            'education': ['learn', 'education', 'study', 'course', 'tutor'],
        }

        for category, keywords in keyword_mapping.items():
            if any(kw in text_lower for kw in keywords):
                categories.add(category)

        return list(categories)
