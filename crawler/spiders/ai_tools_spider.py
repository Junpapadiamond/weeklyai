"""
AI工具集合网站爬虫
采集各类AI工具目录网站的产品信息
"""

from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base_spider import BaseSpider


class AIToolsSpider(BaseSpider):
    """AI工具集合爬虫"""
    
    # 可以采集的网站列表
    SOURCES = {
        'futurepedia': 'https://www.futurepedia.io',
        'there_is_an_ai': 'https://theresanaiforthat.com',
        'ai_tools_list': 'https://ai-tools.directory',
    }
    
    # 分类关键词映射
    KEYWORD_CATEGORIES = {
        'code': 'coding',
        'coding': 'coding',
        'developer': 'coding',
        'programming': 'coding',
        'voice': 'voice',
        'speech': 'voice',
        'audio': 'voice',
        'finance': 'finance',
        'trading': 'finance',
        'investment': 'finance',
        'image': 'image',
        'photo': 'image',
        'art': 'image',
        'video': 'video',
        'animation': 'video',
        'writing': 'writing',
        'text': 'writing',
        'content': 'writing',
        'copywriting': 'writing',
        'health': 'healthcare',
        'medical': 'healthcare',
        'education': 'education',
        'learning': 'education',
        'hardware': 'hardware',
        'device': 'hardware',
        'robot': 'hardware',
    }
    
    def crawl(self) -> List[Dict[str, Any]]:
        """
        爬取AI工具信息
        """
        products = []
        
        # 由于大多数网站有反爬措施，这里提供示例数据
        # 实际使用时可以：
        # 1. 使用 Selenium 处理动态加载
        # 2. 使用各网站的 API（如有）
        # 3. 使用代理池绕过限制
        
        print("  提示: 采集真实数据请配置代理和处理动态加载")
        
        # 示例数据 - 模拟采集结果
        sample_products = [
            {
                'name': 'Runway Gen-3',
                'description': '新一代AI视频生成模型，创建电影级视觉效果',
                'website': 'https://runwayml.com',
                'logo_url': '',
                'tags': ['video', 'ai', 'generation'],
                'popularity': 95,
            },
            {
                'name': 'Suno AI',
                'description': 'AI音乐创作平台，输入文字即可生成完整歌曲',
                'website': 'https://suno.ai',
                'logo_url': '',
                'tags': ['audio', 'music', 'ai'],
                'popularity': 92,
            },
            {
                'name': 'Pika Labs',
                'description': '简单易用的AI视频生成工具',
                'website': 'https://pika.art',
                'logo_url': '',
                'tags': ['video', 'animation'],
                'popularity': 88,
            },
            {
                'name': 'Replit AI',
                'description': '云端IDE集成AI编程助手',
                'website': 'https://replit.com',
                'logo_url': '',
                'tags': ['coding', 'developer'],
                'popularity': 85,
            },
            {
                'name': 'Grammarly',
                'description': 'AI写作助手，提供语法检查和写作建议',
                'website': 'https://grammarly.com',
                'logo_url': '',
                'tags': ['writing', 'content'],
                'popularity': 90,
            },
        ]
        
        for item in sample_products:
            categories = self._extract_categories(item.get('tags', []))
            
            product = self.create_product(
                name=item['name'],
                description=item['description'],
                logo_url=item.get('logo_url', ''),
                website=item['website'],
                categories=categories if categories else ['other'],
                trending_score=item.get('popularity', 50),
                source='ai_tools_directory'
            )
            products.append(product)
        
        return products
    
    def _extract_categories(self, tags: List[str]) -> List[str]:
        """
        从标签中提取分类
        """
        categories = set()
        
        for tag in tags:
            tag_lower = tag.lower()
            for keyword, category in self.KEYWORD_CATEGORIES.items():
                if keyword in tag_lower:
                    categories.add(category)
                    break
        
        return list(categories)
    
    def crawl_futurepedia(self) -> List[Dict]:
        """
        采集 Futurepedia 网站
        实际实现需要处理动态加载
        """
        url = self.SOURCES['futurepedia']
        
        try:
            response = self.fetch(f"{url}/ai-tools")
            soup = BeautifulSoup(response.text, 'lxml')
            
            products = []
            # 解析产品列表...
            # 实际实现需要根据网站结构进行解析
            
            return products
        except Exception as e:
            print(f"  Futurepedia 采集失败: {e}")
            return []


