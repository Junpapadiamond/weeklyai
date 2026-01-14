"""
Y Combinator 公司目录爬虫
获取 YC 投资的 AI 相关初创公司
"""

import time
import random
import json
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base_spider import BaseSpider


class YCSpider(BaseSpider):
    """Y Combinator 公司目录爬虫 - 获取 YC 投资的 AI 公司"""

    BASE_URL = "https://www.ycombinator.com"
    COMPANIES_URL = "https://www.ycombinator.com/companies"

    # AI/ML 相关标签
    AI_TAGS = [
        'artificial-intelligence', 'machine-learning', 'deep-learning',
        'nlp', 'computer-vision', 'generative-ai', 'ai', 'ml',
        'llm', 'robotics', 'automation'
    ]

    # 最近的 YC 批次 (2023-2025)
    RECENT_BATCHES = ['W25', 'S24', 'W24', 'S23', 'W23']

    def __init__(self):
        super().__init__()
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

    def crawl(self) -> List[Dict[str, Any]]:
        """爬取 YC AI 相关公司"""
        products = []
        seen_names = set()

        print("  [YC] 获取 Y Combinator AI 公司...")

        # 方法1: 通过标签获取 AI 公司
        for tag in self.AI_TAGS[:3]:  # 限制请求数
            try:
                tag_products = self._fetch_by_tag(tag)
                for p in tag_products:
                    name = p.get('name', '').lower()
                    if name and name not in seen_names:
                        products.append(p)
                        seen_names.add(name)
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                print(f"    ✗ 获取标签 {tag} 失败: {e}")

        # 方法2: 获取最新批次的公司
        try:
            recent_products = self._fetch_recent_batches()
            for p in recent_products:
                name = p.get('name', '').lower()
                if name and name not in seen_names:
                    products.append(p)
                    seen_names.add(name)
        except Exception as e:
            print(f"    ✗ 获取最新批次失败: {e}")

        print(f"  [YC] 共获取 {len(products)} 个 YC 公司")
        return products

    def _fetch_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """通过标签获取公司"""
        products = []

        try:
            url = f"{self.COMPANIES_URL}?tags={tag}"
            response = self.session.get(url, timeout=15)

            if response.status_code != 200:
                return []

            # YC 页面可能使用 JavaScript 渲染
            # 尝试从页面中提取 JSON 数据
            products = self._parse_companies_page(response.text)

        except Exception as e:
            pass

        return products

    def _fetch_recent_batches(self) -> List[Dict[str, Any]]:
        """获取最近批次的公司"""
        products = []

        for batch in self.RECENT_BATCHES[:2]:  # 限制批次数
            try:
                url = f"{self.COMPANIES_URL}?batch={batch}"
                response = self.session.get(url, timeout=15)

                if response.status_code != 200:
                    continue

                batch_products = self._parse_companies_page(response.text)

                # 筛选 AI 相关
                for p in batch_products:
                    if self._is_ai_related(p):
                        p['extra'] = p.get('extra', {})
                        p['extra']['yc_batch'] = batch
                        products.append(p)

                time.sleep(random.uniform(1, 2))

            except Exception:
                continue

        return products

    def _parse_companies_page(self, html: str) -> List[Dict[str, Any]]:
        """解析公司页面"""
        products = []
        soup = BeautifulSoup(html, 'html.parser')

        # 尝试从 script 标签中提取 JSON 数据
        scripts = soup.find_all('script')
        for script in scripts:
            text = script.string or ''
            if 'companies' in text.lower() and '{' in text:
                try:
                    # 尝试找到 JSON 数据
                    start = text.find('[{')
                    end = text.rfind('}]') + 2
                    if start > -1 and end > start:
                        json_str = text[start:end]
                        data = json.loads(json_str)
                        if isinstance(data, list):
                            for item in data[:50]:
                                product = self._parse_company_json(item)
                                if product:
                                    products.append(product)
                except json.JSONDecodeError:
                    continue

        # 如果没有找到 JSON，解析 HTML 结构
        if not products:
            company_cards = soup.select('[class*="company"], .company-card, article')
            for card in company_cards[:50]:
                try:
                    product = self._parse_company_card(card)
                    if product:
                        products.append(product)
                except Exception:
                    continue

        return products

    def _parse_company_json(self, data: Dict) -> Dict[str, Any]:
        """解析 JSON 格式的公司数据"""
        name = data.get('name', '')
        if not name:
            return None

        description = data.get('one_liner', '') or data.get('long_description', '') or ''
        website = data.get('website', '') or data.get('url', '')
        logo_url = data.get('small_logo_thumb_url', '') or data.get('logo', '')

        # 检查是否 AI 相关
        if not self._is_ai_related_text(f"{name} {description}"):
            tags = data.get('tags', []) or data.get('industries', [])
            if not any(self._is_ai_tag(t) for t in tags):
                return None

        # 提取批次
        batch = data.get('batch', '')

        # 分类
        categories = self._infer_categories(f"{name} {description}")

        # 评分 (YC 公司有一定的背书)
        trending_score = 80
        if batch in self.RECENT_BATCHES[:2]:  # 最新批次
            trending_score = 88

        return self.create_product(
            name=name,
            description=description[:300] if description else '',
            logo_url=logo_url,
            website=website,
            categories=categories if categories else ['other'],
            trending_score=trending_score,
            source='ycombinator',
            extra={
                'yc_batch': batch,
                'discovered_at': datetime.utcnow().isoformat(),
            }
        )

    def _parse_company_card(self, card) -> Dict[str, Any]:
        """解析 HTML 格式的公司卡片"""
        # 提取名称
        name_elem = card.select_one('h2, h3, .name, [class*="name"]')
        name = name_elem.get_text(strip=True) if name_elem else ''

        if not name:
            return None

        # 提取描述
        desc_elem = card.select_one('p, .description, [class*="description"]')
        description = desc_elem.get_text(strip=True) if desc_elem else ''

        # 检查是否 AI 相关
        if not self._is_ai_related_text(f"{name} {description}"):
            return None

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

        categories = self._infer_categories(f"{name} {description}")

        return self.create_product(
            name=name,
            description=description[:300] if description else '',
            logo_url=logo_url,
            website=website,
            categories=categories if categories else ['other'],
            trending_score=80,
            source='ycombinator',
            extra={
                'discovered_at': datetime.utcnow().isoformat(),
            }
        )

    def _is_ai_related(self, product: Dict) -> bool:
        """检查产品是否 AI 相关"""
        name = product.get('name', '')
        description = product.get('description', '')
        return self._is_ai_related_text(f"{name} {description}")

    def _is_ai_related_text(self, text: str) -> bool:
        """检查文本是否 AI 相关"""
        text_lower = text.lower()
        ai_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'ml',
            'deep learning', 'neural', 'nlp', 'gpt', 'llm',
            'computer vision', 'automation', 'robotics', 'generative',
            'chatbot', 'intelligent', 'predictive', 'recommendation'
        ]
        return any(kw in text_lower for kw in ai_keywords)

    def _is_ai_tag(self, tag: str) -> bool:
        """检查标签是否 AI 相关"""
        tag_lower = (tag or '').lower().replace(' ', '-')
        return any(ai_tag in tag_lower for ai_tag in self.AI_TAGS)

    def _infer_categories(self, text: str) -> List[str]:
        """从文本推断分类"""
        text_lower = text.lower()
        categories = set()

        keyword_mapping = {
            'coding': ['code', 'developer', 'programming', 'api', 'devtools', 'infrastructure'],
            'image': ['image', 'photo', 'design', 'art', 'visual', 'creative'],
            'video': ['video', 'animation', 'movie', 'film', 'streaming'],
            'voice': ['voice', 'audio', 'speech', 'music', 'sound'],
            'writing': ['write', 'writing', 'content', 'text', 'copy', 'document'],
            'finance': ['finance', 'fintech', 'banking', 'payment', 'trading'],
            'healthcare': ['health', 'medical', 'biotech', 'clinical', 'pharma'],
            'education': ['learn', 'education', 'edtech', 'course', 'training'],
            'hardware': ['hardware', 'robotics', 'chip', 'sensor', 'device'],
        }

        for category, keywords in keyword_mapping.items():
            if any(kw in text_lower for kw in keywords):
                categories.add(category)

        return list(categories)
