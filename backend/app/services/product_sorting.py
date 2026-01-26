"""
产品排序工具 - 负责所有排序和多样化选择逻辑
"""

import re
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any, Optional


def parse_funding(funding: str) -> float:
    """解析融资金额字符串为数值（单位：百万美元）"""
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


def get_valuation_score(product: Dict) -> float:
    """获取估值/用户数综合分数"""
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


def parse_date(value: Any) -> Optional[datetime]:
    """Parse ISO or YYYY-MM-DD dates safely."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    try:
        if 'T' in value:
            return datetime.fromisoformat(value.replace('Z', '+00:00').split('+')[0])
        return datetime.strptime(value, '%Y-%m-%d')
    except Exception:
        return None


def get_product_date(product: Dict[str, Any]) -> Optional[datetime]:
    """Pick a comparable date field for freshness checks."""
    return parse_date(
        product.get('discovered_at') or product.get('first_seen') or product.get('published_at')
    )


def sort_by_score_funding_valuation(products: List[Dict]) -> List[Dict]:
    """按评分 > 融资 > 估值/用户数排序"""
    return sorted(
        products,
        key=lambda x: (
            x.get('dark_horse_index', 0),
            parse_funding(x.get('funding_total', '')),
            get_valuation_score(x)
        ),
        reverse=True
    )


def sort_by_trending(products: List[Dict]) -> List[Dict]:
    """按热度排序 (hot_score > final_score > trending_score)"""
    return sorted(
        products,
        key=lambda x: x.get('hot_score', x.get('final_score', x.get('trending_score', 0))),
        reverse=True
    )


def sort_by_rating(products: List[Dict]) -> List[Dict]:
    """按评分排序"""
    return sorted(products, key=lambda x: x.get('rating', 0), reverse=True)


def sort_by_users(products: List[Dict]) -> List[Dict]:
    """按用户数排序"""
    return sorted(products, key=lambda x: x.get('weekly_users', 0), reverse=True)


def sort_by_recency(products: List[Dict]) -> List[Dict]:
    """按时间新鲜度排序"""
    return sorted(
        products,
        key=lambda x: x.get('first_seen', x.get('published_at', '')),
        reverse=True
    )


def diversify_products(
    products: List[Dict],
    limit: int,
    max_per_category: int = 4,
    max_per_source: int = 5,
    hardware_ratio: float = 0.4,
    max_per_hw_category: int = 3
) -> List[Dict]:
    """
    多样化选择算法，保证榜单均衡

    参数:
    - limit: 选择数量
    - max_per_category: 每个软件类别最大数量
    - max_per_source: 每个来源最大数量
    - hardware_ratio: 硬件最大占比 (默认 40%)
    - max_per_hw_category: 每个硬件子类别最大数量 (避免全是 drone)
    """
    selected = []
    category_counts = defaultdict(int)
    source_counts = defaultdict(int)
    hw_category_counts = defaultdict(int)
    hw_count = 0
    sw_count = 0

    hw_limit = int(limit * hardware_ratio)
    sw_limit = limit - hw_limit

    def is_hardware(p):
        return p.get('is_hardware') or p.get('category') == 'hardware' or p.get('hardware_category')

    for product in products:
        if len(selected) >= limit:
            break

        # 检查硬件/软件配额
        is_hw = is_hardware(product)
        if is_hw and hw_count >= hw_limit:
            continue
        if not is_hw and sw_count >= sw_limit:
            continue

        # 检查硬件子类别配额 (避免全是 drone/ai_chip)
        if is_hw:
            hw_cat = product.get('hardware_category', 'hardware_other')
            if hw_category_counts[hw_cat] >= max_per_hw_category:
                continue

        # 检查软件类别配额
        categories = product.get('categories') or [product.get('category', 'other')]
        primary = categories[0] if categories else 'other'
        if not is_hw and category_counts[primary] >= max_per_category:
            continue

        # 检查来源配额
        source = product.get('source', 'unknown')
        if source_counts[source] >= max_per_source:
            continue

        # 添加产品
        selected.append(product)
        category_counts[primary] += 1
        source_counts[source] += 1
        if is_hw:
            hw_count += 1
            hw_cat = product.get('hardware_category', 'hardware_other')
            hw_category_counts[hw_cat] += 1
        else:
            sw_count += 1

    # 如果不足，放宽限制再补齐
    for product in products:
        if len(selected) >= limit:
            break
        if product in selected:
            continue
        selected.append(product)

    return selected


def get_effective_date(product: Dict[str, Any]) -> Optional[datetime]:
    """获取产品的有效日期 (考虑 news_updated_at 重置计时器)"""
    # 如果有 news_updated_at, 使用较新的日期
    news_date = parse_date(product.get('news_updated_at'))
    discovered_date = get_product_date(product)

    if news_date and discovered_date:
        return max(news_date, discovered_date)
    return news_date or discovered_date


def product_score_key(product: Dict[str, Any]) -> tuple:
    """计算产品排名分数 (评分 > 融资)"""
    return (
        product.get('dark_horse_index', 0),
        parse_funding(product.get('funding_total', ''))
    )
