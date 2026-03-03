"""
产品过滤器 - 负责过滤和验证逻辑
"""

import re
from typing import List, Dict, Any, Optional, Iterable
from urllib.parse import urlparse

# 被屏蔽的来源和域名
BLOCKED_SOURCES = {'github', 'huggingface', 'huggingface_spaces'}
BLOCKED_DOMAINS = ('github.com', 'huggingface.co')
UNKNOWN_WEBSITE_VALUES = {'', 'unknown', 'n/a', 'na', 'none', 'null', 'undefined', 'tbd'}

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

BLOG_CN_SOURCES = {'cn_news', 'cn_news_glm'}
BLOG_US_SOURCES = {'hackernews', 'reddit', 'tech_news', 'youtube', 'x', 'producthunt'}

SEARCH_TEXT_FIELDS = (
    'name',
    'description',
    'description_en',
    'why_matters',
    'why_matters_en',
    'latest_news',
    'latest_news_en',
    'category',
    'source_title',
    'search_keyword',
    'slug',
    'hardware_category',
    'hardware_type',
    'use_case',
)
SEARCH_LIST_FIELDS = (
    'categories',
    'innovation_traits',
)
SEARCH_ALIAS_FIELDS = (
    'alias',
    'aliases',
    'aka',
    'tags',
    'keywords',
)

_MULTI_SPACE_RE = re.compile(r'\s+')
_SEARCH_CLEAN_RE = re.compile(r'[^\w\u4e00-\u9fff]+', re.UNICODE)

UNKNOWN_COUNTRY_CODE = 'UNKNOWN'
UNKNOWN_COUNTRY_NAME = 'Unknown'
UNKNOWN_COUNTRY_DISPLAY = 'Unknown'

COUNTRY_CODE_TO_NAME = {
    'US': 'United States',
    'CN': 'China',
    'SG': 'Singapore',
    'JP': 'Japan',
    'KR': 'South Korea',
    'GB': 'United Kingdom',
    'DE': 'Germany',
    'FR': 'France',
    'SE': 'Sweden',
    'CA': 'Canada',
    'IL': 'Israel',
    'BE': 'Belgium',
    'AE': 'United Arab Emirates',
    'NL': 'Netherlands',
    'CH': 'Switzerland',
    'IN': 'India',
}

COUNTRY_CODE_TO_FLAG = {
    'US': '🇺🇸',
    'CN': '🇨🇳',
    'SG': '🇸🇬',
    'JP': '🇯🇵',
    'KR': '🇰🇷',
    'GB': '🇬🇧',
    'DE': '🇩🇪',
    'FR': '🇫🇷',
    'SE': '🇸🇪',
    'CA': '🇨🇦',
    'IL': '🇮🇱',
    'BE': '🇧🇪',
    'AE': '🇦🇪',
    'NL': '🇳🇱',
    'CH': '🇨🇭',
    'IN': '🇮🇳',
}

COUNTRY_NAME_ALIASES = {
    'us': 'US',
    'usa': 'US',
    'united states': 'US',
    'u.s.': 'US',
    'america': 'US',
    '美国': 'US',
    'cn': 'CN',
    'china': 'CN',
    'prc': 'CN',
    '中国': 'CN',
    'sg': 'SG',
    'singapore': 'SG',
    '新加坡': 'SG',
    'jp': 'JP',
    'japan': 'JP',
    '日本': 'JP',
    'kr': 'KR',
    'korea': 'KR',
    'south korea': 'KR',
    '韩国': 'KR',
    'gb': 'GB',
    'uk': 'GB',
    'united kingdom': 'GB',
    'britain': 'GB',
    'england': 'GB',
    '英国': 'GB',
    'de': 'DE',
    'germany': 'DE',
    '德国': 'DE',
    'fr': 'FR',
    'france': 'FR',
    '法国': 'FR',
    'se': 'SE',
    'sweden': 'SE',
    '瑞典': 'SE',
    'ca': 'CA',
    'canada': 'CA',
    '加拿大': 'CA',
    'il': 'IL',
    'israel': 'IL',
    '以色列': 'IL',
    'be': 'BE',
    'belgium': 'BE',
    '比利时': 'BE',
    'ae': 'AE',
    'uae': 'AE',
    'united arab emirates': 'AE',
    '阿联酋': 'AE',
    'nl': 'NL',
    'netherlands': 'NL',
    '荷兰': 'NL',
    'ch': 'CH',
    'switzerland': 'CH',
    '瑞士': 'CH',
    'in': 'IN',
    'india': 'IN',
    '印度': 'IN',
}

