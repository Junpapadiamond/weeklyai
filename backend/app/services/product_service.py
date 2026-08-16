"""
产品服务 - 高级业务逻辑层

本模块只包含高级业务逻辑，底层实现委托给:
- product_repository: 数据加载、文件I/O、缓存
- product_filters: 过滤和验证逻辑
- product_sorting: 排序和多样化选择
"""

from collections import defaultdict
from datetime import datetime, timedelta
import re
from typing import List, Dict, Any, Optional

# 导入配置
from config import Config

# 导入底层模块
from . import product_filters as filters
from . import product_sorting as sorting
from .product_repository import ProductRepository


V2_HOOKS = {
    'weird_form',
    'new_behavior',
    'unexpected_combo',
    'quiet_real_problem',
    'new_interaction',
    'niche_depth',
}

V2_HOOK_LABEL_ZH = {
    'weird_form': '形态奇特',
    'new_behavior': '新行为',
    'unexpected_combo': '意外组合',
    'quiet_real_problem': '真实痛点',
    'new_interaction': '新交互',
    'niche_depth': '垂直深挖',
}

V2_HOOK_LABEL_EN = {
    'weird_form': 'weird form',
    'new_behavior': 'new behavior',
    'unexpected_combo': 'unexpected combo',
    'quiet_real_problem': 'real problem',
    'new_interaction': 'new interaction',
    'niche_depth': 'niche depth',
}

V2_HOOK_PATTERNS = {
    'weird_form': (
        'bonsai', '盆栽', 'plant', 'pendant', 'necklace', 'ring', 'smart ring',
        'glasses', '眼镜', 'badge', 'e-badge', 'pin', 'mirror', 'lamp',
        'plush', 'collar', 'wearable', '可穿戴', 'robot', '机器人',
        'lifeform', 'physical ai', 'humanoid', 'smart glasses', 'screenless',
        'wrist strap', 'card', '3mm', 'ceramic', '电子徽章', '吊坠'
    ),
    'new_behavior': (
        'autonomous', 'self-operating', 'unsupervised', 'proactive',
        'automatically', 'auto ', 'agent can', 'agentic', 'run your',
        'execute', 'learns workflow', 'without prompt', 'remembers',
        '记住', '自主', '主动', '自动执行', '全天', '实时', '会主动',
        '能感知', 'understand unspoken', 'records your entire life'
    ),
    'unexpected_combo': (
        'ai social world', 'social world', 'gamified', 'payments',
        'procurement', 'bookkeeper', 'vibe coding', 'hardware development',
        'world model', 'video game', 'quantum physics', 'enzyme',
        'brand agent', 'ai +', 'ai-powered fitness', 'screenless ai',
        '社交世界', '游戏', '支付', '采购', '会计', '硬件开发',
        '世界模型', '量子', '品牌体验', 'ai native'
    ),
    'new_interaction': (
        'voice', 'gesture', 'haptic', 'tactile', 'screenless', 'ambient',
        'touch', 'nearby sharing', 'pov', 'camera', 'conversation',
        'conversational', 'assistant', 'companion', 'emotion', '表达',
        '手势', '触觉', '无屏', '环境式', '近场分享', '触控屏',
        '陪伴', '情绪', '语音', '对话'
    ),
    'quiet_real_problem': (
        'error', 'inconsistency', 'cross-reference', 'compliance', 'claims',
        'documentation', 'phishing', 'security', 'admin', 'hospital',
        'contract', 'legal', 'workflow', 'approval', '供应商', '采购流程',
        '合规', '错误', '不一致', '病历', '理赔', '安全', '合同',
        '审批', '客户看到之前'
    ),
    'niche_depth': (
        'railway', 'warehouse', 'pallet', 'factory', 'industrial',
        'semiconductor', 'agriculture', 'beauty', 'wellness', 'law firm',
        'lawyers', 'broadcast media', 'sports', 'hospital', 'pelvic',
        'mineral', 'rail', '仓储', '铁路', '工厂', '工业', '农业',
        '美业', '医院', '律师', '运动', '矿产', '女性健康'
    ),
}

V2_FUNDING_TERMS = (
    'funding', 'raised', 'financing', 'series a', 'series b', 'series c',
    'seed round', 'pre-seed', 'valuation', 'investor', 'led by', '融资',
    '领投', '估值', '种子轮', 'a轮', 'b轮', 'c轮', '完成', '募资'
)

