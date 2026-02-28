"""
产品数据仓库 - 负责数据加载、文件I/O和缓存管理
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Sorting helpers for merge decisions
from . import product_sorting as sorting
from .env_utils import sanitize_env_value

# MongoDB support
try:
    from pymongo import MongoClient
    HAS_MONGO = True
except ImportError:
    HAS_MONGO = False

# 导入配置
from config import Config

# 爬虫数据文件路径 (支持环境变量配置，Docker 部署时使用 /data)
CRAWLER_DATA_DIR = Config.DATA_PATH if os.path.exists(Config.DATA_PATH) else os.path.join(
    os.path.dirname(__file__),
    '..', '..', '..', 'crawler', 'data'
)
PRODUCTS_FEATURED_FILE = os.path.join(CRAWLER_DATA_DIR, 'products_featured.json')
BLOGS_NEWS_FILE = os.path.join(CRAWLER_DATA_DIR, 'blogs_news.json')
CRAWLER_DATA_FILE = os.path.join(CRAWLER_DATA_DIR, 'products_latest.json')
LAST_UPDATED_FILE = os.path.join(CRAWLER_DATA_DIR, 'last_updated.json')
DARK_HORSES_DIR = os.path.join(CRAWLER_DATA_DIR, 'dark_horses')

# MongoDB connection
_mongo_client = None
_mongo_db = None
_mongo_fail_until = None


def _get_env_int(name: str, default: int, minimum: int = 0) -> int:
    """Read an integer environment variable with clamped fallback."""
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default


MONGO_SERVER_SELECTION_TIMEOUT_MS = _get_env_int("MONGO_SERVER_SELECTION_TIMEOUT_MS", 800, minimum=100)
MONGO_FAILURE_COOLDOWN_SECONDS = _get_env_int("MONGO_FAILURE_COOLDOWN_SECONDS", 60, minimum=0)
BLOG_CACHE_SECONDS = _get_env_int("BLOG_CACHE_SECONDS", 60, minimum=1)


def _mongo_uri_configured() -> bool:
    """Whether MONGO_URI is explicitly configured."""
    return bool(sanitize_env_value(os.getenv('MONGO_URI', '')))


def get_mongo_db():
    """Get MongoDB connection (lazy initialization)."""
    global _mongo_client, _mongo_db, _mongo_fail_until
    if not HAS_MONGO:
        return None
    if not _mongo_uri_configured():
        return None
    if _mongo_db is not None:
        return _mongo_db
    if _mongo_fail_until and datetime.now() < _mongo_fail_until:
        return None
    try:
        mongo_uri = sanitize_env_value(os.environ.get('MONGO_URI', ''))
        if not mongo_uri:
            return None
        _mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=MONGO_SERVER_SELECTION_TIMEOUT_MS)
        _mongo_client.admin.command('ping')
        _mongo_db = _mongo_client.get_database()
        _mongo_fail_until = None
        print("  ✓ Backend connected to MongoDB")
        return _mongo_db
    except Exception as e:
        if _mongo_client is not None:
            try:
                _mongo_client.close()
            except Exception:
                pass
            _mongo_client = None
        _mongo_db = None
        _mongo_fail_until = datetime.now() + timedelta(seconds=MONGO_FAILURE_COOLDOWN_SECONDS)
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


class ProductRepository:
    """产品数据仓库类 - 管理数据加载和缓存"""

    _cached_products = None
    _cache_time = None
    _cache_duration = 300  # 5分钟缓存
    _cached_blogs = None
    _blogs_cache_time = None
    _blogs_cache_duration = BLOG_CACHE_SECONDS

    @classmethod
    def refresh_cache(cls):
        """强制刷新缓存"""
        cls._cached_products = None
        cls._cache_time = None
        cls._cached_blogs = None
        cls._blogs_cache_time = None

    @classmethod
    def load_products(cls, filters_module=None) -> List[Dict]:
        """加载产品数据（带缓存）。

        优先级:
        1) 若设置了 MONGO_URI，优先读取 MongoDB（适配 Vercel）。
        2) 若 MongoDB 不可用或为空，则回退到本地 JSON 逻辑。
        """
        now = datetime.now()

        # 检查缓存
        if cls._cached_products and cls._cache_time:
            age = (now - cls._cache_time).total_seconds()
            if age < cls._cache_duration:
                return cls._cached_products

        products: List[Dict] = []

        # 1) MongoDB path when configured
        if _mongo_uri_configured():
            products = cls.load_from_mongodb()

        # 2) JSON fallback path
        if not products:
            products = cls._load_from_crawler_file()
            if not products:
                products = SAMPLE_PRODUCTS.copy()
            curated = cls._load_curated_dark_horses()
            products = cls._merge_curated_products(products, curated, filters_module)

        # 4. 统一字段 & 过滤
        if filters_module:
            products = filters_module.normalize_products(products)

        # 5. 去重合并（避免重复展示）
        products = cls._dedupe_products(products, filters_module)

        # 更新缓存
        cls._cached_products = products
        cls._cache_time = now

        return products

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
                if 'extra' in p and isinstance(p['extra'], str):
                    try:
                        p['extra'] = json.loads(p['extra'])
                    except Exception:
                        pass
                if 'community_verdict' in p and isinstance(p['community_verdict'], str):
                    try:
                        p['community_verdict'] = json.loads(p['community_verdict'])
                    except Exception:
                        pass

            print(f"  ✓ 加载 {len(products)} 个策展产品")
            return products
        except Exception as e:
            print(f"  ⚠ 加载策展产品失败: {e}")
            return []

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
                                curated: List[Dict[str, Any]],
                                filters_module=None) -> List[Dict[str, Any]]:
        """Merge curated products into base list (prefer curated fields)."""
        if not curated:
            return products

        def _key(p: Dict[str, Any]) -> str:
            if filters_module and hasattr(filters_module, 'build_product_key'):
                return filters_module.build_product_key(p)
            return cls._build_product_key(p)

        by_key = {_key(p): p for p in products if p}
        for item in curated:
            normalized = cls._normalize_curated_product(item)
            if not normalized:
                continue
            if filters_module and filters_module.is_blocked(normalized):
                continue
            key = _key(normalized)
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

    @staticmethod
    def _build_product_key(product: Dict[str, Any]) -> str:
        """Normalize a product key for dedupe/merge."""
        website = (product.get('website') or '').strip().lower()
        if website:
            # Normalize scheme/www/port and keep first path segment when available
            try:
                if not website.startswith(('http://', 'https://')) and '.' in website:
                    website = f"https://{website}"
                from urllib.parse import urlparse
                parsed = urlparse(website)
                domain = (parsed.netloc or '').lower()
                if domain.startswith('www.'):
                    domain = domain[4:]
                domain = domain.split(':')[0]
                path = (parsed.path or '').strip('/')
                if path:
                    first = path.split('/')[0]
                    if len(first) > 1:
                        return f"{domain}/{first}"
                return domain
            except Exception:
                return website
        name_key = (product.get('name') or '').strip().lower()
        return ''.join(ch for ch in name_key if ch.isalnum())

    @classmethod
    def _merge_product_fields(cls, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Merge source fields into target with simple quality heuristics."""
        if not source:
            return

        numeric_max_fields = {'dark_horse_index', 'final_score', 'hot_score', 'trending_score', 'rating'}
        date_fields = {'discovered_at', 'first_seen', 'published_at', 'news_updated_at'}
        country_fields = {'region', 'country_code', 'country_name', 'country_flag', 'country_display', 'country_source'}
        country_source_priority = {
            'unknown': 0,
            # Keep old region-based fallbacks at the lowest rank so better evidence can replace them.
            'region:search_fallback': -1,
            'region:fallback': -1,
            'website:cc_tld': 1,
            'region:legacy': 2,
            'curated:region': 3,
        }

        def _is_unknown_country(field: str, value: Any) -> bool:
            text = str(value or '').strip().lower()
            if field == 'country_code':
                return text in {'', 'unknown'}
            if field == 'country_flag':
                return text in {'', '🌍'}
            if field == 'region':
                return text in {'', 'unknown', '🌍'}
            return text in {'', 'unknown', 'n/a', 'na', 'none', 'null'}

        for field, value in source.items():
            if value in (None, '', [], {}):
                continue

            if field in country_fields:
                current = target.get(field)
                if field == 'country_source':
                    current_rank = country_source_priority.get(str(current or '').strip().lower(), 4)
                    value_rank = country_source_priority.get(str(value or '').strip().lower(), 4)
                    if value_rank >= current_rank:
                        target[field] = value
                    continue
                if _is_unknown_country(field, current) and not _is_unknown_country(field, value):
                    target[field] = value
                    continue
                if not current:
                    target[field] = value
                continue

            if field in numeric_max_fields:
                try:
                    current = target.get(field) or 0
                    target[field] = max(float(current), float(value))
                except Exception:
                    if not target.get(field):
                        target[field] = value
                continue

            if field == 'funding_total':
                try:
                    current = target.get(field) or ''
                    if sorting.parse_funding(value) > sorting.parse_funding(current):
                        target[field] = value
                except Exception:
                    if not target.get(field):
                        target[field] = value
                continue

            if field in date_fields:
                try:
                    current = target.get(field)
                    current_dt = sorting.parse_date(current)
                    value_dt = sorting.parse_date(value)
                    if value_dt and (not current_dt or value_dt > current_dt):
                        target[field] = value
                except Exception:
                    if not target.get(field):
                        target[field] = value
                continue

            # Prefer longer/denser text for narrative fields
            if field in {'description', 'why_matters', 'latest_news'}:
                current = str(target.get(field) or '')
                candidate = str(value)
                if len(candidate) > len(current):
                    target[field] = value
                continue

            # Default: fill missing fields
            if not target.get(field):
                target[field] = value

    @classmethod
    def _dedupe_products(cls, products: List[Dict[str, Any]],
                         filters_module=None) -> List[Dict[str, Any]]:
        """Deduplicate products by normalized key, merging fields."""
        if not products:
            return []

        def _key(p: Dict[str, Any]) -> str:
            if filters_module and hasattr(filters_module, 'build_product_key'):
                return filters_module.build_product_key(p)
            return cls._build_product_key(p)

        def _name_key(p: Dict[str, Any]) -> str:
            raw_name = (p.get('name') or '').strip()
            if not raw_name:
                return ''
            # If name contains non-ASCII, only dedupe on exact normalized name
            if any(ord(ch) > 127 for ch in raw_name):
                normalized = ''.join(raw_name.lower().split())
                return normalized if len(normalized) >= 2 else ''

            # ASCII name: normalize punctuation and require a minimum length
            import re as _re
            key = _re.sub(r'[^a-z0-9]+', '', raw_name.lower())
            if len(key) < 4:
                return ''
            if not _re.search(r'[a-z0-9]', key):
                return ''
            return key

        def _name_key_loose(p: Dict[str, Any]) -> str:
            """Looser name key for near-duplicate variants like '* Smart Glasses'."""
            raw_name = (p.get('name') or '').strip()
            if not raw_name:
                return ''
            if any(ord(ch) > 127 for ch in raw_name):
                return ''

            import re as _re
            tokens = _re.findall(r'[a-z0-9]+', raw_name.lower())
            if not tokens:
                return ''

            stopwords = {
                'ai', 'smart', 'intelligent', 'android', 'xr', 'ar', 'vr',
                'glass', 'glasses', 'device', 'wearable', 'edition', 'version',
                'model', 'pro', 'plus', 'ultra', 'new', 'first',
            }
            core = [t for t in tokens if t not in stopwords and len(t) > 1]
            if len(core) < 2:
                return ''
            return ''.join(core[:4])

        by_key: Dict[str, Dict[str, Any]] = {}
        by_name: Dict[str, Dict[str, Any]] = {}
        by_name_loose: Dict[str, Dict[str, Any]] = {}
        ordered: List[Dict[str, Any]] = []

        for product in products:
            if not isinstance(product, dict):
                continue
            key = _key(product)
            name_key = _name_key(product)
            name_key_loose = _name_key_loose(product)

            if key and key in by_key:
                cls._merge_product_fields(by_key[key], product)
                continue

            if name_key and name_key in by_name:
                target = by_name[name_key]
                cls._merge_product_fields(target, product)
                if key:
                    by_key[key] = target
                continue

            if name_key_loose and name_key_loose in by_name_loose:
                target = by_name_loose[name_key_loose]
                cls._merge_product_fields(target, product)
                if key:
                    by_key[key] = target
                if name_key:
                    by_name[name_key] = target
                continue

            if key:
                by_key[key] = product
            if name_key:
                by_name[name_key] = product
            if name_key_loose:
                by_name_loose[name_key_loose] = product
            ordered.append(product)

        # Re-assign _id to keep uniqueness after dedupe
        for i, p in enumerate(ordered):
            p['_id'] = str(i + 1)

        return ordered

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
    def load_from_mongodb(cls) -> List[Dict]:
        """从MongoDB加载产品数据"""
        from .product_filters import BLOCKED_SOURCES

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
                if 'community_verdict' in p and isinstance(p['community_verdict'], str):
                    try:
                        p['community_verdict'] = json.loads(p['community_verdict'])
                    except Exception:
                        pass

            return products
        except Exception as e:
            print(f"  ⚠ MongoDB load failed: {e}")
            return []

    @classmethod
    def load_blogs(cls) -> List[Dict]:
        """加载博客/新闻/讨论数据（优先 MongoDB，回退 JSON）。"""
        now = datetime.now()

        # 检查缓存
        if cls._cached_blogs is not None and cls._blogs_cache_time:
            age = (now - cls._blogs_cache_time).total_seconds()
            if age < cls._blogs_cache_duration:
                return cls._cached_blogs

        blogs: List[Dict] = []

        if _mongo_uri_configured():
            blogs = cls.load_blogs_from_mongodb()

        if not blogs:
            if not os.path.exists(BLOGS_NEWS_FILE):
                cls._cached_blogs = []
                cls._blogs_cache_time = now
                return []

            try:
                with open(BLOGS_NEWS_FILE, 'r', encoding='utf-8') as f:
                    blogs = json.load(f)

                # 添加 _id 字段
                for i, b in enumerate(blogs):
                    if '_id' not in b:
                        b['_id'] = f"blog_{i + 1}"
            except Exception as e:
                print(f"加载博客数据失败: {e}")
                blogs = []

        cls._cached_blogs = blogs
        cls._blogs_cache_time = now
        return blogs

    @classmethod
    def load_blogs_from_mongodb(cls) -> List[Dict]:
        """从 MongoDB 加载博客数据。"""
        db = get_mongo_db()
        if db is None:
            return []

        try:
            collection = db.blogs
            blogs = list(collection.find({}, {'_id': 0}).sort('published_at', -1))
            if not blogs:
                blogs = list(collection.find({}, {'_id': 0}).sort('created_at', -1))

            for i, b in enumerate(blogs):
                if '_id' not in b:
                    b['_id'] = f"blog_{i + 1}"
            return blogs
        except Exception as e:
            print(f"  ⚠ MongoDB blog load failed: {e}")
            return []

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
    def load_industry_leaders() -> Dict:
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