FLAG_TO_COUNTRY_CODE = {flag: code for code, flag in COUNTRY_CODE_TO_FLAG.items()}
DISCOVERY_REGION_FLAGS = {'🇺🇸', '🇨🇳', '🇪🇺', '🇯🇵🇰🇷', '🇸🇬', '🌍'}
REGION_DERIVED_COUNTRY_SOURCES = {'region:search_fallback', 'region:fallback'}

COUNTRY_BY_CC_TLD = {
    'cn': 'CN',
    'jp': 'JP',
    'kr': 'KR',
    'de': 'DE',
    'fr': 'FR',
    'se': 'SE',
    'ca': 'CA',
    'uk': 'GB',
    'sg': 'SG',
    'il': 'IL',
    'be': 'BE',
    'ae': 'AE',
    'nl': 'NL',
    'ch': 'CH',
    'in': 'IN',
}


def _normalize_domain(url: str, include_path: bool = False) -> str:
    """Normalize domain for dedupe (strip scheme/www/port, optionally keep first path)."""
    if not url:
        return ""
    raw = str(url).strip()
    if not raw:
        return ""
    if not re.match(r'^https?://', raw, re.IGNORECASE) and '.' in raw:
        raw = f"https://{raw}"
    try:
        parsed = urlparse(raw)
        domain = (parsed.netloc or '').lower()
        domain = re.sub(r'^www\.', '', domain)
        domain = domain.split(':')[0]
        if not domain:
            return ""
        if include_path:
            path = (parsed.path or '').strip('/')
            if path:
                first = path.split('/')[0]
                if len(first) > 1:
                    return f"{domain}/{first}"
        return domain
    except Exception:
        return raw.lower()


def _normalize_website(value: Any) -> str:
    """Normalize website into absolute HTTP(S) URL, or empty string if unusable."""
    raw = str(value or '').strip()
    if not raw:
        return ''

    lowered = raw.lower()
    if lowered in UNKNOWN_WEBSITE_VALUES:
        return ''

    if not re.match(r'^https?://', raw, re.IGNORECASE):
        if '.' not in raw:
            return ''
        raw = f"https://{raw}"

    return raw


def _has_usable_website(product: Dict[str, Any]) -> bool:
    """Require a valid official website for all product records."""
    normalized = _normalize_website(product.get('website'))
    if not normalized:
        return False

    try:
        parsed = urlparse(normalized)
        host = (parsed.netloc or '').strip().lower()
        host = re.sub(r'^www\.', '', host).split(':')[0]
        if not host or '.' not in host:
            return False
    except Exception:
        return False

    # Keep normalized value to avoid downstream "unknown"/bare-domain regressions.
    product['website'] = normalized
    return True


def _same_or_subdomain(host: str, root: str) -> bool:
    host = (host or '').lower()
    root = (root or '').lower()
    return bool(host and root and (host == root or host.endswith(f".{root}")))


