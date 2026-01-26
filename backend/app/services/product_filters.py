"""
产品过滤器 - 负责过滤和验证逻辑
"""

from typing import List, Dict, Any, Optional

# 被屏蔽的来源和域名
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
NEW_FEATURE_KEYWORDS = {
    '发布', '推出', '更新', '新版', '新功能',
    'launch', 'release', 'new feature', 'update',
    'v2', 'v3', 'v4', 'announces', '宣布'
}


def build_product_key(product: Dict[str, Any]) -> str:
    """Normalize a product key for dedupe/merge."""
    website = (product.get('website') or '').strip().lower()
    if website:
        return website
    name_key = (product.get('name') or '').strip().lower()
    return ''.join(ch for ch in name_key if ch.isalnum())


def is_blocked(product: Dict[str, Any]) -> bool:
    """Filter non-end-user sources/domains."""
    source = (product.get('source') or '').strip().lower()
    if source in BLOCKED_SOURCES:
        return True
    website = (product.get('website') or '').strip().lower()
    return any(domain in website for domain in BLOCKED_DOMAINS)


def is_well_known(product: Dict[str, Any]) -> bool:
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


def is_hardware(product: Dict[str, Any]) -> bool:
    """判断产品是否为硬件"""
    if product.get('is_hardware'):
        return True
    categories = product.get('categories') or []
    if isinstance(categories, str):
        categories = [categories]
    if 'hardware' in categories:
        return True
    if product.get('category') == 'hardware':
        return True
    if product.get('hardware_category'):
        return True
    return False


def normalize_products(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize products and drop blocked sources/domains + well-known products."""
    normalized = []
    for idx, product in enumerate(products):
        if not product or is_blocked(product) or is_well_known(product):
            continue
        if not product.get('logo_url'):
            logo = product.get('logo') or product.get('logoUrl')
            if logo:
                product['logo_url'] = logo
        if '_id' not in product:
            product['_id'] = str(idx + 1)
        normalized.append(product)
    return normalized


def filter_by_keyword(products: List[Dict], keyword: str) -> List[Dict]:
    """按关键词筛选产品"""
    if not keyword:
        return products
    keyword_lower = keyword.lower()
    return [
        p for p in products
        if keyword_lower in p.get('name', '').lower()
        or keyword_lower in p.get('description', '').lower()
    ]


def filter_by_categories(products: List[Dict], categories: List[str]) -> List[Dict]:
    """按分类筛选（支持多选，OR逻辑）"""
    if not categories:
        return products
    return [
        p for p in products
        if any(cat in p.get('categories', []) for cat in categories)
    ]


def filter_by_type(products: List[Dict], product_type: str) -> List[Dict]:
    """按类型筛选 (software/hardware/all)"""
    if product_type == 'software':
        return [p for p in products if not p.get('is_hardware', False)]
    elif product_type == 'hardware':
        return [p for p in products if p.get('is_hardware', False)]
    return products


def filter_by_dark_horse_index(products: List[Dict], min_index: int = 2, max_index: int = None) -> List[Dict]:
    """按黑马指数筛选"""
    if max_index is not None:
        return [
            p for p in products
            if min_index <= p.get('dark_horse_index', 0) <= max_index
        ]
    return [
        p for p in products
        if p.get('dark_horse_index', 0) >= min_index
    ]


def filter_by_source(products: List[Dict], source: str) -> List[Dict]:
    """按来源筛选"""
    return [
        p for p in products
        if p.get('source', '') == source
    ]


def filter_by_category(products: List[Dict], category: str) -> List[Dict]:
    """按单个分类筛选"""
    return [
        p for p in products
        if category in p.get('categories', [])
    ]
