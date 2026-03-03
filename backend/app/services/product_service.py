"""
产品服务 - 高级业务逻辑层

本模块只包含高级业务逻辑，底层实现委托给:
- product_repository: 数据加载、文件I/O、缓存
- product_filters: 过滤和验证逻辑
- product_sorting: 排序和多样化选择
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# 导入配置
from config import Config

# 导入底层模块
from . import product_filters as filters
from . import product_sorting as sorting
from .product_repository import ProductRepository


class ProductService:
    """产品服务类 - 高级业务逻辑"""

    # ========== 缓存管理 (委托给 Repository) ==========

    @classmethod
    def refresh_cache(cls):
        """强制刷新缓存"""
        ProductRepository.refresh_cache()

    @classmethod
    def _load_products(cls) -> List[Dict]:
        """加载产品数据（带缓存）"""
        return ProductRepository.load_products(filters_module=filters)

    @classmethod
    def _load_blogs(cls) -> List[Dict]:
        """加载博客/新闻/讨论数据"""
        return ProductRepository.load_blogs()

    # ========== 排序工具方法 (委托给 sorting 模块) ==========

    @staticmethod
    def _parse_funding(funding: str) -> float:
        """解析融资金额字符串为数值（单位：百万美元）"""
        return sorting.parse_funding(funding)

    @staticmethod
    def _get_valuation_score(product: Dict) -> float:
        """获取估值/用户数综合分数"""
        return sorting.get_valuation_score(product)

    @staticmethod
    def _parse_date(value: Any) -> Optional[datetime]:
        """Parse ISO or YYYY-MM-DD dates safely."""
        return sorting.parse_date(value)

    @staticmethod
    def _get_product_date(product: Dict[str, Any]) -> Optional[datetime]:
        """Pick a comparable date field for freshness checks."""
        return sorting.get_product_date(product)

    @staticmethod
    def _sort_by_score_funding_valuation(products: List[Dict]) -> List[Dict]:
        """按评分 > 融资 > 估值/用户数排序"""
        return sorting.sort_by_score_funding_valuation(products)

    @staticmethod
    def _diversify_products(
        products: List[Dict],
        limit: int,
        max_per_category: int = 4,
        max_per_source: int = 5,
        hardware_ratio: float = 0.4,
        max_per_hw_category: int = 3
    ) -> List[Dict]:
        """多样化选择算法，保证榜单均衡"""
        return sorting.diversify_products(
            products, limit, max_per_category, max_per_source,
            hardware_ratio, max_per_hw_category
        )

    # ========== 过滤工具方法 (委托给 filters 模块) ==========

    @staticmethod
    def _build_product_key(product: Dict[str, Any]) -> str:
        """Normalize a product key for dedupe/merge."""
        return filters.build_product_key(product)

    @staticmethod
    def _is_blocked(product: Dict[str, Any]) -> bool:
        """Filter non-end-user sources/domains."""
        return filters.is_blocked(product)

    @staticmethod
    def _is_well_known(product: Dict[str, Any]) -> bool:
        """检查是否为著名产品（除非有新功能才显示）"""
        return filters.is_well_known(product)

    @staticmethod
    def _normalize_products(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize products and drop blocked sources/domains + well-known products."""
        return filters.normalize_products(products)

    @staticmethod
    def _is_hardware(product: Dict[str, Any]) -> bool:
        """判断产品是否为硬件"""
        return filters.is_hardware(product)

    # ========== 数据仓库方法 (委托给 Repository) ==========

    @staticmethod
    def get_last_updated() -> Dict[str, Any]:
        """获取最近一次数据更新时间."""
        return ProductRepository.get_last_updated()

    # ========== 业务逻辑方法 ==========

    @staticmethod
    def get_trending_products(limit: int = 5) -> List[Dict]:
        """获取热门推荐产品 (多样化)"""
        products = ProductService._load_products()
        products = filters.filter_by_dark_horse_index(products, min_index=2)

        # 按 hot_score 或 final_score 排序
        sorted_products = sorting.sort_by_trending(products)
        return sorting.diversify_products(
            sorted_products,
            limit,
            max_per_category=2,
            max_per_source=2,
            hardware_ratio=0.4,
            max_per_hw_category=2
        )

    @staticmethod
    def get_weekly_top_products(limit: int = 15, sort_by: str = 'composite') -> List[Dict]:
        """获取本周Top产品

        排序规则:
        - composite: 综合分（热度 + 新鲜度 + 低权重融资）
        - trending: 热度
        - recency: 时间
        - funding: 兼容旧参数（内部保留）

        多样化规则: 硬件 ≤40%, 每个硬件子类别 ≤3, 每个软件类别 ≤4
        """
        products = ProductService._load_products()
        products = filters.filter_by_dark_horse_index(products, min_index=2)

        # 统一排序入口（含历史参数兼容）
        sorted_products = sorting.sort_weekly_top(products, sort_by=sort_by)

        if limit <= 0:
            return sorted_products

        # 多样化选择: 硬件 ≤40%, 每个硬件子类别 ≤3 (避免全是 drone)
        return sorting.diversify_products(
            sorted_products,
            limit,
            max_per_category=4,
            max_per_source=5,
            hardware_ratio=0.4,
            max_per_hw_category=3
        )

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
        keyword = (keyword or '').strip()
        categories = categories or []
        product_type = (product_type or 'all').strip().lower()
        sort_by = (sort_by or 'trending').strip().lower()

        if product_type not in {'all', 'software', 'hardware'}:
            product_type = 'all'
        if sort_by not in {'trending', 'rating', 'users'}:
            sort_by = 'trending'

        try:
            page = max(1, int(page))
        except (TypeError, ValueError):
            page = 1
        try:
            limit = max(1, min(50, int(limit)))
        except (TypeError, ValueError):
            limit = 15

        products = ProductService._load_products()
        results = products.copy()
        keyword_scores: Dict[int, float] = {}

        # 关键词筛选
        if keyword:
            filtered_by_keyword = []
            for product in results:
                relevance = filters.compute_keyword_score(product, keyword)
                if relevance <= 0:
                    continue
                keyword_scores[id(product)] = relevance
                filtered_by_keyword.append(product)
            results = filtered_by_keyword

        # 分类筛选（支持多选，OR逻辑）
        results = filters.filter_by_categories(results, categories)

        # 类型筛选
        results = filters.filter_by_type(results, product_type)

        # 基础排序
        if sort_by == 'trending':
            sorted_results = sorting.sort_by_trending(results)
        elif sort_by == 'rating':
            sorted_results = sorting.sort_by_rating(results)
        elif sort_by == 'users':
            sorted_results = sorting.sort_by_users(results)
        else:
            sorted_results = sorting.sort_by_trending(results)

        # 带关键词时优先相关性，再用所选排序作为次序。
        if keyword:
            sort_rank = {id(product): idx for idx, product in enumerate(sorted_results)}
            results = sorted(
                sorted_results,
                key=lambda product: (
                    -keyword_scores.get(id(product), 0.0),
                    sort_rank.get(id(product), len(sorted_results))
                )
            )
        else:
            results = sorted_results

        # 分页
        total = len(results)
        start = min(max((page - 1) * limit, 0), total)
        end = min(start + limit, total)
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
        filtered = filters.filter_by_category(products, category)

        # 按热度排序
        filtered = sorting.sort_by_trending(filtered)
        return filtered[:limit]

    @staticmethod
    def get_products_by_source(source: str, limit: int = 20) -> List[Dict]:
        """按来源获取产品"""
        products = ProductService._load_products()
        filtered = filters.filter_by_source(products, source)
        return filtered[:limit]

    @staticmethod
    def get_blogs_news(limit: int = 20, market: str = '') -> List[Dict]:
        """获取博客/新闻/讨论内容"""
        blogs = ProductService._load_blogs()
        blogs = filters.filter_blogs_by_market(blogs, market)

        # 按分数排序
        blogs = sorting.sort_by_trending(blogs)
        return blogs[:limit]

    @staticmethod
    def get_blogs_by_source(source: str, limit: int = 20, market: str = '') -> List[Dict]:
        """按来源获取博客内容"""
        blogs = ProductService._load_blogs()
        blogs = filters.filter_blogs_by_market(blogs, market)
        filtered = filters.filter_by_source(blogs, source)
        return filtered[:limit]

    @staticmethod
    def get_dark_horse_products(limit: int = 10, min_index: int = 4) -> List[Dict]:
        """获取黑马产品 - 高潜力新兴产品 (多样化)

        参数:
        - limit: 返回数量
        - min_index: 最低黑马指数 (1-5)

        刷新规则 (保持本周黑马新鲜度):
        - 大部分产品: 严格 5 天后移出本周黑马 → 更多推荐
        - TOP 1 产品 (最高评分+融资): 可保留 10 天
        - 如果 latest_news 更新, 重置计时器
        - 空状态回退: 按评分显示 top 10

        排序规则: 评分 > 融资金额 > 用户数/估值
        多样化规则: 硬件 ≤40%, 每个硬件子类别 ≤3
        """
        products = ProductService._load_products()
        now = datetime.now()
        fresh_cutoff = now - timedelta(days=Config.DARK_HORSE_FRESH_DAYS)  # 5 days
        sticky_cutoff = now - timedelta(days=Config.DARK_HORSE_STICKY_DAYS)  # 10 days

        # 筛选有 dark_horse_index 且 >= min_index 的产品
        all_candidates = filters.filter_by_dark_horse_index(products, min_index=min_index)

        # 黑马区优先展示“可展示质量”产品，避免 unknown 网站 + 占位 Logo 的低质体验。
        def _is_presentable(product: Dict[str, Any]) -> bool:
            website = str(product.get('website') or '').strip().lower()
            has_usable_website = website not in {'', 'unknown', 'n/a', 'na', 'none', 'null'}
            if has_usable_website:
                return True
            logo_url = str(product.get('logo_url') or '').strip()
            needs_verification = bool(product.get('needs_verification'))
            return bool(logo_url) and not needs_verification

        presentable_candidates = [p for p in all_candidates if _is_presentable(p)]
        if presentable_candidates:
            # 如果有足够可展示产品，优先使用它们；否则回退到全量候选避免空列表。
            min_presentable = min(limit, 5)
            if len(presentable_candidates) >= min_presentable:
                all_candidates = presentable_candidates

        if not all_candidates:
            return []

        # 找到 TOP 1 产品 (最高评分+融资, 可保留 10 天)
        top_product = max(all_candidates, key=sorting.product_score_key)
        top_product_date = sorting.get_effective_date(top_product)
        top_product_eligible = (
            top_product_date and top_product_date >= sticky_cutoff
        )

        # 筛选新鲜产品 (5 天内)
        fresh_candidates = []
        for p in all_candidates:
            effective_date = sorting.get_effective_date(p)
            if effective_date and effective_date >= fresh_cutoff:
                fresh_candidates.append(p)

        # 如果 TOP 1 产品不在新鲜列表但仍在 10 天内, 添加到候选
        if top_product_eligible and top_product not in fresh_candidates:
            fresh_candidates.append(top_product)

        # 仅在“完全空状态”时回退到历史候选，避免把过期产品补回本周黑马
        if not fresh_candidates:
            # 按评分+融资排序所有候选
            all_candidates_sorted = sorted(
                all_candidates,
                key=lambda x: (
                    -(x.get('dark_horse_index', 0) or 0),
                    -sorting.parse_funding(x.get('funding_total', '')),
                    -sorting.get_valuation_score(x)
                )
            )
            # 补充不在新鲜列表中的产品
            for p in all_candidates_sorted:
                if p not in fresh_candidates:
                    fresh_candidates.append(p)
                if len(fresh_candidates) >= limit:
                    break

        def sort_key(product: Dict[str, Any]):
            """排序: 新鲜度优先, 然后评分 > 融资"""
            effective_date = sorting.get_effective_date(product) or datetime(1970, 1, 1)
            is_fresh = effective_date >= fresh_cutoff
            is_top_sticky = (product == top_product and top_product_eligible)

            return (
                0 if (is_fresh or is_top_sticky) else 1,  # 新鲜/置顶优先
                -(product.get('dark_horse_index', 0) or 0),
                -sorting.parse_funding(product.get('funding_total', '')),
                -sorting.get_valuation_score(product)
            )

        fresh_candidates.sort(key=sort_key)

        # 使用多样化算法选择产品 (硬件 ≤40%, 每个硬件子类别 ≤3)
        selected = sorting.diversify_products(
            fresh_candidates,
            limit,
            max_per_category=4,
            max_per_source=5,
            hardware_ratio=0.4,
            max_per_hw_category=2
        )

        return selected

    @staticmethod
    def get_rising_star_products(limit: int = 20) -> List[Dict]:
        """获取潜力股产品 - 2-3分的有潜力产品

        参数:
        - limit: 返回数量

        排序规则: 评分 > 融资金额 > 用户数/估值
        """
        products = ProductService._load_products()

        # 筛选 dark_horse_index 为 2-3 的产品
        rising_stars = filters.filter_by_dark_horse_index(products, min_index=2, max_index=3)

        # 排序: 评分 > 融资 > 估值/用户数
        rising_stars = sorting.sort_by_score_funding_valuation(rising_stars)

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

        return sorting.diversify_products(fresh_products, limit, max_per_category=3, max_per_source=3)

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
        products_sorted = sorting.sort_by_recency(products)[:20]

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
        return ProductRepository.load_industry_leaders()