def _sanitize_logo_url(product: Dict[str, Any]) -> None:
    """Drop remote logos that do not belong to the product's official website domain."""
    candidate = (
        product.get('logo_url')
        or product.get('logo')
        or product.get('logoUrl')
        or ''
    )
    logo = str(candidate or '').strip()
    if not logo:
        return

    if logo.startswith('/'):
        product['logo_url'] = logo
        return

    if not re.match(r'^https?://', logo, re.IGNORECASE):
        product['logo_url'] = ''
        return

    website_domain = _normalize_domain(str(product.get('website') or ''), include_path=False)
    if not website_domain:
        product['logo_url'] = ''
        return

    try:
        parsed = urlparse(logo)
        logo_host = (parsed.netloc or '').lower()
        logo_host = re.sub(r'^www\.', '', logo_host).split(':')[0]
    except Exception:
        product['logo_url'] = ''
        return

    if _same_or_subdomain(logo_host, website_domain):
        product['logo_url'] = logo
        return

    # Reject social/media/provider logos as primary logo source.
    product['logo_url'] = ''


def _extract_region_flag(value: Any) -> str:
    text = str(value or '').strip()
    if not text:
        return ''
    match = re.search(r'[\U0001F1E6-\U0001F1FF]{2}', text)
    return match.group(0) if match else ''


def _normalize_country_code(value: Any) -> str:
    text = str(value or '').strip()
    if not text:
        return ''

    upper = text.upper()
    if upper in COUNTRY_CODE_TO_NAME:
        return upper

    flag = _extract_region_flag(text)
    if flag and flag in FLAG_TO_COUNTRY_CODE:
        return FLAG_TO_COUNTRY_CODE[flag]

    normalized = re.sub(r'[_\-.]+', ' ', text.lower()).strip()
    normalized = re.sub(r'\s+', ' ', normalized)
    return COUNTRY_NAME_ALIASES.get(normalized, '')


def _country_code_from_website_tld(website: Any) -> str:
    raw = str(website or '').strip()
    if not raw:
        return ''
    if not re.match(r'^https?://', raw, re.IGNORECASE):
        raw = f'https://{raw}'
    try:
        host = (urlparse(raw).netloc or '').lower().split(':')[0]
        if host.startswith('www.'):
            host = host[4:]
        if not host or '.' not in host:
            return ''
        suffix = host.rsplit('.', 1)[-1]
        return COUNTRY_BY_CC_TLD.get(suffix, '')
    except Exception:
        return ''


def _resolve_company_country(product: Dict[str, Any]) -> tuple[str, str]:
    country_source_hint = str(product.get('country_source') or '').strip().lower()
    skip_region_derived_country_fields = country_source_hint in REGION_DERIVED_COUNTRY_SOURCES

    explicit_fields = [
        'company_country_code',
        'company_country',
        'hq_country_code',
        'hq_country',
        'headquarters_country',
        'origin_country',
        'founder_country',
        'country_code',
        'country_name',
        'country',
        'nationality',
    ]

    for field in explicit_fields:
        if skip_region_derived_country_fields and field in {'country_code', 'country_name', 'country'}:
            # Backward compatibility: old country fields may have been inferred from search region.
            continue
        code = _normalize_country_code(product.get(field))
        if code:
            return code, f'explicit:{field}'

    extra = product.get('extra')
    if isinstance(extra, dict):
        for field in explicit_fields:
            if skip_region_derived_country_fields and field in {'country_code', 'country_name', 'country'}:
                continue
            code = _normalize_country_code(extra.get(field))
            if code:
                return code, f'extra:{field}'

    for field in ('country_flag', 'company_country_flag', 'hq_country_flag'):
        if skip_region_derived_country_fields and field == 'country_flag':
            continue
        code = _normalize_country_code(product.get(field))
        if code:
            return code, f'explicit:{field}'

    source = str(product.get('source') or '').strip().lower()
    region_flag = _extract_region_flag(product.get('region'))
    if source == 'curated' and region_flag:
        code = FLAG_TO_COUNTRY_CODE.get(region_flag, '')
        if code:
            return code, 'curated:region'

    if region_flag and region_flag not in DISCOVERY_REGION_FLAGS:
        code = FLAG_TO_COUNTRY_CODE.get(region_flag, '')
        if code:
            return code, 'region:legacy'

    cc_tld = _country_code_from_website_tld(product.get('website'))
    if cc_tld:
        return cc_tld, 'website:cc_tld'

    return '', 'unknown'


