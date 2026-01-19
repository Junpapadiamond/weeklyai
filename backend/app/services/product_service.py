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
LAST_UPDATED_FILE = os.path.join(CRAWLER_DATA_DIR, 'last_updated.json')
DARK_HORSES_DIR = os.path.join(CRAWLER_DATA_DIR, 'dark_horses')
BLOCKED_SOURCES = {'github', 'huggingface', 'huggingface_spaces'}
BLOCKED_DOMAINS = ('github.com', 'huggingface.co')

# 著名产品黑名单 - 除非有新功能否则不显示
WELL_KNOWN_PRODUCTS = {
    'chatgpt', 'claude', 'gemini', 'bard', 'copilot', 'perplexity',
    'midjourney', 'dall-e', 'stable diffusion', 'cursor', 'github copilot',
    'whisper', 'elevenlabs', 'runway', 'pika', 'sora', 'openai', 'anthropic',
    'notion ai', 'jasper', 'copy.ai', 'grammarly', 'nvidia h100', 'duolingo'
}

# 新功能关键词 - 允许著名产品显示
NEW_FEATURE_KEYWORDS = {'发布', '推出', '更新', '新版', '新功能', 'launch', 'release', 'new feature', 'update', 'v2', 'v3', 'v4', 'announces', '宣布'}

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

