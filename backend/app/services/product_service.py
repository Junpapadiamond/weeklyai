"""
产品服务 - 支持从数据库或爬虫数据文件加载
"""

import os
import json
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any, Optional

# 爬虫数据文件路径
CRAWLER_DATA_FILE = os.path.join(
    os.path.dirname(__file__), 
    '..', '..', '..', 'crawler', 'data', 'products_latest.json'
)

# 示例数据（当没有爬虫数据时使用）
SAMPLE_PRODUCTS = [
    {
        '_id': '1',
        'name': 'ChatGPT',
        'description': 'OpenAI开发的大型语言模型，能够进行自然对话、写作、编程辅助等多种任务。',
        'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/0/04/ChatGPT_logo.svg',
        'website': 'https://chat.openai.com',
        'categories': ['coding', 'writing'],
        'rating': 4.8,
        'weekly_users': 1500000,
        'trending_score': 98,
        'final_score': 98,
        'is_hardware': False,
        'source': 'sample'
    },
    {
        '_id': '2',
        'name': 'Claude',
        'description': 'Anthropic开发的AI助手，以安全、有帮助和诚实为核心设计理念。',
        'logo_url': 'https://www.anthropic.com/images/icons/apple-touch-icon.png',
        'website': 'https://claude.ai',
        'categories': ['coding', 'writing'],
        'rating': 4.7,
        'weekly_users': 800000,
        'trending_score': 95,
        'final_score': 95,
        'is_hardware': False,
        'source': 'sample'
    },
    {
        '_id': '3',
        'name': 'Midjourney',
        'description': '强大的AI图像生成工具，通过文本描述生成高质量艺术图像。',
        'logo_url': 'https://www.midjourney.com/apple-touch-icon.png',
        'website': 'https://midjourney.com',
        'categories': ['image'],
        'rating': 4.9,
        'weekly_users': 1200000,
        'trending_score': 96,
        'final_score': 96,
        'is_hardware': False,
        'source': 'sample'
    },
    {
        '_id': '4',
        'name': 'GitHub Copilot',
        'description': 'GitHub与OpenAI合作开发的AI编程助手，提供智能代码补全和建议。',
        'logo_url': 'https://github.githubassets.com/images/modules/site/copilot/copilot.png',
        'website': 'https://github.com/features/copilot',
        'categories': ['coding'],
        'rating': 4.6,
        'weekly_users': 950000,
        'trending_score': 92,
        'final_score': 92,
        'is_hardware': False,
        'source': 'sample'
    },
    {
        '_id': '5',
        'name': 'Eleven Labs',
        'description': '领先的AI语音合成平台，提供逼真的文字转语音和语音克隆功能。',
        'logo_url': 'https://elevenlabs.io/favicon.ico',
        'website': 'https://elevenlabs.io',
        'categories': ['voice'],
        'rating': 4.7,
        'weekly_users': 600000,
        'trending_score': 89,
        'final_score': 89,
        'is_hardware': False,
        'source': 'sample'
    },
    {
        '_id': '6',
        'name': 'NVIDIA H100',
        'description': 'NVIDIA最新一代AI加速器，专为大规模AI训练和推理设计。',
        'logo_url': 'https://www.nvidia.com/favicon.ico',
        'website': 'https://www.nvidia.com/en-us/data-center/h100/',
        'categories': ['hardware'],
        'rating': 4.9,
        'weekly_users': 50000,
        'trending_score': 94,
        'final_score': 94,
        'is_hardware': True,
        'source': 'sample'
    },
    {
        '_id': '7',
        'name': 'Perplexity AI',
        'description': 'AI驱动的搜索引擎，提供带引用来源的答案。',
        'logo_url': 'https://www.perplexity.ai/favicon.ico',
        'website': 'https://perplexity.ai',
        'categories': ['other'],
        'rating': 4.5,
        'weekly_users': 700000,
        'trending_score': 88,
        'final_score': 88,
        'is_hardware': False,
        'source': 'sample'
    },
    {
        '_id': '8',
        'name': 'Runway ML',
        'description': '创意AI工具套件，提供视频生成、编辑和特效功能。',
        'logo_url': 'https://runwayml.com/favicon.ico',
        'website': 'https://runwayml.com',
        'categories': ['video', 'image'],
        'rating': 4.6,
        'weekly_users': 450000,
        'trending_score': 87,
        'final_score': 87,
        'is_hardware': False,
        'source': 'sample'
    },
    {
        '_id': '9',
        'name': 'Stable Diffusion',
        'description': '开源的AI图像生成模型，支持本地部署和自定义训练。',
        'logo_url': 'https://stability.ai/favicon.ico',
        'website': 'https://stability.ai',
        'categories': ['image'],
        'rating': 4.6,
        'weekly_users': 890000,
        'trending_score': 91,
        'final_score': 91,
        'is_hardware': False,
        'source': 'sample'
    },
    {
        '_id': '10',
        'name': 'Google Gemini',
        'description': 'Google最新的多模态AI模型，整合文本、图像、音频理解能力。',
        'logo_url': 'https://www.google.com/favicon.ico',
        'website': 'https://gemini.google.com',
        'categories': ['coding', 'writing', 'image'],
        'rating': 4.5,
        'weekly_users': 1100000,
        'trending_score': 93,
        'final_score': 93,
        'is_hardware': False,
        'source': 'sample'
    },
    {
        '_id': '11',
        'name': 'Hugging Face',
        'description': '开源AI社区平台，提供模型托管、数据集和机器学习工具。',
        'logo_url': 'https://huggingface.co/favicon.ico',
        'website': 'https://huggingface.co',
        'categories': ['coding', 'other'],
        'rating': 4.8,
        'weekly_users': 750000,
        'trending_score': 90,
        'final_score': 90,
        'is_hardware': False,
        'source': 'sample'
    },
    {
        '_id': '12',
        'name': 'Cursor',
        'description': 'AI增强的代码编辑器，内置智能代码补全和对话式编程功能。',
        'logo_url': 'https://cursor.sh/favicon.ico',
        'website': 'https://cursor.sh',
        'categories': ['coding'],
        'rating': 4.8,
        'weekly_users': 420000,
        'trending_score': 94,
        'final_score': 94,
        'is_hardware': False,
        'source': 'sample'
    },
    {
        '_id': '13',
        'name': 'Sora',
        'description': 'OpenAI的文本到视频生成模型，能创建高质量的视频内容。',
        'logo_url': 'https://openai.com/favicon.ico',
        'website': 'https://openai.com/sora',
        'categories': ['video'],
        'rating': 4.8,
        'weekly_users': 300000,
        'trending_score': 97,
        'final_score': 97,
        'is_hardware': False,
        'source': 'sample'
    },
    {
        '_id': '14',
        'name': 'Whisper',
        'description': 'OpenAI开源的语音识别模型，支持多语言转录和翻译。',
        'logo_url': 'https://openai.com/favicon.ico',
        'website': 'https://openai.com/research/whisper',
        'categories': ['voice'],
        'rating': 4.7,
        'weekly_users': 520000,
        'trending_score': 85,
        'final_score': 85,
        'is_hardware': False,
        'source': 'sample'
    },
    {
        '_id': '15',
        'name': 'Duolingo Max',
        'description': '使用GPT-4增强的语言学习平台，提供AI对话练习功能。',
        'logo_url': 'https://www.duolingo.com/favicon.ico',
        'website': 'https://www.duolingo.com/max',
        'categories': ['education'],
        'rating': 4.6,
        'weekly_users': 650000,
        'trending_score': 84,
        'final_score': 84,
        'is_hardware': False,
        'source': 'sample'
    },
]