V2_NON_PRODUCT_TERMS = (
    'fund', 'investment platform', 'support program', 'accelerator',
    'venture capital', 'customer experience centre', '体验中心',
    '投资平台', '支持计划', '资助项目', '基金'
)

V2_FAMOUS_BRAND_TERMS = (
    'openai', 'chatgpt', 'anthropic', 'claude', 'google', 'gemini',
    'deepmind', 'meta ', 'meta-', 'ray-ban meta', 'apple', 'microsoft',
    'cursor', 'xiaomi', '小米', 'bytedance', '字节',
    'alibaba', '阿里', 'qianwen', '千问', 'tencent', '腾讯'
)

V2_FAMOUS_SURPRISE_TERMS = (
    'first', '首次', 'radical departure', 'new behavior', '新行为',
    'screenless', '无屏', 'unsupervised', '自主', 'terminal',
    'can now', '现在可以', 'quietly shipped', '新能力', 'new capability',
    'new form', '新形态', 'prototype', '首款'
)

V2_REASON_ZH = {
    'weird_form': '通过了形态惊喜门槛：AI 不再只是聊天框，而是进入一个可截图、可转发的新载体。',
    'new_behavior': '通过了行为惊喜门槛：重点是产品现在能做的新动作，而不是模型号或融资额。',
    'unexpected_combo': '通过了组合惊喜门槛：把 AI 放进一个不太常见的场景组合里，值得点进去看。',
    'quiet_real_problem': '通过了真问题门槛：不是炫技，而是把一个高频、烦人的真实流程明显压短。',
    'new_interaction': '通过了交互惊喜门槛：用户和 AI 的接触方式发生变化，不只是多一个按钮。',
    'niche_depth': '通过了垂直深挖门槛：切进一个足够具体的行业场景，问题窄但价值清楚。',
}

