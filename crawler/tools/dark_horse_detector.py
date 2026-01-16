"""
自动黑马检测器
根据多维度信号自动计算 dark_horse_index (1-5)
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional


def parse_funding_amount(text: str) -> Optional[float]:
    """从文本中提取融资金额（单位：百万美元）

    支持格式:
    - $10M, $10 million
    - $1B, $1 billion
    - $23M Series A
    - 融资 2300万美元
    """
    if not text:
        return None

    text = str(text)

    # 匹配 $XXM 或 $XX million
    patterns = [
        r'\$(\d+(?:\.\d+)?)\s*[Bb](?:illion)?',  # $1B -> 1000M
        r'\$(\d+(?:\.\d+)?)\s*[Mm](?:illion)?',  # $10M -> 10M
        r'\$(\d+(?:\.\d+)?)\s*[Kk]',              # $500K -> 0.5M
    ]

    for i, pattern in enumerate(patterns):
        match = re.search(pattern, text)
        if match:
            amount = float(match.group(1))
            if i == 0:  # billion
                amount *= 1000
            elif i == 2:  # K
                amount /= 1000
            return amount

    return None


def is_recent_product(product: Dict[str, Any], days: int = 30) -> bool:
    """检查产品是否是最近N天内的新产品"""
    date_fields = ['first_seen', 'published_at', 'discovered_at']

    for field in date_fields:
        date_str = product.get(field) or product.get('extra', {}).get(field)
        if not date_str:
            continue

        try:
            if isinstance(date_str, str):
                # ISO 格式
                if 'T' in date_str:
                    parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00').split('+')[0])
                else:
                    parsed = datetime.strptime(date_str[:10], '%Y-%m-%d')

                age_days = (datetime.utcnow() - parsed).days
                return age_days <= days
        except (ValueError, TypeError):
            continue

    return False


def has_positive_growth(product: Dict[str, Any]) -> bool:
    """检查产品是否有正向增长"""
    extra = product.get('extra', {}) or {}
    metrics_delta = extra.get('metrics_delta', {}) or {}

    if not metrics_delta:
        return False

    growth_keys = ['stars', 'votes', 'likes', 'downloads', 'weekly_users', 'points', 'comments']
    positive_sum = sum(max(0, metrics_delta.get(k, 0)) for k in growth_keys)

    return positive_sum > 0


def calculate_dark_horse_index(product: Dict[str, Any]) -> int:
    """计算单个产品的黑马指数 (0-5)

    评分规则:
    +2  融资 >= $10M
    +1  融资 >= $1M (且 < $10M)
    +1  treasure_score >= 60
    +1  30天内新产品
    +1  有正向增长 (metrics_delta > 0)
    +1  优质来源加成 (ProductHunt/YC/TechCrunch)

    返回: 0-5 的整数
    """
    score = 0
    extra = product.get('extra', {}) or {}

    # === 1. 融资信号 (最高 +2) ===
    funding_text = (
        product.get('funding_total', '') or
        extra.get('funding_total', '') or
        str(extra.get('funding_amount', '')) or
        product.get('description', '')
    )

    funding_amount = parse_funding_amount(funding_text)

    # 如果 extra 里有数字形式的 funding_amount，直接用
    if not funding_amount and extra.get('funding_amount'):
        try:
            funding_amount = float(extra['funding_amount'])
        except (ValueError, TypeError):
            pass

    if funding_amount:
        if funding_amount >= 10:  # >= $10M
            score += 2
        elif funding_amount >= 1:  # >= $1M
            score += 1

    # === 2. 宝藏分数信号 ===
    treasure_score = product.get('treasure_score', 0) or 0
    if treasure_score >= 60:
        score += 1

    # === 3. 新鲜度信号 ===
    if is_recent_product(product, days=30):
        score += 1

    # === 4. 增长信号 ===
    if has_positive_growth(product):
        score += 1

    # === 5. 来源信号 ===
    source = product.get('source', '').lower()
    premium_sources = {
        'producthunt': 1,
        'techcrunch': 1,
        'ycombinator': 1,
        'yc': 1,
        'exhibition': 1,  # 展会产品
        'curated': 1,     # 手动策展
    }
    if source in premium_sources:
        score += premium_sources[source]

    # === 6. 融资新闻特殊加成 ===
    if extra.get('is_funding_news'):
        score += 1

    # 限制在 0-5 范围
    return min(5, max(0, score))


def detect_dark_horses(products: List[Dict[str, Any]],
                       min_index: int = 3,
                       apply_to_all: bool = True) -> List[Dict[str, Any]]:
    """批量检测黑马产品

    Args:
        products: 产品列表
        min_index: 最低黑马指数阈值（用于筛选返回）
        apply_to_all: 是否为所有产品计算 dark_horse_index

    Returns:
        如果 apply_to_all=True: 返回添加了 dark_horse_index 的完整列表
        如果 apply_to_all=False: 只返回黑马产品（index >= min_index）
    """
    dark_horses = []

    for product in products:
        # 如果已有手动设置的 dark_horse_index，跳过
        if product.get('dark_horse_index') and product.get('source') == 'curated':
            if apply_to_all:
                dark_horses.append(product)
            elif product.get('dark_horse_index', 0) >= min_index:
                dark_horses.append(product)
            continue

        # 自动计算
        index = calculate_dark_horse_index(product)
        product['dark_horse_index'] = index

        if apply_to_all:
            dark_horses.append(product)
        elif index >= min_index:
            dark_horses.append(product)

    return dark_horses


def get_top_dark_horses(products: List[Dict[str, Any]],
                        limit: int = 10,
                        min_index: int = 3) -> List[Dict[str, Any]]:
    """获取 Top N 黑马产品

    Args:
        products: 产品列表
        limit: 返回数量
        min_index: 最低黑马指数

    Returns:
        按 dark_horse_index 降序排列的产品列表
    """
    # 确保所有产品都有 dark_horse_index
    detect_dark_horses(products, apply_to_all=True)

    # 筛选并排序
    dark_horses = [p for p in products if p.get('dark_horse_index', 0) >= min_index]

    dark_horses.sort(
        key=lambda x: (
            x.get('dark_horse_index', 0),
            x.get('treasure_score', 0),
            x.get('final_score', x.get('trending_score', 0))
        ),
        reverse=True
    )

    return dark_horses[:limit]


# === 测试 ===
if __name__ == '__main__':
    # 测试用例
    test_products = [
        {
            'name': 'TestStartup',
            'description': 'AI startup raises $15M Series A',
            'source': 'techcrunch',
            'extra': {'funding_amount': 15, 'is_funding_news': True},
            'treasure_score': 65,
            'first_seen': datetime.utcnow().isoformat()
        },
        {
            'name': 'OldProduct',
            'description': 'Some old AI tool',
            'source': 'aitools',
            'treasure_score': 30,
            'first_seen': '2024-01-01'
        },
        {
            'name': 'YCStartup',
            'funding_total': '$2M Seed',
            'source': 'ycombinator',
            'treasure_score': 55,
            'first_seen': datetime.utcnow().isoformat()
        }
    ]

    print("测试黑马检测器:")
    print("-" * 50)

    for p in test_products:
        index = calculate_dark_horse_index(p)
        print(f"{p['name']}: dark_horse_index = {index}")

    print("\nTop 黑马产品:")
    top = get_top_dark_horses(test_products, limit=5, min_index=2)
    for i, p in enumerate(top, 1):
        print(f"  {i}. {p['name']} (index={p['dark_horse_index']})")
