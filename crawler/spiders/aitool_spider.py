"""
AI工具导航网站爬虫
爬取各类 AI 工具目录网站（如 Futurepedia, There's An AI For That 等）
"""

import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base_spider import BaseSpider


class AIToolSpider(BaseSpider):
    """AI 工具导航网站爬虫"""
    
    # 目标网站列表
    SOURCES = {
        'toolify': {
            'url': 'https://www.toolify.ai/Best-AI-Tools',
            'name': 'Toolify.ai'
        },
        'aitoptools': {
            'url': 'https://aitoptools.com',
            'name': 'AI Top Tools'
        },
        'topai': {
            'url': 'https://topai.tools',
            'name': 'TopAI.tools'
        }
    }
    
    def crawl(self) -> List[Dict[str, Any]]:
        """爬取 AI 工具导航网站"""
        products = []
        
        # 爬取 Toolify
        print("  [AITools] 爬取 Toolify.ai...")
        try:
            toolify_products = self._crawl_toolify()
            products.extend(toolify_products)
            print(f"    ✓ 获取 {len(toolify_products)} 个产品")
        except Exception as e:
            print(f"    ✗ Toolify 爬取失败: {e}")
        
        # 爬取 AI Top Tools
        print("  [AITools] 爬取 AI Top Tools...")
        try:
            aitop_products = self._crawl_aitoptools()
            products.extend(aitop_products)
            print(f"    ✓ 获取 {len(aitop_products)} 个产品")
        except Exception as e:
            print(f"    ✗ AI Top Tools 爬取失败: {e}")
        
        print(f"  [AITools] 共获取 {len(products)} 个产品")
        return products
    
    def _crawl_toolify(self) -> List[Dict[str, Any]]:
        """爬取 Toolify.ai"""
        url = self.SOURCES['toolify']['url']
        
        response = self.fetch(url)
        soup = BeautifulSoup(response.text, 'lxml')
        
        products = []
        
        # 查找产品卡片
        cards = soup.select('.tool-card, [class*="ToolCard"], article')
        
        for card in cards[:30]:
            try:
                product = self._parse_toolify_card(card)
                if product:
                    products.append(product)
            except:
                continue
        
        return products
    
    def _parse_toolify_card(self, card) -> Dict[str, Any]:
        """解析 Toolify 产品卡片"""
        # 获取名称
        name_elem = card.select_one('h2, h3, [class*="title"], [class*="name"]')
        name = name_elem.get_text(strip=True) if name_elem else ''
        
        if not name or len(name) < 2:
            return None
        
        # 获取描述
        desc_elem = card.select_one('p, [class*="description"], [class*="desc"]')
        description = desc_elem.get_text(strip=True) if desc_elem else ''
        
        # 获取链接
        link_elem = card.select_one('a[href]')
        website = ''
        if link_elem:
            href = link_elem.get('href', '')
            if href.startswith('http'):
                website = href
            elif href.startswith('/'):
                website = f"https://www.toolify.ai{href}"
        
        # 获取Logo
        img_elem = card.select_one('img')
        logo_url = ''
        if img_elem:
            logo_url = img_elem.get('src', '') or img_elem.get('data-src', '')
        
        # 获取分类标签
        tag_elems = card.select('[class*="tag"], [class*="category"], .badge')
        categories = []
        for tag in tag_elems:
            cat = self._map_category(tag.get_text(strip=True))
            if cat:
                categories.append(cat)
        
        if not categories:
            categories = self._infer_categories(f"{name} {description}")
        
        return self.create_product(
            name=name,
            description=description,
            logo_url=logo_url,
            website=website,
            categories=categories if categories else ['other'],
            trending_score=70,
            source='toolify'
        )
    
    def _crawl_aitoptools(self) -> List[Dict[str, Any]]:
        """爬取 AI Top Tools"""
        url = self.SOURCES['aitoptools']['url']
        
        try:
            response = self.fetch(url)
            soup = BeautifulSoup(response.text, 'lxml')
        except:
            return []
        
        products = []
        
        # 查找产品列表
        items = soup.select('.tool-item, [class*="tool"], article, .card')
        
        for item in items[:30]:
            try:
                name_elem = item.select_one('h2, h3, h4, [class*="title"]')
                name = name_elem.get_text(strip=True) if name_elem else ''
                
                if not name or len(name) < 2:
                    continue
                
                desc_elem = item.select_one('p, [class*="desc"]')
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                
                link_elem = item.select_one('a[href^="http"]')
                website = link_elem.get('href', '') if link_elem else ''
                
                categories = self._infer_categories(f"{name} {description}")
                
                product = self.create_product(
                    name=name,
                    description=description,
                    logo_url='',
                    website=website,
                    categories=categories if categories else ['other'],
                    trending_score=65,
                    source='aitoptools'
                )
                products.append(product)
                
            except:
                continue
        
        return products
    
    def _map_category(self, tag: str) -> str:
        """将标签映射到分类"""
        tag_lower = tag.lower()
        
        mapping = {
            'code': 'coding',
            'coding': 'coding',
            'developer': 'coding',
            'programming': 'coding',
            'image': 'image',
            'art': 'image',
            'design': 'image',
            'photo': 'image',
            'video': 'video',
            'animation': 'video',
            'audio': 'voice',
            'voice': 'voice',
            'speech': 'voice',
            'music': 'voice',
            'writing': 'writing',
            'text': 'writing',
            'content': 'writing',
            'copy': 'writing',
            'finance': 'finance',
            'trading': 'finance',
            'health': 'healthcare',
            'medical': 'healthcare',
            'education': 'education',
            'learning': 'education',
        }
        
        for keyword, category in mapping.items():
            if keyword in tag_lower:
                return category
        
        return ''
    
    def _infer_categories(self, text: str) -> List[str]:
        """从文本推断分类"""
        text_lower = text.lower()
        categories = set()
        
        keyword_mapping = {
            'coding': ['code', 'developer', 'programming', 'api', 'github', 'ide'],
            'image': ['image', 'photo', 'design', 'art', 'draw', 'paint', 'picture'],
            'video': ['video', 'animation', 'movie', 'film'],
            'voice': ['voice', 'audio', 'speech', 'music', 'sound', 'podcast'],
            'writing': ['write', 'writing', 'content', 'text', 'copy', 'blog', 'article'],
            'finance': ['finance', 'trading', 'invest', 'stock', 'crypto'],
            'healthcare': ['health', 'medical', 'fitness', 'wellness'],
            'education': ['learn', 'education', 'study', 'course', 'tutor'],
        }
        
        for category, keywords in keyword_mapping.items():
            if any(kw in text_lower for kw in keywords):
                categories.add(category)
        
        return list(categories)