class ProductService:
    """产品服务类"""
    
    _cached_products = None
    _cache_time = None
    _cache_duration = 300  # 5分钟缓存
    
    @classmethod
    def _load_products(cls) -> List[Dict]:
        """加载产品数据（带缓存）"""
        now = datetime.now()
        
        # 检查缓存
        if cls._cached_products and cls._cache_time:
            age = (now - cls._cache_time).total_seconds()
            if age < cls._cache_duration:
                return cls._cached_products
        
        # 尝试从爬虫数据文件加载
        products = cls._load_from_crawler_file()
        
        # 如果没有爬虫数据，使用示例数据
        if not products:
            products = SAMPLE_PRODUCTS.copy()
        
        # 更新缓存
        cls._cached_products = products
        cls._cache_time = now
        
        return products
    
    @classmethod
    def _load_from_crawler_file(cls) -> List[Dict]:
        """从爬虫数据文件加载"""
        if not os.path.exists(CRAWLER_DATA_FILE):
            return []
        
        try:
            with open(CRAWLER_DATA_FILE, 'r', encoding='utf-8') as f:
                products = json.load(f)
            
            # 添加 _id 字段
            for i, p in enumerate(products):
                if '_id' not in p:
                    p['_id'] = str(i + 1)
            
            return products
        except Exception as e:
            print(f"加载爬虫数据失败: {e}")
            return []
    
    @classmethod
    def refresh_cache(cls):
        """强制刷新缓存"""
        cls._cached_products = None
        cls._cache_time = None

    @staticmethod
    def _diversify_products(products: List[Dict], limit: int, max_per_category: int, max_per_source: int) -> List[Dict]:
        """限制单一类别与来源占比，保证榜单更均衡。"""
        selected = []
        category_counts = defaultdict(int)
        source_counts = defaultdict(int)

        for product in products:
            categories = product.get('categories') or ['other']
            primary = categories[0] if categories else 'other'
            source = product.get('source', 'unknown')
            if category_counts[primary] >= max_per_category:
                continue
            if source_counts[source] >= max_per_source:
                continue
            selected.append(product)
            category_counts[primary] += 1
            source_counts[source] += 1
            if len(selected) >= limit:
                return selected

        # 如果不足，再补齐剩余
        for product in products:
            if product in selected:
                continue
            selected.append(product)
            if len(selected) >= limit:
                break

        return selected
    
    @staticmethod
    def get_trending_products(limit: int = 5) -> List[Dict]:
        """获取热门推荐产品"""
        products = ProductService._load_products()
        
        # 按 hot_score 或 final_score 排序
        sorted_products = sorted(
            products,
            key=lambda x: x.get('hot_score', x.get('final_score', x.get('trending_score', 0))),
            reverse=True
        )
        return ProductService._diversify_products(sorted_products, limit, max_per_category=2, max_per_source=2)
    
    @staticmethod
    def get_weekly_top_products(limit: int = 15) -> List[Dict]:
        """获取本周Top产品"""
        products = ProductService._load_products()
        
        # 按 top_score 或 final_score 排序
        sorted_products = sorted(
            products,
            key=lambda x: x.get('top_score', x.get('final_score', x.get('trending_score', 0))),
            reverse=True
        )
        return ProductService._diversify_products(sorted_products, limit, max_per_category=4, max_per_source=5)
    
    @staticmethod
    def get_product_by_id(product_id: str) -> Optional[Dict]:
        """根据ID获取产品"""
        products = ProductService._load_products()
        
        for product in products:
            if str(product.get('_id', '')) == product_id:
                return product
            # 也支持按名称查找
            if product.get('name', '').lower() == product_id.lower():
                return product
        
        return None
    
    @staticmethod
    def search_products(keyword: str = '', categories: List[str] = None, 
                       product_type: str = 'all', sort_by: str = 'trending',
                       page: int = 1, limit: int = 15) -> Dict:
        """
        搜索产品
        
        参数:
        - keyword: 搜索关键词
        - categories: 分类列表
        - product_type: 类型 (software/hardware/all)
        - sort_by: 排序方式 (trending/rating/users)
        - page: 页码
        - limit: 每页数量
        """
        products = ProductService._load_products()
        results = products.copy()
        
        # 关键词筛选
        if keyword:
            keyword_lower = keyword.lower()
            results = [
                p for p in results 
                if keyword_lower in p.get('name', '').lower() 
                or keyword_lower in p.get('description', '').lower()
            ]
        
        # 分类筛选（支持多选，OR逻辑）
        if categories:
            results = [
                p for p in results 
                if any(cat in p.get('categories', []) for cat in categories)
            ]
        
        # 类型筛选
        if product_type == 'software':
            results = [p for p in results if not p.get('is_hardware', False)]
        elif product_type == 'hardware':
            results = [p for p in results if p.get('is_hardware', False)]
        
        # 排序
        if sort_by == 'trending':
            results.sort(
                key=lambda x: x.get('hot_score', x.get('final_score', x.get('trending_score', 0))),
                reverse=True
            )
        elif sort_by == 'rating':
            results.sort(key=lambda x: x.get('rating', 0), reverse=True)
        elif sort_by == 'users':
            results.sort(key=lambda x: x.get('weekly_users', 0), reverse=True)
        
        # 分页
        total = len(results)
        start = (page - 1) * limit
        end = start + limit
        paginated_results = results[start:end]
        
        return {
            'products': paginated_results,
            'total': total
        }
    
    @staticmethod
    def get_all_products() -> List[Dict]:
        """获取所有产品"""
        return ProductService._load_products()
    
    @staticmethod
    def get_products_by_category(category: str, limit: int = 20) -> List[Dict]:
        """按分类获取产品"""
        products = ProductService._load_products()
        
        filtered = [
            p for p in products 
            if category in p.get('categories', [])
        ]
        
        # 按热度排序
        filtered.sort(
            key=lambda x: x.get('final_score', x.get('trending_score', 0)),
            reverse=True
        )
        
        return filtered[:limit]
    
    @staticmethod
    def get_products_by_source(source: str, limit: int = 20) -> List[Dict]:
        """按来源获取产品"""
        products = ProductService._load_products()
        
        filtered = [
            p for p in products 
            if p.get('source', '') == source
        ]
        
        return filtered[:limit]
