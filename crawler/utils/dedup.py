#!/usr/bin/env python3
"""
增强的产品去重模块

支持多维度去重：
1. 域名去重（处理 www、子域名、短链接）
2. 名称相似度去重（模糊匹配）
3. 公司名/产品名映射
4. 别名系统
"""

import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse


# ═══════════════════════════════════════════════════════════════════════════════
# 已知别名/变体映射
# ═══════════════════════════════════════════════════════════════════════════════

# 公司名 -> 规范名
COMPANY_ALIASES = {
    # Humane
    "humane": "humane",
    "humane ai": "humane",
    "humane ai pin": "humane",
    "humane ai pin 2": "humane",
    "hu.ma.ne": "humane",
    
    # Limitless
    "limitless": "limitless",
    "limitless ai": "limitless",
    "limitless pendant": "limitless",
    "rewind ai": "limitless",  # 改名了
    
    # Thinking Machines
    "thinking machines": "thinking-machines",
    "thinkingmachines": "thinking-machines",
    "thinking machines lab": "thinking-machines",
    "thinkingmachineslab": "thinking-machines",
    
    # Mistral
    "mistral": "mistral",
    "mistral ai": "mistral",
    
    # xAI
    "xai": "xai",
    "x.ai": "xai",
    "x ai": "xai",
    
    # Anthropic
    "anthropic": "anthropic",
    "claude": "anthropic",
    
    # OpenAI
    "openai": "openai",
    "open ai": "openai",
    "chatgpt": "openai",
}

# 域名 -> 规范域名
DOMAIN_ALIASES = {
    # Humane
    "humane.com": "humane.com",
    "hu.ma.ne": "humane.com",
    
    # Limitless
    "limitless.ai": "limitless.ai",
    "rewind.ai": "limitless.ai",
    
    # Thinking Machines
    "thinkingmachines.ai": "thinkingmachines.ai",
    "thinkingmachineslab.com": "thinkingmachines.ai",
    
    # xAI
    "x.ai": "x.ai",
    "xai.com": "x.ai",
}


# ═══════════════════════════════════════════════════════════════════════════════
# 域名规范化
# ═══════════════════════════════════════════════════════════════════════════════

def normalize_domain(url: str, include_path: bool = False) -> str:
    """
    规范化域名，用于去重
    
    处理：
    - 移除 www.
    - 移除协议
    - 转小写
    - 处理已知别名
    
    Args:
        url: URL 字符串
        include_path: 是否包含路径（用于区分同一域名的不同产品）
    
    示例：
    - "https://www.example.com/page" → "example.com" (include_path=False)
    - "https://www.example.com/page" → "example.com/page" (include_path=True)
    - "hu.ma.ne" → "humane.com"
    """
    if not url:
        return ""
    
    try:
        # 添加协议（如果没有）
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # 移除 www.
        domain = re.sub(r'^www\.', '', domain)
        
        # 移除端口
        domain = domain.split(':')[0]
        
        # 检查别名
        if domain in DOMAIN_ALIASES:
            domain = DOMAIN_ALIASES[domain]
        
        # 是否包含路径
        if include_path and parsed.path and parsed.path != '/':
            path = parsed.path.rstrip('/')
            return f"{domain}{path}"
        
        return domain
    except Exception:
        return url.lower().strip()


def get_domain_key(url: str) -> str:
    """
    获取用于去重的域名 key
    
    规则：
    - 如果 URL 有子路径，返回 domain/path（区分同一公司的不同产品）
    - 如果 URL 只是根域名，返回 domain
    
    示例：
    - "https://thinkingmachines.ai" → "thinkingmachines.ai"
    - "https://thinkingmachines.ai/tinker/" → "thinkingmachines.ai/tinker"
    """
    if not url:
        return ""
    
    try:
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        
        parsed = urlparse(url)
        domain = normalize_domain(url, include_path=False)
        path = parsed.path.strip('/')
        
        # 如果有有意义的路径，包含它
        if path and not path.startswith(('?', '#')) and len(path) > 0:
            # 只取第一级路径
            first_path = path.split('/')[0]
            if first_path and len(first_path) > 1:  # 避免单字符路径
                return f"{domain}/{first_path}"
        
        return domain
    except Exception:
        return normalize_domain(url, include_path=False)


def extract_base_domain(domain: str) -> str:
    """
    提取基础域名（不含子域名）
    
    "api.example.com" → "example.com"
    "www.sub.example.co.uk" → "example.co.uk"
    """
    if not domain:
        return ""
    
    # 常见的二级域名后缀
    multi_part_tlds = {
        'co.uk', 'com.cn', 'com.au', 'co.jp', 'co.kr',
        'com.br', 'com.mx', 'co.in', 'com.hk'
    }
    
    parts = domain.split('.')
    
    # 检查是否是多部分 TLD
    if len(parts) >= 3:
        last_two = '.'.join(parts[-2:])
        if last_two in multi_part_tlds:
            return '.'.join(parts[-3:])
    
    # 返回最后两部分
    if len(parts) >= 2:
        return '.'.join(parts[-2:])
    
    return domain


