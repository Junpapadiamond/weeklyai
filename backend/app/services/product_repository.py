"""
产品数据仓库 - 负责数据加载、文件I/O和缓存管理
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from functools import lru_cache
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
        _mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=MONGO_SERVER_SELECTION_TIMEOUT_MS,
                                    connectTimeoutMS=2000, socketTimeoutMS=5000, maxPoolSize=10)
        _mongo_client.admin.command('ping')
        _mongo_db = _mongo_client.get_default_database(os.getenv('MONGO_DB_NAME', 'weeklyai'))
        _mongo_fail_until = None
        print("  Backend connected to MongoDB")
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
        print(f"  MongoDB connection failed: {e}; using JSON files")
        return None


class ProductRepository:
    """产品数据仓库类 - 管理数据加载和缓存"""

    _cached_products = None
    _cache_time = None
    _cache_filter_module = None
    _cache_duration = 300  # 5分钟缓存
    _cached_blogs = None
    _blogs_cache_time = None
    _blogs_cache_duration = BLOG_CACHE_SECONDS
    _storage_source = 'snapshot'

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
        if cls._cached_products is not None and cls._cache_time and cls._cache_filter_module is filters_module:
            age = (now - cls._cache_time).total_seconds()
            if age < cls._cache_duration:
                return cls._cached_products

        products: List[Dict] = []

        # 1) MongoDB path when configured
        if _mongo_uri_configured():
            products = cls.load_from_mongodb()
        cls._storage_source = 'mongodb' if products else 'snapshot'

        # 2) JSON fallback path
        if not products:
            products = cls._load_from_crawler_file()
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
        cls._cache_filter_module = filters_module

        return products

    @classmethod
    def _load_from_crawler_file(cls) -> List[Dict]:
        """从策展产品文件加载 (products_featured.json)

        这是唯一的产品数据源，包含人工审核的高质量产品。
        不会加载爬虫的原始输出 (products_latest.json)。
        """
        # 只加载策展产品文件
        if not os.path.exists(PRODUCTS_FEATURED_FILE):
            print("  products_featured.json unavailable; no products will be invented")
            return []

        try:
            with open(PRODUCTS_FEATURED_FILE, 'r', encoding='utf-8') as f:
                products = json.load(f)

            # 添加 _id 字段
            for i, p in enumerate(products):
                if '_id' not in p:
                    p['_id'] = str(p.get('id') or p.get('_sync_key') or i + 1)
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

            print(f"  Loaded {len(products)} curated products")
            return products
        except Exception as e:
            print(f"  Curated product load failed: {e}")
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

        # Preserve existing links; new products use their stable domain/path key.
        legacy_ids = cls._legacy_ids()
        for p in ordered:
            key = cls._build_product_key(p)
            stable_id = 'p_' + hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]
            p['_id'] = str(legacy_ids.get(key) or p.get('id') or stable_id)

        return ordered

    @staticmethod
    @lru_cache(maxsize=1)
    def _legacy_ids():
        try:
            with open(os.path.join(CRAWLER_DATA_DIR, 'product_legacy_ids.json'), encoding='utf-8') as source:
                result = json.load(source)
                return result if isinstance(result, dict) else {}
        except (OSError, ValueError):
            return {}

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
                print(f"  Loaded {len(products)} products from MongoDB")

            # 添加 _id 字段
            for i, p in enumerate(products):
                if '_id' not in p:
                    p['_id'] = str(p.get('id') or p.get('_sync_key') or i + 1)
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
            print(f"  MongoDB load failed: {e}")
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
            print(f"  MongoDB blog load failed: {e}")
            return []

    @staticmethod
    def get_last_updated() -> Dict[str, Any]:
        """获取最近一次数据更新时间."""
        try:
            with open(LAST_UPDATED_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = {}

        last_updated = data.get('last_updated')

        try:
            parsed = datetime.fromisoformat(str(last_updated).replace('Z', '+00:00'))
            hours_ago = round((datetime.now(parsed.tzinfo) - parsed).total_seconds() / 3600, 1)
        except Exception:
            hours_ago = None

        products = ProductRepository.load_products()
        dates = [sorting.get_effective_date(p) for p in products]
        newest = max((date for date in dates if date and date <= datetime.utcnow()), default=None)
        return {'last_updated': last_updated, 'hours_ago': hours_ago,
                'product_last_updated': newest.isoformat() if newest else None,
                'product_hours_ago': round((datetime.utcnow() - newest).total_seconds() / 3600, 1) if newest else None,
                'storage': ProductRepository._storage_source}

    @staticmethod
    @lru_cache(maxsize=1)
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