def _normalize_country_fields(product: Dict[str, Any]) -> None:
    source_region = str(product.get('source_region') or '').strip()
    if not source_region:
        existing_region = str(product.get('region') or '').strip()
        if existing_region:
            product['source_region'] = existing_region

    code, country_source = _resolve_company_country(product)
    if code:
        name = COUNTRY_CODE_TO_NAME.get(code, code)
        flag = COUNTRY_CODE_TO_FLAG.get(code, '')
        display = f'{flag} {name}'.strip()
        product['country_code'] = code
        product['country_name'] = name
        product['country_flag'] = flag
        product['country_display'] = display
        product['country_source'] = country_source
        product['region'] = flag or name
        return

    product['country_code'] = UNKNOWN_COUNTRY_CODE
    product['country_name'] = UNKNOWN_COUNTRY_NAME
    product['country_flag'] = ''
    product['country_display'] = UNKNOWN_COUNTRY_DISPLAY
    product['country_source'] = 'unknown'
    product['region'] = UNKNOWN_COUNTRY_DISPLAY


def _get_domain_key(url: str) -> str:
    """Return domain key (domain or domain/first-path) for dedupe."""
    return _normalize_domain(url, include_path=True)


def build_product_key(product: Dict[str, Any]) -> str:
    """Normalize a product key for dedupe/merge."""
    website = product.get('website') or ''
    domain_key = _get_domain_key(website)
    if domain_key:
        return domain_key
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
        if not product:
            continue
        if not _has_usable_website(product):
            continue
        if is_blocked(product) or is_well_known(product):
            continue
        _sanitize_logo_url(product)
        _normalize_country_fields(product)
        if '_id' not in product:
            product['_id'] = str(idx + 1)
        normalized.append(product)
    return normalized


def _normalize_search_text(value: Any) -> str:
    """Normalize free text for fuzzy keyword matching."""
    if value is None:
        return ''
    text = str(value).strip().casefold()
    if not text:
        return ''

    text = text.replace('_', ' ').replace('-', ' ')
    text = re.sub(r'https?://', ' ', text, flags=re.IGNORECASE)
    text = text.replace('www.', ' ')
    text = _SEARCH_CLEAN_RE.sub(' ', text)
    return _MULTI_SPACE_RE.sub(' ', text).strip()


def _normalize_category_token(value: Any) -> str:
    """Normalize category value into a stable token."""
    normalized = _normalize_search_text(value)
    if not normalized:
        return ''
    return normalized.replace(' ', '')


def _flatten_values(value: Any) -> Iterable[str]:
    """Yield string values from scalar/list containers."""
    if value is None:
        return
    if isinstance(value, (list, tuple, set)):
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                yield text
        return

    text = str(value).strip()
    if text:
        yield text