# ═══════════════════════════════════════════════════════════════════════════════
# 名称规范化
# ═══════════════════════════════════════════════════════════════════════════════

def normalize_name(name: str) -> str:
    """
    规范化产品/公司名称
    
    处理：
    - 转小写
    - 移除特殊字符
    - 移除常见后缀（AI, Inc, Labs 等）
    - 处理已知别名
    """
    if not name:
        return ""
    
    # 转小写
    name = name.lower().strip()
    
    # 检查别名
    if name in COMPANY_ALIASES:
        return COMPANY_ALIASES[name]
    
    # 移除常见后缀
    suffixes = [
        r'\s*\(.*\)$',  # (xxx)
        r'\s*-\s*ai$',
        r'\s+ai$',
        r'\s+inc\.?$',
        r'\s+labs?$',
        r'\s+corp\.?$',
        r'\s+ltd\.?$',
        r'\s+llc\.?$',
        r'\s+gmbh$',
        r'\s+co\.?$',
    ]
    
    for suffix in suffixes:
        name = re.sub(suffix, '', name, flags=re.IGNORECASE)
    
    # 移除特殊字符，保留字母数字空格
    name = re.sub(r'[^\w\s]', '', name)
    
    # 压缩空格
    name = ' '.join(name.split())
    
    return name


def name_similarity(name1: str, name2: str) -> float:
    """
    计算两个名称的相似度
    
    返回 0.0 - 1.0 之间的值
    """
    if not name1 or not name2:
        return 0.0
    
    # 先规范化
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)
    
    # 完全相同
    if n1 == n2:
        return 1.0
    
    # 使用 SequenceMatcher
    return SequenceMatcher(None, n1, n2).ratio()


# ═══════════════════════════════════════════════════════════════════════════════
# 去重检查器
# ═══════════════════════════════════════════════════════════════════════════════

class DuplicateChecker:
    """
    产品去重检查器
    
    使用多种策略检查重复：
    1. 域名 + 路径检查（区分同一公司的不同产品）
    2. 精确名称匹配
    3. 规范化名称匹配
    4. 名称相似度 + 类别匹配（可选，避免误伤）
    """
    
    def __init__(
        self,
        existing_products: List[Dict],
        similarity_threshold: float = 0.90,  # 提高到 90% 避免误伤
        check_similarity: bool = True
    ):
        """
        初始化检查器
        
        Args:
            existing_products: 已有产品列表
            similarity_threshold: 名称相似度阈值（0.90 = 90% 相似）
            check_similarity: 是否检查相似度
        """
        self.similarity_threshold = similarity_threshold
        self.check_similarity = check_similarity
        
        # 构建索引
        self.domain_keys: Set[str] = set()  # domain/path 形式
        self.names: Set[str] = set()
        self.normalized_names: Set[str] = set()
        self.products_by_name: Dict[str, Dict] = {}  # 用于相似度检查时比较类别
        
        for product in existing_products:
            self._add_to_index(product)
    
    def _add_to_index(self, product: Dict):
        """添加产品到索引"""
        # 域名 key（包含路径）
        website = product.get('website', '')
        if website:
            website_lower = website.lower().strip()
            if website_lower in {"unknown", "n/a", "na", "none"}:
                website = ""
        if website:
            domain_key = get_domain_key(website)
            if domain_key:
                self.domain_keys.add(domain_key)
        
        # 名称
        name = product.get('name', '')
        if name:
            name_lower = name.lower().strip()
            self.names.add(name_lower)
            self.products_by_name[name_lower] = product
            
            normalized = normalize_name(name)
            if normalized:
                self.normalized_names.add(normalized)
    
    def is_duplicate(self, product: Dict) -> Tuple[bool, Optional[str]]:
        """
        检查产品是否重复
        
        Returns:
            (是否重复, 重复原因)
        """
        name = product.get('name', '')
        website = product.get('website', '')
        category = product.get('category', '')
        
        # 1. 域名 + 路径检查
        if website:
            website_lower = website.lower().strip()
            if website_lower in {"unknown", "n/a", "na", "none"}:
                website = ""
        if website:
            domain_key = get_domain_key(website)
            if domain_key and domain_key in self.domain_keys:
                return True, f"域名重复: {domain_key}"
        
        # 2. 精确名称检查
        if name:
            name_lower = name.lower().strip()
            if name_lower in self.names:
                return True, f"名称精确重复: {name}"
            
            # 规范化名称检查
            normalized = normalize_name(name)
            if normalized and normalized in self.normalized_names:
                return True, f"规范化名称重复: {normalized}"
            
            # 3. 相似度检查（仅当类别相同时）
            if self.check_similarity:
                for existing_name, existing_product in self.products_by_name.items():
                    sim = name_similarity(name, existing_name)
                    if sim >= self.similarity_threshold:
                        # 额外检查：类别是否相同
                        existing_category = existing_product.get('category', '')
                        if category and existing_category and category == existing_category:
                            return True, f"名称相似 ({sim:.0%}): {name} ≈ {existing_name}"
        
        return False, None
    
    def add_product(self, product: Dict):
        """添加新产品到索引（用于批量处理时更新）"""
        self._add_to_index(product)


