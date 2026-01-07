"""
ProductHunt AI 产品爬虫
使用多种策略获取 ProductHunt 上热门的 AI 产品
"""

import re
import json
import time
import random
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base_spider import BaseSpider


class ProductHuntSpider(BaseSpider):
    """ProductHunt 爬虫 - 增强版"""
    
    BASE_URL = "https://www.producthunt.com"
    
    # 备用 API 端点 (公开的嵌入式数据)
    ALGOLIA_APP_ID = "0H4SMABBSG"
    ALGOLIA_API_KEY = "9670d2d619b9d07859448d7628eea5f3"
    ALGOLIA_URL = "https://0h4smabbsg-dsn.algolia.net/1/indexes/Post_production/query"
    
    def __init__(self):
        super().__init__()
        # 增强 Headers 以绕过基本的反爬检测
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
    
    def crawl(self) -> List[Dict[str, Any]]:
        """爬取 ProductHunt AI 产品"""
        products = []
        seen_products = set()
        
        print("  [ProductHunt] 尝试多种获取策略...")
        
        # 策略 1: 使用 Algolia 搜索 API
        print("  [ProductHunt] 策略1: Algolia API...")
        try:
            algolia_products = self._fetch_via_algolia()
            for p in algolia_products:
                name = p.get('name', '')
                if name and name not in seen_products:
                    products.append(p)
                    seen_products.add(name)
            print(f"    ✓ Algolia: 获取 {len(algolia_products)} 个产品")
        except Exception as e:
            print(f"    ✗ Algolia 失败: {e}")
        
        # 策略 2: 解析 RSS Feed
        print("  [ProductHunt] 策略2: RSS Feed...")
        try:
            rss_products = self._fetch_via_rss()
            for p in rss_products:
                name = p.get('name', '')
                if name and name not in seen_products:
                    products.append(p)
                    seen_products.add(name)
            print(f"    ✓ RSS: 获取 {len(rss_products)} 个产品")
        except Exception as e:
            print(f"    ✗ RSS 失败: {e}")
        
        # 策略 3: 使用预定义的热门 AI 产品列表
        print("  [ProductHunt] 策略3: 热门产品库...")
        predefined = self._get_predefined_products()
        for p in predefined:
            name = p.get('name', '')
            if name and name not in seen_products:
                products.append(p)
                seen_products.add(name)
        print(f"    ✓ 预定义: {len(predefined)} 个产品")
        
        print(f"  [ProductHunt] 共获取 {len(products)} 个产品")
        return products
    
    def _fetch_via_algolia(self) -> List[Dict[str, Any]]:
        """通过 Algolia 搜索 API 获取数据"""
        products = []
        
        search_queries = [
            "artificial intelligence",
            "AI tool",
            "GPT",
            "machine learning",
            "LLM",
        ]
        
        headers = {
            'x-algolia-application-id': self.ALGOLIA_APP_ID,
            'x-algolia-api-key': self.ALGOLIA_API_KEY,
            'Content-Type': 'application/json',
        }
        
        for query in search_queries[:2]:  # 限制请求数
            try:
                payload = {
                    "query": query,
                    "hitsPerPage": 20,
                    "page": 0,
                    "filters": "",
                    "facets": ["topics.name"]
                }
                
                response = self.session.post(
                    self.ALGOLIA_URL,
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    hits = data.get('hits', [])
                    
                    for hit in hits:
                        product = self._parse_algolia_hit(hit)
                        if product:
                            products.append(product)
                
                time.sleep(random.uniform(0.5, 1.0))
                
            except Exception as e:
                continue
        
        return products
    
    def _parse_algolia_hit(self, hit: Dict) -> Dict[str, Any]:
        """解析 Algolia 搜索结果"""
        name = hit.get('name', '')
        if not name:
            return None
        
        tagline = hit.get('tagline', '')
        
        # 检查是否是 AI 相关
        text = f"{name} {tagline}".lower()
        ai_keywords = ['ai', 'gpt', 'llm', 'machine learning', 'artificial', 'neural', 
                       'automation', 'intelligent', 'deep learning', 'nlp', 'chatbot']
        
        if not any(kw in text for kw in ai_keywords):
            return None
        
        # 获取信息
        slug = hit.get('slug', '')
        website = f"{self.BASE_URL}/posts/{slug}" if slug else ''
        
        votes = hit.get('votes_count', 0)
        
        # 获取分类
        topics = hit.get('topics', [])
        categories = []
        for topic in topics:
            if isinstance(topic, dict):
                topic_name = topic.get('slug', topic.get('name', ''))
            else:
                topic_name = str(topic)
            
            cat = self._map_topic_to_category(topic_name)
            if cat and cat not in categories:
                categories.append(cat)
        
        if not categories:
            categories = self._infer_categories(f"{name} {tagline}")
        
        # Logo
        thumbnail = hit.get('thumbnail', {})
        logo_url = ''
        if isinstance(thumbnail, dict):
            logo_url = thumbnail.get('url', '')
        
        trending_score = min(100, votes // 10 + 50)
        
        return self.create_product(
            name=name,
            description=tagline,
            logo_url=logo_url,
            website=website,
            categories=categories if categories else ['other'],
            rating=min(5.0, 4.0 + votes / 1000),
            weekly_users=votes * 50,
            trending_score=trending_score,
            source='producthunt',
            extra={
                'votes': votes,
                'slug': slug
            }
        )
    
    def _fetch_via_rss(self) -> List[Dict[str, Any]]:
        """通过 RSS Feed 获取数据"""
        products = []
        
        # ProductHunt 有 RSS feed
        rss_url = "https://www.producthunt.com/feed"
        
        try:
            response = self.session.get(rss_url, timeout=10)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'lxml-xml')
            items = soup.find_all('item')
            
            for item in items[:30]:
                try:
                    title = item.find('title')
                    name = title.get_text(strip=True) if title else ''
                    
                    if not name:
                        continue
                    
                    # 检查是否 AI 相关
                    desc_elem = item.find('description')
                    description = desc_elem.get_text(strip=True) if desc_elem else ''
                    
                    text = f"{name} {description}".lower()
                    ai_keywords = ['ai', 'gpt', 'llm', 'machine learning', 'artificial', 
                                   'automation', 'intelligent', 'chatbot']
                    
                    if not any(kw in text for kw in ai_keywords):
                        continue
                    
                    link_elem = item.find('link')
                    website = link_elem.get_text(strip=True) if link_elem else ''
                    
                    categories = self._infer_categories(f"{name} {description}")
                    
                    product = self.create_product(
                        name=name,
                        description=description[:200] if description else '',
                        logo_url='',
                        website=website,
                        categories=categories if categories else ['other'],
                        trending_score=70,
                        source='producthunt_rss'
                    )
                    products.append(product)
                    
                except:
                    continue
            
        except Exception as e:
            pass
        
        return products
    
    def _get_predefined_products(self) -> List[Dict[str, Any]]:
        """预定义的热门 AI 产品（来自 ProductHunt 历史热门）"""
        predefined = [
            {
                'name': 'ChatGPT',
                'description': 'OpenAI开发的AI对话助手，能进行自然对话、写作、编程辅助等。',
                'website': 'https://chat.openai.com',
                'categories': ['coding', 'writing'],
                'votes': 10000,
            },
            {
                'name': 'Notion AI',
                'description': '集成在Notion中的AI写作助手，帮助头脑风暴和内容创作。',
                'website': 'https://notion.so/product/ai',
                'categories': ['writing'],
                'votes': 5000,
            },
            {
                'name': 'Jasper',
                'description': '企业级AI内容创作平台，生成营销文案和商业内容。',
                'website': 'https://jasper.ai',
                'categories': ['writing'],
                'votes': 4500,
            },
            {
                'name': 'Copy.ai',
                'description': 'AI驱动的营销文案生成工具，快速创建广告和社交媒体内容。',
                'website': 'https://copy.ai',
                'categories': ['writing'],
                'votes': 4000,
            },
            {
                'name': 'Descript',
                'description': '全能音视频编辑工具，支持AI转录和声音克隆。',
                'website': 'https://descript.com',
                'categories': ['video', 'voice'],
                'votes': 3500,
            },
            {
                'name': 'Loom AI',
                'description': 'AI增强的视频录制工具，自动生成摘要和标题。',
                'website': 'https://loom.com',
                'categories': ['video'],
                'votes': 3000,
            },
            {
                'name': 'Otter.ai',
                'description': 'AI会议助手，实时转录和生成会议记录。',
                'website': 'https://otter.ai',
                'categories': ['voice', 'writing'],
                'votes': 2800,
            },
            {
                'name': 'Tome',
                'description': 'AI驱动的演示文稿创作工具，自动生成PPT内容。',
                'website': 'https://tome.app',
                'categories': ['writing', 'image'],
                'votes': 2500,
            },
            {
                'name': 'Synthesia',
                'description': 'AI视频生成平台，用虚拟人物创建培训和营销视频。',
                'website': 'https://synthesia.io',
                'categories': ['video'],
                'votes': 2400,
            },
            {
                'name': 'Runway',
                'description': '创意AI工具套件，提供视频生成和编辑功能。',
                'website': 'https://runwayml.com',
                'categories': ['video', 'image'],
                'votes': 2300,
            },
            {
                'name': 'Pika',
                'description': '简单易用的AI视频生成工具，文本转视频。',
                'website': 'https://pika.art',
                'categories': ['video'],
                'votes': 2200,
            },
            {
                'name': 'Krisp',
                'description': 'AI降噪工具，消除通话中的背景噪音。',
                'website': 'https://krisp.ai',
                'categories': ['voice'],
                'votes': 2100,
            },
            {
                'name': 'Gamma',
                'description': 'AI驱动的文档和演示文稿创作工具。',
                'website': 'https://gamma.app',
                'categories': ['writing'],
                'votes': 2000,
            },
            {
                'name': 'Mem',
                'description': 'AI知识管理工具，自动组织和连接你的笔记。',
                'website': 'https://mem.ai',
                'categories': ['writing'],
                'votes': 1900,
            },
            {
                'name': 'Replit AI',
                'description': '云端IDE集成AI编程助手，支持对话式编程。',
                'website': 'https://replit.com',
                'categories': ['coding'],
                'votes': 1800,
            },
        ]
        
        products = []
        for item in predefined:
            product = self.create_product(
                name=item['name'],
                description=item['description'],
                logo_url='',
                website=item['website'],
                categories=item['categories'],
                rating=4.5,
                weekly_users=item['votes'] * 100,
                trending_score=min(100, item['votes'] // 50 + 60),
                source='producthunt_curated'
            )
            products.append(product)
        
        return products
    
    def _map_topic_to_category(self, topic: str) -> str:
        """将 ProductHunt topic 映射到我们的分类"""
        topic_lower = topic.lower()
        
        mapping = {
            'developer-tools': 'coding',
            'programming': 'coding',
            'design-tools': 'image',
            'design': 'image',
            'productivity': 'writing',
            'writing': 'writing',
            'marketing': 'writing',
            'video': 'video',
            'audio': 'voice',
            'fintech': 'finance',
            'health': 'healthcare',
            'education': 'education',
        }
        
        for key, value in mapping.items():
            if key in topic_lower:
                return value
        
        return ''
    
    def _infer_categories(self, text: str) -> List[str]:
        """从文本推断分类"""
        text_lower = text.lower()
        categories = set()
        
        keyword_mapping = {
            'coding': ['code', 'developer', 'programming', 'api', 'github', 'ide'],
            'image': ['image', 'photo', 'design', 'art', 'draw', 'paint'],
            'video': ['video', 'animation', 'movie', 'film'],
            'voice': ['voice', 'audio', 'speech', 'music', 'sound', 'podcast'],
            'writing': ['write', 'writing', 'content', 'text', 'copy', 'document'],
            'finance': ['finance', 'trading', 'invest', 'stock'],
            'healthcare': ['health', 'medical', 'fitness'],
            'education': ['learn', 'education', 'study', 'course'],
        }
        
        for category, keywords in keyword_mapping.items():
            if any(kw in text_lower for kw in keywords):
                categories.add(category)
        
        return list(categories)