def _collect_search_blobs(product: Dict[str, Any]) -> Dict[str, str]:
    """Collect normalized keyword search text by semantic field groups."""

    def _join_text(values: Iterable[str]) -> str:
        normalized = [_normalize_search_text(v) for v in values]
        normalized = [v for v in normalized if v]
        return ' '.join(normalized)

    name_text = _join_text(_flatten_values(product.get('name')))
    description_text = _join_text([
        *_flatten_values(product.get('description')),
        *_flatten_values(product.get('description_en')),
    ])
    why_text = _join_text([
        *_flatten_values(product.get('why_matters')),
        *_flatten_values(product.get('why_matters_en')),
    ])

    category_values: List[str] = []
    for field in SEARCH_LIST_FIELDS:
        category_values.extend(list(_flatten_values(product.get(field))))
    category_values.extend(list(_flatten_values(product.get('category'))))
    category_text = _join_text(category_values)

    alias_values: List[str] = []
    for field in SEARCH_ALIAS_FIELDS:
        alias_values.extend(list(_flatten_values(product.get(field))))

    extra = product.get('extra')
    if isinstance(extra, dict):
        for field in SEARCH_ALIAS_FIELDS:
            alias_values.extend(list(_flatten_values(extra.get(field))))
    alias_text = _join_text(alias_values)

    meta_values: List[str] = []
    for field in SEARCH_TEXT_FIELDS:
        if field in {'name', 'description', 'description_en', 'why_matters', 'why_matters_en', 'category'}:
            continue
        meta_values.extend(list(_flatten_values(product.get(field))))
    meta_text = _join_text(meta_values)

    website_values: List[str] = []
    website_values.extend(list(_flatten_values(product.get('website'))))
    website_values.extend(list(_flatten_values(product.get('source_url'))))
    parsed_website = str(product.get('website') or '').strip()
    parsed_source_url = str(product.get('source_url') or '').strip()
    if parsed_website:
        website_values.append(_normalize_domain(parsed_website, include_path=False))
    if parsed_source_url:
        website_values.append(_normalize_domain(parsed_source_url, include_path=False))
    website_text = _join_text(website_values)

    combined_text = _join_text([
        name_text,
        description_text,
        why_text,
        category_text,
        alias_text,
        meta_text,
        website_text,
    ])

    return {
        'name': name_text,
        'description': description_text,
        'why_matters': why_text,
        'categories': category_text,
        'aliases': alias_text,
        'meta': meta_text,
        'website': website_text,
        'combined': combined_text,
    }


def compute_keyword_score(product: Dict[str, Any], keyword: str) -> float:
    """Compute keyword relevance score for a product."""
    normalized_keyword = _normalize_search_text(keyword)
    if not normalized_keyword:
        return 0.0

    keyword_tokens = [token for token in normalized_keyword.split(' ') if token]
    if not keyword_tokens:
        return 0.0

    blobs = _collect_search_blobs(product)
    combined_text = blobs['combined']
    if not combined_text:
        return 0.0

    matched_tokens = [token for token in keyword_tokens if token in combined_text]
    if not matched_tokens and normalized_keyword not in combined_text:
        return 0.0

    score = 0.0
    phrase_weights = {
        'name': 16.0,
        'aliases': 13.0,
        'categories': 10.0,
        'meta': 9.0,
        'description': 8.0,
        'why_matters': 7.0,
        'website': 6.0,
    }
    token_weights = {
        'name': 4.2,
        'aliases': 3.5,
        'categories': 2.8,
        'meta': 2.4,
        'description': 2.1,
        'why_matters': 1.8,
        'website': 1.4,
    }

    for field, weight in phrase_weights.items():
        field_text = blobs.get(field, '')
        if field_text and normalized_keyword in field_text:
            score += weight

    unique_tokens = list(dict.fromkeys(keyword_tokens))
    for token in unique_tokens:
        for field, weight in token_weights.items():
            field_text = blobs.get(field, '')
            if field_text and token in field_text:
                score += weight

    # Reward stronger token coverage for multi-word queries.
    coverage = len(set(matched_tokens))
    if len(unique_tokens) > 1:
        score += min(4.0, coverage * 1.15)

    return score


def filter_by_keyword(products: List[Dict], keyword: str) -> List[Dict]:
    """按关键词筛选产品"""
    normalized_keyword = _normalize_search_text(keyword)
    if not normalized_keyword:
        return products

    scored_products = []
    for product in products:
        score = compute_keyword_score(product, normalized_keyword)
        if score > 0:
            scored_products.append((score, product))

    scored_products.sort(key=lambda item: item[0], reverse=True)
    return [product for _, product in scored_products]