# 示例数据（当没有爬虫数据时使用）- 只包含黑马产品，不包含著名产品
SAMPLE_PRODUCTS = [
    {
        '_id': '1',
        'name': 'Lovable',
        'description': '欧洲最快增长的 AI 产品，8 个月从 0 到独角兽。非开发者也能快速构建全栈应用。',
        'logo_url': 'https://lovable.dev/favicon.ico',
        'website': 'https://lovable.dev',
        'categories': ['coding'],
        'rating': 4.8,
        'weekly_users': 120000,
        'trending_score': 92,
        'final_score': 92,
        'is_hardware': False,
        'why_matters': '证明了 AI 原生产品可以极速获客，对想做 AI 创业的 PM 有重要参考价值。',
        'source': 'sample'
    },
    {
        '_id': '2',
        'name': 'Devin',
        'description': '全自主 AI 软件工程师，能够端到端处理需求拆解、代码实现与交付。Cognition Labs 出品。',
        'logo_url': 'https://cognition.ai/favicon.ico',
        'website': 'https://cognition.ai',
        'categories': ['coding'],
        'rating': 4.7,
        'weekly_users': 160000,
        'trending_score': 93,
        'final_score': 93,
        'is_hardware': False,
        'why_matters': '重新定义了「AI 工程师」边界，PM 需要思考如何与 AI 协作而非仅仅使用 AI。',
        'source': 'sample'
    },
    {
        '_id': '3',
        'name': 'Kiro',
        'description': 'AWS 背景团队打造的规范驱动 AI 开发平台，强调稳定的工程化交付而非炫技。',
        'logo_url': 'https://kiro.dev/favicon.ico',
        'website': 'https://kiro.dev',
        'categories': ['coding'],
        'rating': 4.7,
        'weekly_users': 85000,
        'trending_score': 90,
        'final_score': 90,
        'is_hardware': False,
        'why_matters': '大厂背景创业，专注企业级可靠性，是 AI 编程工具的差异化方向。',
        'source': 'sample'
    },
    {
        '_id': '4',
        'name': 'Emergent',
        'description': '非开发者也能用 AI 代理构建全栈应用的建站产品，降低技术门槛。',
        'logo_url': 'https://emergent.sh/favicon.ico',
        'website': 'https://emergent.sh',
        'categories': ['coding'],
        'rating': 4.6,
        'weekly_users': 45000,
        'trending_score': 88,
        'final_score': 88,
        'is_hardware': False,
        'why_matters': '面向非技术用户的 AI 开发工具，扩展了「谁能做产品」的边界。',
        'source': 'sample'
    },
    {
        '_id': '5',
        'name': 'Bolt.new',
        'description': 'StackBlitz 推出的浏览器内全栈 AI 开发环境，无需配置即可开始编码。',
        'logo_url': 'https://bolt.new/favicon.ico',
        'website': 'https://bolt.new',
        'categories': ['coding'],
        'rating': 4.8,
        'weekly_users': 200000,
        'trending_score': 91,
        'final_score': 91,
        'is_hardware': False,
        'why_matters': '零配置 + 浏览器内运行，大幅降低 AI 开发入门门槛。',
        'source': 'sample'
    },
    {
        '_id': '6',
        'name': 'Windsurf',
        'description': 'Codeium 推出的 Agentic IDE，强调 AI 代理主动参与开发流程。',
        'logo_url': 'https://codeium.com/favicon.ico',
        'website': 'https://codeium.com/windsurf',
        'categories': ['coding'],
        'rating': 4.6,
        'weekly_users': 95000,
        'trending_score': 87,
        'final_score': 87,
        'is_hardware': False,
        'why_matters': 'Agentic IDE 概念的先行者，代表了 AI 编程工具的演进方向。',
        'source': 'sample'
    },
    {
        '_id': '7',
        'name': 'NEO (1X Technologies)',
        'description': '挪威初创公司研发的人形机器人，定位家庭助手和轻工业场景。',
        'logo_url': 'https://1x.tech/favicon.ico',
        'website': 'https://1x.tech',
        'categories': ['hardware'],
        'rating': 4.5,
        'weekly_users': 15000,
        'trending_score': 85,
        'final_score': 85,
        'is_hardware': True,
        'why_matters': '人形机器人赛道的黑马，融资后估值飙升，值得关注具身智能趋势。',
        'source': 'sample'
    },
    {
        '_id': '8',
        'name': 'Rokid AR Studio',
        'description': '中国 AR 眼镜厂商推出的 AI 开发平台，支持空间计算应用开发。',
        'logo_url': 'https://www.rokid.com/favicon.ico',
        'website': 'https://www.rokid.com',
        'categories': ['hardware'],
        'rating': 4.4,
        'weekly_users': 25000,
        'trending_score': 82,
        'final_score': 82,
        'is_hardware': True,
        'why_matters': '国产 AR 眼镜 + AI 平台，空间计算赛道的本土玩家。',
        'source': 'sample'
    },
    {
        '_id': '9',
        'name': 'DeepSeek',
        'description': '中国 AI 研究公司，以高效开源模型著称，性价比极高。',
        'logo_url': 'https://www.deepseek.com/favicon.ico',
        'website': 'https://www.deepseek.com',
        'categories': ['coding', 'writing'],
        'rating': 4.6,
        'weekly_users': 180000,
        'trending_score': 89,
        'final_score': 89,
        'is_hardware': False,
        'why_matters': '开源大模型的性价比之王，训练成本仅为竞品的 1/10。',
        'source': 'sample'
    },
    {
        '_id': '10',
        'name': 'Replit Agent',
        'description': 'Replit 推出的 AI 代理，能自主完成从需求到部署的完整开发流程。',
        'logo_url': 'https://replit.com/favicon.ico',
        'website': 'https://replit.com',
        'categories': ['coding'],
        'rating': 4.5,
        'weekly_users': 150000,
        'trending_score': 86,
        'final_score': 86,
        'is_hardware': False,
        'why_matters': '全流程 AI 开发代理，从 idea 到上线一站式完成。',
        'source': 'sample'
    },
    {
        '_id': '11',
        'name': 'Thinking Machines Lab',
        'description': '菲律宾 AI 研究初创，专注东南亚本地化大语言模型研发。',
        'logo_url': 'https://thinkingmachines.ph/favicon.ico',
        'website': 'https://thinkingmachines.ph',
        'categories': ['other'],
        'rating': 4.3,
        'weekly_users': 12000,
        'trending_score': 78,
        'final_score': 78,
        'is_hardware': False,
        'why_matters': '东南亚本土 AI 研究力量，区域化 AI 的代表案例。',
        'source': 'sample'
    },
    {
        '_id': '12',
        'name': 'Poe',
        'description': 'Quora 推出的多模型 AI 聊天平台，一站式访问多种 AI 模型。',
        'logo_url': 'https://poe.com/favicon.ico',
        'website': 'https://poe.com',
        'categories': ['other'],
        'rating': 4.5,
        'weekly_users': 280000,
        'trending_score': 84,
        'final_score': 84,
        'is_hardware': False,
        'why_matters': 'AI 模型聚合平台，让用户无需切换即可对比不同模型能力。',
        'source': 'sample'
    },
    {
        '_id': '13',
        'name': 'v0.dev',
        'description': 'Vercel 推出的 AI UI 生成器，通过对话生成 React 组件代码。',
        'logo_url': 'https://v0.dev/favicon.ico',
        'website': 'https://v0.dev',
        'categories': ['coding', 'image'],
        'rating': 4.7,
        'weekly_users': 175000,
        'trending_score': 90,
        'final_score': 90,
        'is_hardware': False,
        'why_matters': '前端 AI 生成的标杆产品，设计师和开发者都能用。',
        'source': 'sample'
    },
    {
        '_id': '14',
        'name': 'Kling AI',
        'description': '快手推出的 AI 视频生成工具，支持文本/图片转视频。',
        'logo_url': 'https://klingai.com/favicon.ico',
        'website': 'https://klingai.com',
        'categories': ['video'],
        'rating': 4.4,
        'weekly_users': 320000,
        'trending_score': 85,
        'final_score': 85,
        'is_hardware': False,
        'why_matters': '国产视频生成 AI 的代表，在特定场景下效果不输海外竞品。',
        'source': 'sample'
    },
    {
        '_id': '15',
        'name': 'Glif',
        'description': '可视化 AI 工作流构建平台，无需代码即可串联多个 AI 模型。',
        'logo_url': 'https://glif.app/favicon.ico',
        'website': 'https://glif.app',
        'categories': ['image', 'other'],
        'rating': 4.5,
        'weekly_users': 45000,
        'trending_score': 83,
        'final_score': 83,
        'is_hardware': False,
        'why_matters': 'AI 工作流的乐高积木，让创意人士无需写代码也能玩转 AI。',
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
    def _is_well_known(product: Dict[str, Any]) -> bool:
        """检查是否为著名产品（除非有新功能才显示）

        返回 True 表示应该被过滤掉（是著名产品且没有新功能）
        返回 False 表示可以显示（不是著名产品，或是著名产品但有新功能）
        """
        name = (product.get('name') or '').lower().strip()
        # 检查是否匹配任何著名产品
        is_famous = any(known in name for known in WELL_KNOWN_PRODUCTS)
        if not is_famous:
            return False  # 不是著名产品，可以显示

        # 是著名产品，检查是否有新功能关键词
        desc = (product.get('description') or '').lower()
        title = (product.get('title') or '').lower()
        text = f"{name} {desc} {title}"
        has_new_feature = any(kw in text for kw in NEW_FEATURE_KEYWORDS)

        # 如果有新功能，返回 False（可以显示）；否则返回 True（过滤掉）
        return not has_new_feature

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
        """Normalize products and drop blocked sources/domains + well-known products."""
        normalized = []
        for idx, product in enumerate(products):
            if not product or cls._is_blocked(product) or cls._is_well_known(product):
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
        """加载产品数据（带缓存）- 只从 products_featured.json 加载策展产品

        重要: 产品数据只来自手动策展的 JSON 文件，不从 MongoDB 或爬虫输出加载。
        这确保了产品列表的高质量和人工审核。
        """
        now = datetime.now()

        # 检查缓存
        if cls._cached_products and cls._cache_time:
            age = (now - cls._cache_time).total_seconds()
            if age < cls._cache_duration:
                return cls._cached_products

        # 1. 只从 products_featured.json 加载（策展产品）
        products = cls._load_from_crawler_file()

        # 2. 如果没有策展文件，使用示例数据
        if not products:
            products = SAMPLE_PRODUCTS.copy()

        # 3. 合并手动策展黑马产品 (dark_horses/ 目录)
        curated = cls._load_curated_dark_horses()
        products = cls._merge_curated_products(products, curated)

        # 4. 统一字段 & 过滤
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
        """从策展产品文件加载 (products_featured.json)

        这是唯一的产品数据源，包含人工审核的高质量产品。
        不会加载爬虫的原始输出 (products_latest.json)。
        """
        # 只加载策展产品文件
        if not os.path.exists(PRODUCTS_FEATURED_FILE):
            print("  ⚠ products_featured.json 不存在，将使用示例数据")
            return []

        try:
            with open(PRODUCTS_FEATURED_FILE, 'r', encoding='utf-8') as f:
                products = json.load(f)

            # 添加 _id 字段
            for i, p in enumerate(products):
                if '_id' not in p:
                    p['_id'] = str(i + 1)

            print(f"  ✓ 加载 {len(products)} 个策展产品")
            return products
        except Exception as e:
            print(f"  ⚠ 加载策展产品失败: {e}")
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
    def get_last_updated() -> Dict[str, Any]:
        """获取最近一次数据更新时间."""
        if not os.path.exists(LAST_UPDATED_FILE):
            return {'last_updated': None, 'hours_ago': None}

        try:
            with open(LAST_UPDATED_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return {'last_updated': None, 'hours_ago': None}

        last_updated = data.get('last_updated')
        if not last_updated:
            return {'last_updated': None, 'hours_ago': None}

        try:
            parsed = datetime.fromisoformat(str(last_updated).replace('Z', '+00:00'))
            hours_ago = round((datetime.now(parsed.tzinfo) - parsed).total_seconds() / 3600, 1)
        except Exception:
            hours_ago = None

        return {'last_updated': last_updated, 'hours_ago': hours_ago}

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
        """获取本周Top产品
        
        排序规则: 评分 > 融资金额 > 用户数/估值
        """
        products = ProductService._load_products()
        
        # 排序: 评分 > 融资 > 估值/用户数
        sorted_products = ProductService._sort_by_score_funding_valuation(products)
        
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
    def _parse_funding(funding: str) -> float:
        """解析融资金额字符串为数值（单位：百万美元）"""
        import re
        if not funding or funding == 'unknown':
            return 0
        match = re.match(r'\$?([\d.]+)\s*(M|B|K)?', str(funding), re.IGNORECASE)
        if not match:
            return 0
        value = float(match.group(1))
        unit = (match.group(2) or '').upper()
        if unit == 'B':
            value *= 1000
        elif unit == 'K':
            value /= 1000
        return value

    @staticmethod
    def _get_valuation_score(product: Dict) -> float:
        """获取估值/用户数综合分数"""
        import re
        # 优先使用估值
        valuation = product.get('valuation') or product.get('market_cap') or ''
        if valuation:
            match = re.match(r'\$?([\d.]+)\s*(M|B|K)?', str(valuation), re.IGNORECASE)
            if match:
                value = float(match.group(1))
                unit = (match.group(2) or '').upper()
                if unit == 'B':
                    value *= 1000
                elif unit == 'K':
                    value /= 1000
                return value * 10  # 估值权重更高
        
        # 其次使用用户数
        users = product.get('weekly_users') or product.get('users') or product.get('monthly_users') or 0
        if users > 0:
            return users / 10000  # 转换为万用户
        
        # 最后使用热度分数
        return product.get('hot_score') or product.get('trending_score') or product.get('final_score') or 0

    @staticmethod
    def _sort_by_score_funding_valuation(products: List[Dict]) -> List[Dict]:
        """按评分 > 融资 > 估值/用户数排序"""
        return sorted(
            products,
            key=lambda x: (
                x.get('dark_horse_index', 0),
                ProductService._parse_funding(x.get('funding_total', '')),
                ProductService._get_valuation_score(x)
            ),
            reverse=True
        )

    @staticmethod
    def get_dark_horse_products(limit: int = 6, min_index: int = 4) -> List[Dict]:
        """获取黑马产品 - 高潜力新兴产品

        参数:
        - limit: 返回数量
        - min_index: 最低黑马指数 (1-5)
        
        排序规则: 评分 > 融资金额 > 用户数/估值
        """
        products = ProductService._load_products()

        # 筛选有 dark_horse_index 且 >= min_index 的产品
        dark_horses = [
            p for p in products
            if p.get('dark_horse_index', 0) >= min_index
        ]

        # 排序: 评分 > 融资 > 估值/用户数
        dark_horses = ProductService._sort_by_score_funding_valuation(dark_horses)

        return dark_horses[:limit]

    @staticmethod
    def get_rising_star_products(limit: int = 20) -> List[Dict]:
        """获取潜力股产品 - 2-3分的有潜力产品

        参数:
        - limit: 返回数量
        
        排序规则: 评分 > 融资金额 > 用户数/估值
        """
        products = ProductService._load_products()

        # 筛选 dark_horse_index 为 2-3 的产品
        rising_stars = [
            p for p in products
            if 2 <= p.get('dark_horse_index', 0) <= 3
        ]

        # 排序: 评分 > 融资 > 估值/用户数
        rising_stars = ProductService._sort_by_score_funding_valuation(rising_stars)

        return rising_stars[:limit]

    @staticmethod
    def get_todays_picks(limit: int = 10, hours: int = 48) -> List[Dict]:
        """获取今日精选 - 仅返回最近48小时内的新产品

        参数:
        - limit: 返回数量 (默认10)
        - hours: 时间窗口，默认48小时
        """
        products = ProductService._load_products()
        now = datetime.now()

        # 筛选最近 hours 小时内的产品
        fresh_products = []
        for p in products:
            # 尝试多个日期字段
            date_str = p.get('first_seen') or p.get('published_at') or p.get('discovered_at')
            if not date_str:
                continue

            try:
                # 处理不同日期格式
                if isinstance(date_str, str):
                    # ISO格式: 2026-01-14T10:30:00
                    if 'T' in date_str:
                        product_date = datetime.fromisoformat(date_str.replace('Z', '+00:00').split('+')[0])
                    # 简单日期: 2026-01-14
                    else:
                        product_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                else:
                    continue

                # 检查是否在时间窗口内
                age_hours = (now - product_date).total_seconds() / 3600
                if age_hours <= hours:
                    p['_freshness_hours'] = age_hours  # 添加新鲜度标记
                    fresh_products.append(p)
            except (ValueError, TypeError):
                continue

        # 按 treasure_score > final_score > trending_score 排序
        fresh_products.sort(
            key=lambda x: (
                x.get('treasure_score', 0),
                x.get('final_score', x.get('trending_score', 0)),
                -x.get('_freshness_hours', 999)  # 越新鲜越靠前
            ),
            reverse=True
        )

        # 清理临时字段
        for p in fresh_products:
            p.pop('_freshness_hours', None)

        return ProductService._diversify_products(fresh_products, limit, max_per_category=3, max_per_source=3)

    @staticmethod
    def get_related_products(product_id: str, limit: int = 6) -> List[Dict]:
        """获取相关产品 - 基于分类和标签的相似产品推荐"""
        products = ProductService._load_products()

        # Find the target product
        target = None
        for p in products:
            if str(p.get('_id', '')) == product_id or p.get('name', '').lower() == product_id.lower():
                target = p
                break

        if not target:
            return []

        target_categories = set(target.get('categories', []))
        target_name = target.get('name', '')

        # Score all other products by similarity
        scored = []
        for p in products:
            if p.get('name') == target_name:
                continue

            score = 0
            p_categories = set(p.get('categories', []))

            # Category overlap (primary factor)
            overlap = len(target_categories & p_categories)
            score += overlap * 10

            # Same hardware/software type
            if p.get('is_hardware') == target.get('is_hardware'):
                score += 3

            # Recency bonus
            if p.get('first_seen'):
                score += 2

            if score > 0:
                scored.append((score, p))

        # Sort by score descending
        scored.sort(key=lambda x: (-x[0], -(x[1].get('final_score', 0) or 0)))

        return [p for _, p in scored[:limit]]

    @staticmethod
    def get_analytics_summary() -> Dict[str, Any]:
        """获取数据分析摘要"""
        products = ProductService._load_products()
        blogs = ProductService._load_blogs()

        # Category distribution
        category_counts = defaultdict(int)
        for p in products:
            for cat in p.get('categories', ['other']):
                category_counts[cat] += 1

        # Top categories
        top_categories = sorted(
            category_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        # Trending direction (compare scores)
        avg_score = sum(p.get('final_score', 0) or 0 for p in products) / max(len(products), 1)

        # Top movers (highest scoring products)
        top_movers = sorted(
            products,
            key=lambda x: x.get('hot_score', x.get('final_score', 0)) or 0,
            reverse=True
        )[:5]

        # Hardware vs Software split
        hardware_count = sum(1 for p in products if p.get('is_hardware'))
        software_count = len(products) - hardware_count

        return {
            'total_products': len(products),
            'total_blogs': len(blogs),
            'category_distribution': dict(category_counts),
            'top_categories': [{'name': cat, 'count': count} for cat, count in top_categories],
            'average_score': round(avg_score, 1),
            'top_movers': [
                {'name': p.get('name'), 'score': p.get('hot_score', p.get('final_score', 0))}
                for p in top_movers
            ],
            'hardware_count': hardware_count,
            'software_count': software_count,
            'last_updated': ProductService.get_last_updated().get('last_updated')
        }

    @staticmethod
    def generate_rss_feed() -> str:
        """生成RSS订阅源XML"""
        products = ProductService._load_products()

        # Sort by recency
        products_sorted = sorted(
            products,
            key=lambda x: x.get('first_seen', x.get('published_at', '')),
            reverse=True
        )[:20]

        items = []
        for p in products_sorted:
            name = p.get('name', '未命名')
            description = p.get('description', '')
            website = p.get('website', '')
            pub_date = p.get('first_seen', p.get('published_at', ''))
            categories = p.get('categories', [])

            item = f"""    <item>
      <title><![CDATA[{name}]]></title>
      <link>{website}</link>
      <description><![CDATA[{description}]]></description>
      <pubDate>{pub_date}</pubDate>
      {''.join(f'<category>{cat}</category>' for cat in categories)}
    </item>"""
            items.append(item)

        items_xml = '\n'.join(items)

        rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>WeeklyAI - 每周 AI 产品精选</title>
    <link>https://weeklyai.com</link>
    <description>发现最新、最热门的 AI 产品和工具</description>
    <language>zh-CN</language>
    <lastBuildDate>{datetime.now().isoformat()}</lastBuildDate>
{items_xml}
  </channel>
</rss>"""

        return rss

    @staticmethod
    def get_industry_leaders() -> Dict:
        """获取行业领军产品 - 已知名的成熟 AI 产品参考列表"""
        industry_leaders_file = os.path.join(CRAWLER_DATA_DIR, 'industry_leaders.json')

        if os.path.exists(industry_leaders_file):
            try:
                with open(industry_leaders_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading industry leaders: {e}")
                return {"categories": {}}

        return {"categories": {}}