V2_REASON_EN = {
    'weird_form': 'Passes the form-surprise gate: AI leaves the chat box and lands in a click-worthy object.',
    'new_behavior': 'Passes the behavior-surprise gate: the product can do something materially new, not just run a newer model.',
    'unexpected_combo': 'Passes the combo-surprise gate: AI is being placed into an unexpected product context.',
    'quiet_real_problem': 'Passes the real-problem gate: it shortens a frequent painful workflow instead of chasing novelty.',
    'new_interaction': 'Passes the interaction-surprise gate: the way a person touches or talks to AI changes.',
    'niche_depth': 'Passes the niche-depth gate: the problem is narrow, but the use case is concrete enough to matter.',
}


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

    @staticmethod
    def _blog_identity(blog: Dict[str, Any]) -> str:
        """Build stable identity key for blog dedupe in feed composition."""
        source = str(blog.get("source") or "").strip().lower()
        website = str(blog.get("website") or blog.get("url") or "").strip().lower()
        name = str(blog.get("name") or blog.get("title") or "").strip().lower()
        published_at = str(blog.get("published_at") or "").strip()
        return f"{source}|{website}|{name}|{published_at}"

    @staticmethod
    def _inject_recent_cn_tail(blogs: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """Keep hybrid head ranking stable, but ensure CN recent items remain visible in tail."""
        if limit <= 0:
            return []

        selected = blogs[:limit]
        if not selected:
            return selected

        cn_recent_all = [b for b in sorting.sort_by_recency(blogs) if filters.infer_blog_market(b) == "cn"]
        if not cn_recent_all:
            return selected

        # 先刷新已有 CN 槽位为最新 CN，避免 CN 视图首屏停留在旧条目。
        cn_slots = [idx for idx, blog in enumerate(selected) if filters.infer_blog_market(blog) == "cn"]
        refresh_count = min(len(cn_slots), len(cn_recent_all))
        for slot_idx in range(refresh_count):
            selected[cn_slots[slot_idx]] = cn_recent_all[slot_idx]

        cn_in_selected = [b for b in selected if filters.infer_blog_market(b) == "cn"]
        # 仅保证基础可见度，不改变 global 主视图头部排序体验
        min_cn = min(limit, 12)
        if len(cn_in_selected) >= min_cn:
            return selected

        selected_keys = {ProductService._blog_identity(b) for b in selected}
        missing_cn = [b for b in cn_recent_all if ProductService._blog_identity(b) not in selected_keys]
        if not missing_cn:
            return selected

        need = min_cn - len(cn_in_selected)
        if need <= 0:
            return selected

        protect_head = min(limit, 40)
        replace_slots = [
            idx
            for idx in range(len(selected) - 1, protect_head - 1, -1)
            if filters.infer_blog_market(selected[idx]) != "cn"
        ]
        if not replace_slots:
            return selected

        for idx, cn_blog in zip(replace_slots, missing_cn[:need]):
            selected[idx] = cn_blog
        return selected

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
    def _screenshot_worthy_products() -> List[Dict]:
        """Return v2 editor-approved picks, newest first."""
        products = ProductService._load_products()
        picks = [ProductService._decorate_v2_pick(p) for p in products if p.get('screenshot_worthy') is True]
        return sorting.sort_by_recency(picks)

    @staticmethod
    def _v2_text(product: Dict[str, Any]) -> str:
        fields = [
            product.get('name'),
            product.get('description'),
            product.get('description_en'),
            product.get('why_matters'),
            product.get('why_matters_en'),
            product.get('latest_news'),
            product.get('latest_news_en'),
            product.get('category'),
            product.get('hardware_category'),
            product.get('hardware_type'),
            product.get('form_factor'),
            product.get('use_case'),
            product.get('source'),
            product.get('funding_total'),
        ]
        fields.extend(product.get('categories') or [])
        fields.extend(product.get('innovation_traits') or [])
        extra = product.get('extra') if isinstance(product.get('extra'), dict) else {}
        fields.extend(str(value) for value in extra.values() if isinstance(value, (str, int, float)))
        return ' '.join(str(value or '') for value in fields).lower()

    @staticmethod
    def _count_terms(text: str, terms) -> int:
        return sum(1 for term in terms if term in text)

    @staticmethod
    def _first_sentence(value: Any, max_chars: int = 86) -> str:
        text = str(value or '').strip()
        if not text:
            return ''
        text = re.split(r'(?<=[。.!?])\s+', text)[0].strip()
        text = text.replace('\n', ' ')
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 1].rstrip('，,；;。.') + '…'

    @staticmethod
    def _score_v2_candidate(product: Dict[str, Any]) -> Dict[str, Any]:
        text = ProductService._v2_text(product)
        hook_scores: Dict[str, float] = defaultdict(float)
        hook_terms: Dict[str, List[str]] = defaultdict(list)

        for hook, terms in V2_HOOK_PATTERNS.items():
            for term in terms:
                if term in text:
                    hook_scores[hook] += 1.0
                    if len(hook_terms[hook]) < 3:
                        hook_terms[hook].append(term)

        weights = {
            'weird_form': 30,
            'new_behavior': 28,
            'unexpected_combo': 24,
            'new_interaction': 23,
            'niche_depth': 18,
            'quiet_real_problem': 17,
        }
        weighted_scores = {
            hook: min(58.0, weights[hook] + (hits - 1) * 8.0)
            for hook, hits in hook_scores.items()
            if hits > 0
        }
        if weighted_scores:
            hook = max(weighted_scores, key=lambda key: (weighted_scores[key], weights[key]))
            surprise_score = weighted_scores[hook]
        else:
            hook = 'quiet_real_problem'
            surprise_score = 4.0

        multi_hook_bonus = min(18.0, max(0, len(weighted_scores) - 1) * 6.0)
        freshness = sorting.get_freshness_score(product) * 0.10
        heat = sorting.get_heat_score(product) * 0.03
        funding_hits = ProductService._count_terms(text, V2_FUNDING_TERMS)
        non_product_hits = ProductService._count_terms(text, V2_NON_PRODUCT_TERMS)

        funding_penalty = min(26.0, funding_hits * (4.5 if surprise_score < 30 else 2.0))
        non_product_penalty = 36.0 if non_product_hits and surprise_score < 46 else 0.0
        famous_hits = ProductService._count_terms(text, V2_FAMOUS_BRAND_TERMS)
        famous_surprise_hits = ProductService._count_terms(text, V2_FAMOUS_SURPRISE_TERMS)
        famous_penalty = 0.0
        if famous_hits:
            # Big labs are allowed, but legacy/bootstrap data must explain what is
            # specifically surprising about this launch before it outranks indies.
            famous_penalty = 22.0 if famous_surprise_hits == 0 else 10.0
            if surprise_score < 46:
                famous_penalty += 10.0

        score = max(
            0.0,
            surprise_score
            + multi_hook_bonus
            + freshness
            + heat
            - funding_penalty
            - non_product_penalty
            - famous_penalty
        )

        signals = []
        for candidate_hook in sorted(weighted_scores, key=weighted_scores.get, reverse=True)[:3]:
            signals.append(V2_HOOK_LABEL_EN[candidate_hook])
        if surprise_score >= 30:
            signals.append('not funding-led')

        return {
            'score': round(score, 1),
            'hook': hook,
            'signals': signals[:4],
            'matched_terms': hook_terms.get(hook, []),
            'funding_heavy': funding_hits >= 2 and surprise_score < 36,
            'non_product': bool(non_product_hits and surprise_score < 46),
            'famous_brand': bool(famous_hits),
            'famous_surprise': bool(famous_surprise_hits),
        }

    @staticmethod
    def _decorate_v2_pick(product: Dict[str, Any], force_bootstrap: bool = False) -> Dict[str, Any]:
        """Attach v2 editorial metadata without mutating the stored record."""
        clone = dict(product)
        clone['screenshot_worthy'] = True
        score = ProductService._score_v2_candidate(clone)
        if clone.get('hook') not in V2_HOOKS or force_bootstrap:
            clone['hook'] = score['hook']
        clone.setdefault('has_strong_image', bool(clone.get('logo_url') or clone.get('logo')))
        clone.setdefault('is_bootstrap_pick', force_bootstrap)
        clone['v2_score'] = score['score']
        clone['v2_signals'] = score['signals']

        hook = clone.get('hook') if clone.get('hook') in V2_HOOKS else score['hook']
        summary = ProductService._first_sentence(clone.get('description') or clone.get('why_matters'))
        summary_en = ProductService._first_sentence(clone.get('description_en') or clone.get('why_matters_en') or clone.get('description'))
        if not summary:
            summary = f"{clone.get('name') or '这个产品'} 有明确的产品惊喜点。"
        if not summary_en:
            summary_en = f"{clone.get('name') or 'This product'} has a concrete product surprise."

        clone.setdefault('pick_reason', f"{V2_REASON_ZH[hook]} 这次选择看的是“会不会让人停下来点开”，不是融资大小。")
        clone.setdefault('pick_reason_en', f"{V2_REASON_EN[hook]} This pick is ranked by stop-scroll surprise, not funding size.")

        why_text = str(clone.get('why_matters') or '').lower()
        why_en_text = str(clone.get('why_matters_en') or '').lower()
        if force_bootstrap and (not clone.get('why_matters') or ProductService._count_terms(why_text, V2_FUNDING_TERMS) >= 2):
            clone['why_matters'] = f"{summary} {V2_REASON_ZH[hook]}"
        if force_bootstrap and (not clone.get('why_matters_en') or ProductService._count_terms(why_en_text, V2_FUNDING_TERMS) >= 2):
            clone['why_matters_en'] = f"{summary_en} {V2_REASON_EN[hook]}"
        return clone

    @staticmethod
    def _bootstrap_v2_products(limit: int) -> List[Dict[str, Any]]:
        """Rank legacy data by the v2 stop-scroll rubric until curated picks exist."""
        products = ProductService._load_products()
        scored: List[Dict[str, Any]] = []
        seen_keys = set()
        for product in products:
            website = str(product.get('website') or '').strip().lower()
            if website in {'', 'unknown', 'n/a', 'na', 'none', 'null'}:
                continue
            key = ProductService._build_product_key(product)
            if key and key in seen_keys:
                continue
            seen_keys.add(key)

            decorated = ProductService._decorate_v2_pick(product, force_bootstrap=True)
            if decorated.get('v2_score', 0) < 18:
                continue
            scored.append(decorated)

        epoch = datetime(1970, 1, 1)
        scored.sort(
            key=lambda item: (
                item.get('v2_score', 0),
                sorting.get_product_date(item) or epoch,
                sorting.get_heat_score(item),
            ),
            reverse=True
        )

        if limit <= 0:
            return scored

        selected: List[Dict[str, Any]] = []
        hook_counts: Dict[str, int] = defaultdict(int)
        max_per_hook = 2 if limit > 3 else 1
        for item in scored:
            hook = item.get('hook') or 'quiet_real_problem'
            if hook_counts[hook] >= max_per_hook:
                continue
            selected.append(item)
            hook_counts[hook] += 1
            if len(selected) >= limit:
                return selected

        selected_keys = {ProductService._build_product_key(item) for item in selected}
        for item in scored:
            key = ProductService._build_product_key(item)
            if key in selected_keys:
                continue
            selected.append(item)
            if len(selected) >= limit:
                break
        return selected

    @staticmethod
    def get_hero_product() -> Optional[Dict]:
        """获取 v2 今日 Hero pick；今日无则回退最近一个并标记 is_yesterday."""
        picks = ProductService._screenshot_worthy_products()
        if not picks:
            fallback = ProductService._bootstrap_v2_products(limit=1)
            if not fallback:
                return None
            hero = fallback[0]
            hero['is_yesterday'] = True
            return hero

        hero = dict(picks[0])
        product_date = sorting.get_product_date(hero)
        if product_date and product_date.date() < datetime.now().date():
            hero['is_yesterday'] = True
        else:
            hero['is_yesterday'] = False
        return hero

    @staticmethod
    def get_picks(limit: int = 7) -> List[Dict]:
        """获取最近 N 个 v2 screenshot-worthy picks."""
        try:
            limit = max(1, min(50, int(limit)))
        except (TypeError, ValueError):
            limit = 7
        picks = ProductService._screenshot_worthy_products()
        if picks:
            return picks[:limit]
        return ProductService._bootstrap_v2_products(limit=limit)

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

        target_market = (market or '').strip().lower()
        if target_market == 'cn':
            # 仅中国区按新鲜度优先，保证本土源更新稳定可见。
            blogs = sorting.sort_by_recency(blogs)
        else:
            # 保持 global/hybrid/us 原有热度排序行为不变。
            blogs = sorting.sort_by_trending(blogs)

        if target_market in {'', 'all', 'hybrid', 'global'}:
            return ProductService._inject_recent_cn_tail(blogs, limit)
        return blogs[:limit]

    @staticmethod
    def get_blogs_by_source(source: str, limit: int = 20, market: str = '') -> List[Dict]:
        """按来源获取博客内容"""
        blogs = ProductService._load_blogs()
        blogs = filters.filter_blogs_by_market(blogs, market)
        filtered = filters.filter_by_source(blogs, source)

        target_market = (market or '').strip().lower()
        source_name = (source or '').strip().lower()
        if target_market == 'cn' or source_name in {'cn_news', 'cn_news_glm'}:
            filtered = sorting.sort_by_recency(filtered)
        return filtered[:limit]

    @staticmethod
    def get_dark_horse_products(limit: int = 10, min_index: int = 4) -> List[Dict]:
        """Deprecated: 获取旧黑马端点兼容数据，v2 优先返回 screenshot_worthy picks.

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
        v2_picks = [p for p in products if p.get('screenshot_worthy') is True]
        if v2_picks:
            return sorting.sort_by_recency(v2_picks)[:limit]
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
        """Deprecated: 获取旧潜力股端点兼容数据，v2 优先返回 screenshot_worthy picks.

        参数:
        - limit: 返回数量

        排序规则: 评分 > 融资金额 > 用户数/估值
        """
        products = ProductService._load_products()
        v2_picks = [p for p in products if p.get('screenshot_worthy') is True]
        if v2_picks:
            return sorting.sort_by_recency(v2_picks)[:limit]

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
    def get_daily_featured() -> Optional[Dict]:
        """获取「今日精选」单品 - 每天固定展示当周最高分黑马产品"""
        products = ProductRepository.load_products()
        candidates = [p for p in products if (p.get("dark_horse_index") or 0) >= 4]
        if not candidates:
            candidates = [p for p in products if (p.get("dark_horse_index") or 0) >= 3]
        if not candidates:
            return None
        candidates_sorted = sorted(candidates, key=sorting.product_score_key, reverse=True)
        day_index = datetime.now().timetuple().tm_yday % len(candidates_sorted)
        return candidates_sorted[day_index]

    @staticmethod
    def get_industry_leaders() -> Dict:
        """获取行业领军产品 - 已知名的成熟 AI 产品参考列表"""
        return ProductRepository.load_industry_leaders()