def filter_by_categories(products: List[Dict], categories: List[str]) -> List[Dict]:
    """按分类筛选（支持多选，OR逻辑）"""
    if not categories:
        return products

    normalized_target = {
        _normalize_category_token(category)
        for category in categories
        if _normalize_category_token(category)
    }
    if not normalized_target:
        return products

    filtered: List[Dict] = []
    for product in products:
        product_categories: List[str] = []
        product_categories.extend(list(_flatten_values(product.get('categories'))))
        product_categories.extend(list(_flatten_values(product.get('category'))))

        normalized_product_categories = {
            _normalize_category_token(category)
            for category in product_categories
            if _normalize_category_token(category)
        }
        if normalized_target.intersection(normalized_product_categories):
            filtered.append(product)

    return filtered


def filter_by_type(products: List[Dict], product_type: str) -> List[Dict]:
    """按类型筛选 (software/hardware/all)"""
    if product_type == 'software':
        return [p for p in products if not is_hardware(p)]
    elif product_type == 'hardware':
        return [p for p in products if is_hardware(p)]
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
    """按来源筛选（支持来源别名 + URL 域名兜底）"""
    target = (source or '').strip().lower()
    if not target:
        return products

    def _norm(value: Any) -> str:
        return str(value or '').strip().lower()

    def _to_source_type(product: Dict[str, Any]) -> str:
        extra = product.get('extra') or {}
        if isinstance(extra, dict):
            return _norm(extra.get('source_type'))
        return ''

    def _matches_alias(raw_source: str) -> bool:
        if raw_source == target:
            return True
        aliases = {
            'youtube': {'youtube', 'youtube_rss', 'yt'},
            'x': {'x', 'twitter'},
            'reddit': {'reddit'},
        }
        if target in aliases and raw_source in aliases[target]:
            return True
        return False

    def _matches_domain(product: Dict[str, Any]) -> bool:
        website = _norm(product.get('website'))
        source_url = _norm(product.get('source_url'))
        joined = f"{website} {source_url}"

        if target == 'youtube':
            return 'youtube.com' in joined or 'youtu.be' in joined
        if target == 'x':
            return any(domain in joined for domain in ('x.com', 'twitter.com', 'mobile.twitter.com'))
        if target == 'reddit':
            return 'reddit.com' in joined
        return False

    filtered: List[Dict] = []
    for product in products:
        raw_source = _norm(product.get('source'))
        source_type = _to_source_type(product)
        if _matches_alias(raw_source) or _matches_alias(source_type) or _matches_domain(product):
            filtered.append(product)

    return filtered


def infer_blog_market(blog: Dict[str, Any]) -> str:
    """Infer blog market label: cn/us/global."""
    source = str(blog.get('source') or '').strip().lower()
    if source in BLOG_CN_SOURCES:
        return 'cn'
    if source in BLOG_US_SOURCES:
        return 'us'

    extra = blog.get('extra')
    if isinstance(extra, dict):
        explicit = str(extra.get('news_market') or '').strip().lower()
        if explicit in {'cn', 'us', 'global', 'hybrid'}:
            return 'global' if explicit == 'hybrid' else explicit

    explicit_market = str(blog.get('market') or '').strip().lower()
    if explicit_market in {'cn', 'us', 'global', 'hybrid'}:
        return 'global' if explicit_market == 'hybrid' else explicit_market

    region = str(blog.get('region') or '').strip().lower()
    if '🇨🇳' in region or '中国' in region or 'cn' in region:
        return 'cn'
    if '🇺🇸' in region or '美国' in region or 'us' in region:
        return 'us'
    return 'global'


def filter_blogs_by_market(blogs: List[Dict], market: str) -> List[Dict]:
    """Filter blog/news by market selector: cn/us/hybrid."""
    target = (market or '').strip().lower()
    if target in {'', 'all', 'hybrid', 'global'}:
        return blogs
    if target not in {'cn', 'us'}:
        return blogs
    return [b for b in blogs if infer_blog_market(b) == target]


def filter_by_category(products: List[Dict], category: str) -> List[Dict]:
    """按单个分类筛选"""
    return [
        p for p in products
        if category in p.get('categories', [])
    ]
