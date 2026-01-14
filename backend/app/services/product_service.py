"""
产品服务 - 支持从数据库或爬虫数据文件加载
"""

import os
import json
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any, Optional

# MongoDB support
try:
    from pymongo import MongoClient
    HAS_MONGO = True
except ImportError:
    HAS_MONGO = False

# 爬虫数据文件路径
CRAWLER_DATA_DIR = os.path.join(
    os.path.dirname(__file__),
    '..', '..', '..', 'crawler', 'data'
)
PRODUCTS_FEATURED_FILE = os.path.join(CRAWLER_DATA_DIR, 'products_featured.json')
BLOGS_NEWS_FILE = os.path.join(CRAWLER_DATA_DIR, 'blogs_news.json')
CRAWLER_DATA_FILE = os.path.join(CRAWLER_DATA_DIR, 'products_latest.json')
DARK_HORSES_DIR = os.path.join(CRAWLER_DATA_DIR, 'dark_horses')
BLOCKED_SOURCES = {'github', 'huggingface', 'huggingface_spaces'}
BLOCKED_DOMAINS = ('github.com', 'huggingface.co')

# MongoDB connection
_mongo_client = None
_mongo_db = None

def get_mongo_db():
    """Get MongoDB connection (lazy initialization)"""
    global _mongo_client, _mongo_db
    if not HAS_MONGO:
        return None
    if _mongo_db is not None:
        return _mongo_db
    try:
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/weeklyai')
        _mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        _mongo_client.admin.command('ping')
        _mongo_db = _mongo_client.get_database()
        print("  ✓ Backend connected to MongoDB")
        return _mongo_db
    except Exception as e:
        print(f"  ⚠ MongoDB connection failed: {e}, using JSON files")
        return None

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
        'name': 'Kiro',
        'description': 'AWS 背景团队打造的规范驱动 AI 开发平台，强调稳定的工程化交付。',
        'logo_url': 'https://kiro.dev/favicon.ico',
        'website': 'https://kiro.dev',
        'categories': ['coding'],
        'rating': 4.7,
        'weekly_users': 180000,
        'trending_score': 90,
        'final_score': 90,
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
        'name': 'Lovable',
        'description': '欧洲最快增长的 AI 产品团队之一，8 个月从 0 到独角兽。',
        'logo_url': 'https://lovable.dev/favicon.ico',
        'website': 'https://lovable.dev',
        'categories': ['other'],
        'rating': 4.8,
        'weekly_users': 120000,
        'trending_score': 88,
        'final_score': 88,
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

    @staticmethod
    def _build_product_key(product: Dict[str, Any]) -> str:
        """Normalize a product key for dedupe/merge."""
        website = (product.get('website') or '').strip().lower()
        if website:
            return website
        name_key = (product.get('name') or '').strip().lower()
        return ''.join(ch for ch in name_key if ch.isalnum())

    @staticmethod
    def _is_blocked(product: Dict[str, Any]) -> bool:
        """Filter non-end-user sources/domains."""
        source = (product.get('source') or '').strip().lower()
        if source in BLOCKED_SOURCES:
            return True
        website = (product.get('website') or '').strip().lower()
        return any(domain in website for domain in BLOCKED_DOMAINS)

    @staticmethod
    def _normalize_curated_product(product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Map curated dark-horse fields into standard product fields."""
        if not isinstance(product, dict):
            return None
        normalized = product.copy()
        if not normalized.get('logo_url'):
            normalized['logo_url'] = normalized.get('logo') or normalized.get('logoUrl') or ''
        if not normalized.get('categories'):
            category = normalized.get('category')
            if category:
                normalized['categories'] = [category]
        if not normalized.get('source'):
            normalized['source'] = 'curated'
        if 'is_hardware' not in normalized:
            normalized['is_hardware'] = False
        return normalized

    @classmethod
    def _load_curated_dark_horses(cls) -> List[Dict[str, Any]]:
        """Load manually curated dark-horse products."""
        if not os.path.isdir(DARK_HORSES_DIR):
            return []

        curated: List[Dict[str, Any]] = []
        for filename in sorted(os.listdir(DARK_HORSES_DIR)):
            if not filename.endswith('.json'):
                continue
            if filename == 'template.json':
                continue
            path = os.path.join(DARK_HORSES_DIR, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    data = [data]
                if isinstance(data, list):
                    curated.extend(item for item in data if isinstance(item, dict))
            except Exception:
                continue
        return curated

    @classmethod
    def _merge_curated_products(cls, products: List[Dict[str, Any]],
                                curated: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge curated products into base list (prefer curated fields)."""
        if not curated:
            return products

        by_key = {cls._build_product_key(p): p for p in products if p}
        for item in curated:
            normalized = cls._normalize_curated_product(item)
            if not normalized or cls._is_blocked(normalized):
                continue
            key = cls._build_product_key(normalized)
            if not key:
                continue
            if key in by_key:
                target = by_key[key]
                for field, value in normalized.items():
                    if value not in (None, '', [], {}):
                        target[field] = value
                continue
            products.append(normalized)
            by_key[key] = normalized
        return products

    @classmethod
    def _normalize_products(cls, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize products and drop blocked sources/domains."""
        normalized = []
        for idx, product in enumerate(products):
            if not product or cls._is_blocked(product):
                continue
            if not product.get('logo_url'):
                logo = product.get('logo') or product.get('logoUrl')
                if logo:
                    product['logo_url'] = logo
            if '_id' not in product:
                product['_id'] = str(idx + 1)
            normalized.append(product)
        return normalized
    
    @classmethod
    def _load_products(cls) -> List[Dict]:
        """加载产品数据（带缓存）- 优先使用MongoDB"""
        now = datetime.now()

        # 检查缓存
        if cls._cached_products and cls._cache_time:
            age = (now - cls._cache_time).total_seconds()
            if age < cls._cache_duration:
                return cls._cached_products

        # 1. 优先尝试从MongoDB加载
        products = cls._load_from_mongodb()

        # 2. 如果MongoDB没数据，尝试从JSON文件加载
        if not products:
            products = cls._load_from_crawler_file()

        # 3. 如果都没有，使用示例数据
        if not products:
            products = SAMPLE_PRODUCTS.copy()

        # 4. 合并手动策展黑马产品
        curated = cls._load_curated_dark_horses()
        products = cls._merge_curated_products(products, curated)

        # 5. 统一字段 & 过滤
        products = cls._normalize_products(products)

        # 更新缓存
        cls._cached_products = products
        cls._cache_time = now

        return products

    @classmethod
    def _load_from_mongodb(cls) -> List[Dict]:
        """从MongoDB加载产品数据"""
        db = get_mongo_db()
        if db is None:
            return []

        try:
            collection = db.products
            blocked_sources = list(BLOCKED_SOURCES)
            # 获取产品，排除 content_type='blog' 和 content_type='filtered'
            products = list(collection.find(
                {
                    'content_type': {'$nin': ['blog', 'filtered']},
                    'source': {'$nin': blocked_sources}
                },
                {'_id': 0}
            ).sort('final_score', -1))

            # 如果没有 content_type 字段，获取所有产品
            if not products:
                products = list(collection.find(
                    {'source': {'$nin': blocked_sources}},
                    {'_id': 0}
                ).sort('final_score', -1))

            if products:
                print(f"  ✓ Loaded {len(products)} products from MongoDB")

            # 添加 _id 字段
            for i, p in enumerate(products):
                if '_id' not in p:
                    p['_id'] = str(i + 1)
                # Parse extra field if it's a string
                if 'extra' in p and isinstance(p['extra'], str):
                    try:
                        p['extra'] = json.loads(p['extra'])
                    except:
                        pass

            return products
        except Exception as e:
            print(f"  ⚠ MongoDB load failed: {e}")
            return []
    
    @classmethod
    def _load_from_crawler_file(cls) -> List[Dict]:
        """从爬虫数据文件加载（优先使用 products_featured.json）"""
        # 优先使用分类后的产品文件
        data_file = PRODUCTS_FEATURED_FILE if os.path.exists(PRODUCTS_FEATURED_FILE) else CRAWLER_DATA_FILE

        if not os.path.exists(data_file):
            return []

        try:
            with open(data_file, 'r', encoding='utf-8') as f:
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
    def _load_blogs(cls) -> List[Dict]:
        """加载博客/新闻/讨论数据"""
        if not os.path.exists(BLOGS_NEWS_FILE):
            return []

        try:
            with open(BLOGS_NEWS_FILE, 'r', encoding='utf-8') as f:
                blogs = json.load(f)

            # 添加 _id 字段
            for i, b in enumerate(blogs):
                if '_id' not in b:
                    b['_id'] = f"blog_{i + 1}"

            return blogs
        except Exception as e:
            print(f"加载博客数据失败: {e}")
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

    @staticmethod
    def get_blogs_news(limit: int = 20) -> List[Dict]:
        """获取博客/新闻/讨论内容"""
        blogs = ProductService._load_blogs()

        # 按分数排序
        blogs.sort(
            key=lambda x: x.get('final_score', x.get('trending_score', 0)),
            reverse=True
        )

        return blogs[:limit]

    @staticmethod
    def get_blogs_by_source(source: str, limit: int = 20) -> List[Dict]:
        """按来源获取博客内容"""
        blogs = ProductService._load_blogs()

        filtered = [
            b for b in blogs
            if b.get('source', '') == source
        ]

        return filtered[:limit]

    @staticmethod
    def get_dark_horse_products(limit: int = 6, min_index: int = 4) -> List[Dict]:
        """获取黑马产品 - 高潜力新兴产品

        参数:
        - limit: 返回数量
        - min_index: 最低黑马指数 (1-5)
        """
        products = ProductService._load_products()

        # 筛选有 dark_horse_index 且 >= min_index 的产品
        dark_horses = [
            p for p in products
            if p.get('dark_horse_index', 0) >= min_index
        ]

        # 按 dark_horse_index 降序，然后按 final_score 降序
        dark_horses.sort(
            key=lambda x: (
                x.get('dark_horse_index', 0),
                x.get('final_score', x.get('trending_score', 0))
            ),
            reverse=True
        )

        return dark_horses[:limit]