# ═══════════════════════════════════════════════════════════════════════════════
# 数据清理工具
# ═══════════════════════════════════════════════════════════════════════════════

def deduplicate_products(
    products: List[Dict],
    similarity_threshold: float = 0.90,
    keep: str = "best"
) -> Tuple[List[Dict], List[Dict]]:
    """
    对产品列表去重
    
    Args:
        products: 产品列表
        similarity_threshold: 相似度阈值
        keep: "first" 保留第一个，"best" 保留评分最高的
        
    Returns:
        (去重后的列表, 被移除的重复项)
    """
    if not products:
        return [], []
    
    unique = []
    duplicates = []
    checker = DuplicateChecker([], similarity_threshold, check_similarity=True)
    
    # 如果 keep="best"，先按评分排序（高分优先）
    if keep == "best":
        products = sorted(
            products,
            key=lambda p: (
                p.get('dark_horse_index', 0),
                _funding_to_number(p.get('funding_total', '')),
                p.get('discovered_at', ''),
            ),
            reverse=True
        )
    
    for product in products:
        is_dup, reason = checker.is_duplicate(product)
        if is_dup:
            product['_duplicate_reason'] = reason
            duplicates.append(product)
        else:
            unique.append(product)
            checker.add_product(product)
    
    return unique, duplicates


def _funding_to_number(funding_str: str) -> float:
    """
    将融资字符串转换为数字用于排序
    
    "$500M" → 500000000
    "$1.5B" → 1500000000
    """
    if not funding_str:
        return 0
    
    funding_str = funding_str.upper().replace(',', '').replace('$', '')
    
    multipliers = {
        'B': 1_000_000_000,
        'M': 1_000_000,
        'K': 1_000,
    }
    
    for suffix, mult in multipliers.items():
        if suffix in funding_str:
            try:
                num = float(funding_str.replace(suffix, '').strip())
                return num * mult
            except ValueError:
                return 0
    
    try:
        return float(funding_str)
    except ValueError:
        return 0


def generate_slug(name: str) -> str:
    """
    从名称生成 slug
    
    "Thinking Machines Lab" → "thinking-machines-lab"
    """
    if not name:
        return ""
    
    # 转小写
    slug = name.lower()
    
    # 替换特殊字符为连字符
    slug = re.sub(r'[^\w\s-]', '', slug)
    
    # 空格转连字符
    slug = re.sub(r'[\s_]+', '-', slug)
    
    # 移除多余连字符
    slug = re.sub(r'-+', '-', slug)
    
    # 移除首尾连字符
    slug = slug.strip('-')
    
    return slug


def fix_missing_fields(products: List[Dict]) -> List[Dict]:
    """
    修复缺失字段
    
    - 生成缺失的 slug
    - 尝试从名称推断 website
    """
    for product in products:
        # 修复 slug
        if not product.get('slug'):
            name = product.get('name', '')
            if name:
                product['slug'] = generate_slug(name)
        
        # 标记空 website
        if not product.get('website'):
            product['_missing_website'] = True
    
    return products


# ═══════════════════════════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import json
    import sys
    
    # 测试
    print("=== 去重模块测试 ===\n")
    
    # 测试域名规范化
    test_urls = [
        "https://www.example.com/page",
        "hu.ma.ne",
        "https://thinkingmachines.ai",
        "http://api.sub.example.co.uk/path",
    ]
    
    print("域名规范化测试:")
    for url in test_urls:
        print(f"  {url} → {normalize_domain(url)}")
    
    # 测试名称规范化
    test_names = [
        "Humane AI Pin 2",
        "Limitless AI",
        "Thinking Machines Lab",
        "Example Inc.",
        "Test (AI Company)",
    ]
    
    print("\n名称规范化测试:")
    for name in test_names:
        print(f"  {name} → {normalize_name(name)}")
    
    # 测试相似度
    print("\n名称相似度测试:")
    pairs = [
        ("Humane AI Pin", "Humane AI Pin 2"),
        ("Mistral AI", "MilkStraw AI"),
        ("Skild AI", "Shield AI"),
    ]
    for n1, n2 in pairs:
        sim = name_similarity(n1, n2)
        print(f"  {n1} vs {n2}: {sim:.0%}")
