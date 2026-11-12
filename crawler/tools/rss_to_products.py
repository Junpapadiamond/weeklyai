#!/usr/bin/env python3
"""
RSS 新闻 → 产品数据转换模块

流程:
1. 读取 RSS 新闻文章 (blogs_news.json)
2. 筛选包含产品/融资信息的文章
3. 用 LLM 提取产品信息
4. 评估是否符合黑马标准
5. 输出到候选池 (candidates/)

使用:
    python tools/rss_to_products.py                    # 处理所有新闻
    python tools/rss_to_products.py --limit 10         # 只处理 10 篇
    python tools/rss_to_products.py --dry-run          # 测试模式
    python tools/rss_to_products.py --source TechCrunch # 指定来源
"""

import json
import os
import sys
import re
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Set, Tuple
import argparse
from urllib.parse import urlparse

from dotenv import load_dotenv

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
from utils.product_identity import is_shared_host, product_identity_key

REPO_ROOT = os.path.dirname(PROJECT_ROOT)
load_dotenv(os.path.join(REPO_ROOT, '.env'))
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# ============================================
# 配置
# ============================================

DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
BLOGS_NEWS_FILE = os.path.join(DATA_DIR, 'blogs_news.json')
CANDIDATES_DIR = os.path.join(DATA_DIR, 'candidates')
PRODUCTS_FEATURED_FILE = os.path.join(DATA_DIR, 'products_featured.json')
INDUSTRY_LEADERS_FILE = os.path.join(DATA_DIR, 'industry_leaders.json')
PENDING_REVIEW_FILE = os.path.join(CANDIDATES_DIR, 'pending_review.json')
DEFAULT_CACHE_FILE = os.path.join(CANDIDATES_DIR, 'rss_to_products_cache.json')

# 确保目录存在
os.makedirs(CANDIDATES_DIR, exist_ok=True)

def safe_load_json(path: str, default):
    if not path or not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def safe_save_json(path: str, payload) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def normalize_domain(url: str) -> str:
    if not url:
        return ""
    if is_shared_host(url):
        return product_identity_key(url)
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")) and "." in url:
        url = f"https://{url}"
    try:
        parsed = urlparse(url)
    except Exception:
        return url.lower()
    host = (parsed.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host or url.lower()


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def normalize_name_key(value: str) -> str:
    """Strict normalized name key used for safe featured enrich fallback."""
    key = normalize_name(value)
    return key if len(key) >= 4 else ""


_INDUSTRY_LEADERS_CACHE: Optional[Tuple[Set[str], Set[str]]] = None


def load_industry_leader_index() -> Tuple[Set[str], Set[str]]:
    """
    Load industry leader products (name + domain) for exclusion.

    Source: crawler/data/industry_leaders.json
    """
    global _INDUSTRY_LEADERS_CACHE
    if _INDUSTRY_LEADERS_CACHE is not None:
        return _INDUSTRY_LEADERS_CACHE

    data = safe_load_json(INDUSTRY_LEADERS_FILE, {}) or {}
    names: Set[str] = set()
    domains: Set[str] = set()

    try:
        categories = (data.get("categories") or {}) if isinstance(data, dict) else {}
        if isinstance(categories, dict):
            for cat in categories.values():
                products = (cat or {}).get("products") if isinstance(cat, dict) else None
                if not isinstance(products, list):
                    continue
                for p in products:
                    if not isinstance(p, dict):
                        continue
                    n = normalize_name(p.get("name", ""))
                    if n:
                        names.add(n)
                    d = normalize_domain(p.get("website", ""))
                    if d:
                        domains.add(d)
    except Exception:
        # Best-effort; on error treat as empty.
        names = set()
        domains = set()

    _INDUSTRY_LEADERS_CACHE = (names, domains)
    return _INDUSTRY_LEADERS_CACHE


def is_industry_leader(name: str, website: str) -> bool:
    """Return True if the product matches an industry leader by normalized name or website domain."""
    names, domains = load_industry_leader_index()
    name_norm = normalize_name(name)
    if name_norm and name_norm in names:
        return True
    domain = normalize_domain(website)
    if domain and domain in domains:
        return True
    return False


def to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def parse_date(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        cleaned = value.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned).astimezone(timezone.utc)
    except Exception:
        pass
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def normalize_article(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize different news/blog schemas into a single article shape."""
    extra = raw.get("extra") or {}
    if not isinstance(extra, dict):
        extra = {}

    title = (raw.get("title") or raw.get("name") or "").strip()
    summary = (raw.get("summary") or raw.get("description") or raw.get("snippet") or "").strip()
    link = (raw.get("link") or raw.get("website") or raw.get("source_url") or "").strip()
    source = (raw.get("source") or "").strip()

    published_at = (
        raw.get("published_at")
        or raw.get("published")
        or raw.get("first_seen")
        or raw.get("discovered_at")
        or ""
    )

    return {
        "title": title,
        "summary": summary,
        "link": link,
        "source": source,
        "published_at": published_at,
        "extra": extra,
        "has_product_mention": bool(raw.get("has_product_mention")),
    }


def article_key(article: Dict[str, Any]) -> str:
    link = (article.get("link") or "").strip()
    if link:
        return link
    return f"{article.get('source', '')}:{normalize_name(article.get('title', ''))}"


def build_signal(article: Dict[str, Any]) -> Dict[str, Any]:
    source = (article.get("source") or "").lower().strip()
    title = (article.get("title") or "").strip()
    link = (article.get("link") or "").strip()
    summary = (article.get("summary") or "").strip()
    published_at = (article.get("published_at") or "").strip()
    extra = article.get("extra") or {}
    if not isinstance(extra, dict):
        extra = {}

    author = ""
    if source == "youtube":
        author = (extra.get("channel") or extra.get("author") or "").strip()
    elif source == "x":
        handle = (extra.get("author_handle") or extra.get("author") or "").strip()
        if handle and not handle.startswith("@"):
            handle = f"@{handle}"
        author = handle

    signal = {
        "platform": source,
        "url": link,
        "title": title[:140],
        "published_at": published_at[:40],
        "snippet": summary[:280],
        "author": author[:80],
    }
    return {k: v for k, v in signal.items() if v}

# 产品提及关键词 (用于初筛)
PRODUCT_KEYWORDS = [
    # 融资相关
    "raises", "raised", "funding", "Series A", "Series B", "Series C", "seed round",
    "valuation", "unicorn", "investment", "投资", "融资", "估值", "A轮", "B轮",
    # 产品发布
    "launches", "launched", "announces", "announced", "releases", "released",
    "introduces", "unveiled", "发布", "推出", "上线",
    # 公司动态
    "startup", "founded", "founded by", "创业", "创始人",
    # 排除词 (大公司动态)
    # "OpenAI", "Google", "Microsoft", "Meta", "Apple", "Amazon",
]

# 大公司名单 (硬编码，用于后处理检测)
BIG_COMPANY_KEYWORDS = {
    # 公司名 -> 显示名
    "openai": "OpenAI",
    "chatgpt": "OpenAI",
    "gpt-": "OpenAI",
    "dall-e": "OpenAI",
    "sora": "OpenAI",
    "google": "Google",
    "gemini": "Google",
    "deepmind": "Google",
    "veo": "Google",
    "imagen": "Google",
    "google flow": "Google",  # Google Labs Flow (精确匹配避免误判)
    "anthropic": "Anthropic",
    "claude": "Anthropic",
    "microsoft": "Microsoft",
    "copilot": "Microsoft",
    "meta": "Meta",
    "llama": "Meta",
    "apple": "Apple",
    "amazon": "Amazon",
    "alexa": "Amazon",
    "nvidia": "Nvidia",
    "tesla": "Tesla",
    "alibaba": "Alibaba",
    "qwen": "Alibaba",
    "tencent": "Tencent",
    "baidu": "Baidu",
    "ernie": "Baidu",
    "bytedance": "ByteDance",
    "doubao": "ByteDance",
}

# 排除大公司及其产品 (Focus: 黑马创业公司)
EXCLUDE_BIG_COMPANY_PRODUCTS = True  # 设为 False 可收录大公司产品

# 纯公司名排除
EXCLUDE_TERMS = {
    "openai", "google", "microsoft", "meta", "apple", "amazon", 
    "nvidia", "anthropic", "alibaba", "tencent", "baidu", "bytedance",
}

# ============================================
# LLM 客户端
# ============================================

def get_llm_client():
    """获取 LLM 客户端 (Perplexity)"""
    perplexity_key = os.getenv('PERPLEXITY_API_KEY')
    if not perplexity_key:
        return (None, None)
    try:
        from utils.perplexity_client import PerplexityClient
        client = PerplexityClient(api_key=perplexity_key)
        if client.is_available():
            return ("perplexity", client)
    except Exception as e:
        print(f"  ⚠️ Perplexity 初始化失败: {e}")
    return (None, None)


# ============================================
# 产品提取 Prompt
# ============================================

EXTRACTION_PROMPT = """分析以下新闻文章，提取其中提到的 AI 产品或创业公司信息。

文章标题: {title}
文章来源: {source}
文章内容: {content}

请提取以下信息（如果文章中没有提到具体产品/公司，返回空 JSON）：

{{
  "has_product": true/false,  // 是否包含可收录的产品信息
  "products": [
    {{
      "name": "产品/公司名称",
      "website": "官网 URL (如果文章提到)",
      "description": "一句话产品描述 (50字以内)",
      "category": "类别: coding/image/video/voice/writing/agent/hardware/finance/education/healthcare/other",
      "is_hardware": false,  // 是否是硬件产品
      "hardware_category": "",  // 如果是硬件: ai_chip/robotics/smart_glasses/wearables/drone/edge_ai
      "funding_total": "融资金额 (如 $50M, $1.2B)",
      "funding_stage": "融资阶段 (Seed/Series A/B/C)",
      "founded_date": "成立年份",
      "region": "地区: 🇺🇸/🇨🇳/🇪🇺/🇯🇵/🇰🇷/🇸🇬",
      "why_matters": "为什么值得关注 (一句话，要具体，包含数据)",
      "dark_horse_score": 1-5,  // 黑马评分
      "score_reason": "评分理由"
    }}
  ]
}}

【重要】我们的核心目标是发现「黑马」和「潜力新人」：
- **优先提取创业公司** - 融资新闻、新产品发布、快速增长的小公司
- **大公司产品次要** - 只有非常创新的新产品才值得收录

评分标准:
- 5分: 创业公司融资>$100M / 品类开创者 / 增长异常快
- 4分: 创业公司融资>$30M / ARR>$10M / 顶级VC背书
- 3分: 融资$1M-$30M / ProductHunt上榜 / 有明显增长
- 2分: 刚发布/数据不足 但有创新点
- 1分: 信息不足 / 普通产品
- 大公司新产品: 非常创新可给4-5分，普通更新1-2分

注意:
1. 只提取明确的产品/公司，不要猜测
2. 纯公司名不算产品 (如 "OpenAI" 不是产品，但 "ChatGPT Health" 是产品)
3. why_matters 必须具体：优先使用原文中出现的数字/事实；如果原文没有数字，写清楚差异化/信号点，但不要编造数字
4. 如果文章只是行业分析/观点，has_product 设为 false
5. 如果来源是 YouTube / X：忽略赞助商、广告、折扣码等推广内容，只提取主内容真正介绍的产品

只返回 JSON，不要其他内容。"""


# ============================================
# LLM 调用
# ============================================

def extract_products_with_llm(article: Dict, llm_type: str, llm_client: Any) -> List[Dict]:
    """使用 LLM 从文章中提取产品信息"""
    
    title = article.get('title', '')
    source = article.get('source', '')
    content = article.get('summary', '')

    if (source or "").lower().strip() in {"youtube", "x"}:
        content = clean_social_content(content)
        if len(content) < 60:
            return []
    
    prompt = EXTRACTION_PROMPT.format(
        title=title,
        source=source,
        content=content
    )
    
    try:
        if llm_type != "perplexity":
            return []

        response = llm_client.analyze(prompt=prompt)
        # analyze 返回解析后的 JSON 或字符串
        if isinstance(response, dict):
            result_text = json.dumps(response)
        elif isinstance(response, list):
            result_text = json.dumps({"has_product": True, "products": response})
        else:
            result_text = str(response)
        
        # 解析 JSON
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            result = json.loads(json_match.group())
            if result.get('has_product') and result.get('products'):
                return result['products']
        
        return []
    
    except Exception as e:
        print(f"    ❌ LLM 调用失败: {e}")
        return []


# ============================================
# 产品验证和标准化
# ============================================

def clean_social_content(content: str) -> str:
    """Remove common sponsor/boilerplate lines from social snippets (YouTube/X)."""
    if not content:
        return ""

    blocked = re.compile(
        r"(sponsor|sponsors|check\\s+out|sign\\s+up|patreon|discount|promo\\s+code|affiliate|"
        r"subscribe|newsletter|merch|giveaway|support\\s+us|use\\s+code)",
        re.IGNORECASE,
    )

    text = str(content)

    # Common YouTube pattern: sponsor blurb then "📝 ..." with real context.
    marker_idx = text.find("📝")
    if marker_idx != -1:
        prefix = text[:marker_idx]
        if blocked.search(prefix):
            text = text[marker_idx:]

    lines = [ln.strip() for ln in text.splitlines() if ln and ln.strip()]
    kept = [ln for ln in lines if not blocked.search(ln)]
    if not kept:
        return ""
    cleaned = " ".join(kept)

    # Strip URLs to reduce chance of extracting sponsors/track links.
    cleaned = re.sub(r"https?://\\S+", "", cleaned)
    cleaned = re.sub(r"\\s+", " ", cleaned).strip()
    return cleaned

def search_website(name: str, category: str, llm_client: Any) -> str:
    """搜索产品官网"""
    if not llm_client:
        return ""
    
    try:
        query = f"{name} {category} official website"
        results = llm_client.search(query=query, max_results=3)
        
        if results:
            # 优先选择产品官网
            for r in results:
                url = r.url.lower()
                name_clean = name.lower().replace(' ', '').replace('-', '')
                if name_clean[:4] in url or any(domain in url for domain in ['.com', '.ai', '.io']):
                    return r.url
            return results[0].url
        return ""
    except Exception:
        return ""


def validate_product(
    product: Dict,
    article: Dict,
    llm_client: Any = None,
    *,
    featured_index: Optional[Dict[str, Dict[str, Any]]] = None,
    featured_name_index: Optional[Dict[str, Dict[str, Any]]] = None,
    enrich_featured: bool = True,
) -> Optional[Dict]:
    """验证和标准化产品数据"""
    from utils.website_resolver import extract_official_website_from_source, is_placeholder_url
    
    name = product.get('name', '').strip()
    if not name or len(name) < 2:
        return None
    
    # 排除纯公司名 (不是具体产品)
    if name.lower() in EXCLUDE_TERMS:
        return None
    
    # 检查必要字段
    score = product.get('dark_horse_score', 0)
    if score < 2:
        return None  # 评分太低，不收录
    
    why_matters = product.get('why_matters', '')
    if not why_matters or len(why_matters) < 10:
        return None  # 没有说明为什么重要

    description = (product.get("description", "") or "").strip()
    if len(description) < 20:
        return None  # 描述太短，不利于判断

    # why_matters 质量：必须“具体”（数字或明确差异化/背书/里程碑）
    generic_phrases = [
        "很有潜力", "值得关注", "融资情况良好", "团队背景不错", "前景广阔",
        "promising", "worth watching", "interesting", "potential", "good product",
    ]
    why_lower = why_matters.lower()
    if any(p.lower() in why_lower for p in generic_phrases) and len(why_matters) < 60:
        return None

    has_number = bool(re.search(r"[\$¥€]\d+|arr|\d+[mbk万亿]|\d+%|\d{1,3}[,.]?\d{0,3}", why_lower))
    has_specific = any(kw.lower() in why_lower for kw in [
        "领投", "融资", "估值", "用户", "增长", "arr", "首创", "首个",
        "前openai", "前google", "前meta", "yc", "a16z", "sequoia",
        "open source", "开源", "crowdfunding", "众筹", "已发货", "预售", "no subscription", "无订阅",
    ])
    if not has_number and not has_specific:
        return None

    # 获取网站 (优先从 source_url 解析，避免模型猜官网)
    website = (product.get('website', '') or '').strip()
    if website and is_placeholder_url(website):
        website = ""

    article_link = (article.get('link') or '').strip()
    if (not website or website.lower() == "unknown") and article_link:
        resolved = extract_official_website_from_source(article_link, name)
        if resolved:
            website = resolved
            product['website_source'] = "source_url"

    if not website and llm_client:
        website = search_website(name, product.get('category', ''), llm_client)

    if not website or website.lower() == "unknown":
        return None

    # Industry leaders should not enter candidates, but can still be enriched if they already exist in featured.
    domain_key = normalize_domain(website) if website and website.lower() != "unknown" else ""
    name_key = normalize_name_key(name)
    featured_hit = bool(
        enrich_featured and (
            (featured_index and domain_key and domain_key in featured_index)
            or (featured_name_index and name_key and name_key in featured_name_index)
        )
    )
    if (not featured_hit) and is_industry_leader(name, website):
        return None

    # 检测并排除大公司产品 (Focus: 黑马和创业公司)
    name_lower = name.lower()
    website_lower = website.lower() if website else ""
    
    # 检查产品名是否包含大公司关键词
    for keyword in BIG_COMPANY_KEYWORDS.keys():
        if keyword in name_lower:
            return None  # 排除大公司产品
    
    # 检查网站是否属于大公司
    big_company_domains = [
        "openai.com", "anthropic.com", "claude.ai", "claude.com",
        "google.com", "labs.google", "deepmind.google",
        "microsoft.com", "meta.com", "apple.com", "amazon.com",
        "nvidia.com", "alibaba.com", "tencent.com", "baidu.com", "bytedance.com"
    ]
    for domain in big_company_domains:
        if domain in website_lower:
            return None  # 排除大公司产品
    
    is_big_company = False
    parent_company = ""

    dark_index = min(5, max(1, int(score)))
    category = product.get('category', 'other')
    categories = [category] if category else ['other']
    is_hardware = bool(product.get('is_hardware')) or category == 'hardware'
    if is_hardware and 'hardware' not in categories:
        categories.insert(0, 'hardware')

    published_at = (article.get('published_at') or '').strip()
    if not published_at:
        published_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # 标准化数据
    standardized = {
        "name": name,
        "slug": name.lower().replace(' ', '-').replace('.', '-'),
        "website": website,
        "logo_url": "",
        "description": description[:200],
        "category": category,
        "categories": categories,
        "is_hardware": is_hardware,
        "hardware_category": product.get('hardware_category', ''),
        "is_big_company": is_big_company,  # 标记大公司产品
        "parent_company": parent_company,  # 母公司名称
        "funding_total": product.get('funding_total', ''),
        "funding_stage": product.get('funding_stage', ''),
        "founded_date": product.get('founded_date', ''),
        "region": product.get('region', '🇺🇸'),
        "dark_horse_index": dark_index,
        "why_matters": why_matters[:300],
        "criteria_met": [product.get('score_reason', '')],
        "discovered_at": datetime.now().strftime('%Y-%m-%d'),
        "source": article.get('source', ''),
        "source_url": article_link,
        "source_title": article.get('title', ''),
        "published_at": published_at,
        "first_seen": to_iso(datetime.now(timezone.utc)),
        "final_score": dark_index * 20,
        "trending_score": dark_index * 18,
        "hot_score": dark_index * 20,
        "top_score": dark_index * 20,
    }

    if product.get('website_source'):
        standardized['website_source'] = product['website_source']

    return standardized


def is_duplicate(product: Dict, existing_products: List[Dict]) -> bool:
    """检查产品是否重复"""
    name = product.get('name', '').lower().replace(' ', '')
    website = product.get('website', '').lower()
    
    for existing in existing_products:
        existing_name = existing.get('name', '').lower().replace(' ', '')
        existing_website = existing.get('website', '').lower()
        
        if name == existing_name:
            return True
        if website and existing_website and website in existing_website:
            return True
    
    return False


# ============================================
# 主流程
# ============================================

def load_existing_products() -> List[Dict]:
    """加载已有产品 (用于去重)"""
    featured = safe_load_json(PRODUCTS_FEATURED_FILE, []) or []
    pending = safe_load_json(PENDING_REVIEW_FILE, []) or []
    existing: List[Dict[str, Any]] = []
    if isinstance(featured, list):
        existing.extend(featured)
    if isinstance(pending, list):
        existing.extend(pending)
    return existing


def filter_articles(
    articles: List[Dict[str, Any]],
    sources: Optional[Set[str]] = None,
    source_contains: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """筛选包含产品信息的文章（支持 sources 精确过滤 + 关键词初筛）"""
    filtered: List[Dict[str, Any]] = []

    sources_norm = {s.lower().strip() for s in (sources or set()) if s and s.strip()}
    source_contains_norm = (source_contains or "").lower().strip()
    try:
        allowed_year = int(os.getenv("CONTENT_YEAR", str(datetime.now(timezone.utc).year)))
    except Exception:
        allowed_year = datetime.now(timezone.utc).year

    for article in articles:
        src = (article.get("source") or "").lower().strip()

        if sources_norm and src not in sources_norm:
            continue
        if (not sources_norm) and source_contains_norm and source_contains_norm not in src:
            continue

        # Keep only the allowed year (default: current year).
        published_at = (article.get("published_at") or "").strip()
        published_dt = parse_date(published_at)
        if not published_dt or published_dt.year != allowed_year:
            continue

        text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
        has_keyword = any(kw.lower() in text for kw in PRODUCT_KEYWORDS)

        # Social signals (youtube/x) are already pre-filtered by spiders; keep them even if keyword misses.
        if has_keyword or article.get("has_product_mention") or src in {"youtube", "x"}:
            filtered.append(article)

    return filtered


def load_processed_cache(cache_file: str) -> Set[str]:
    data = safe_load_json(cache_file, [])
    if isinstance(data, list):
        return {str(x) for x in data if str(x)}
    return set()


def save_processed_cache(cache_file: str, keys: Set[str]) -> None:
    safe_save_json(cache_file, sorted(keys))


def build_featured_index(featured: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for p in featured:
        domain = normalize_domain(p.get("website", ""))
        if domain and domain not in index:
            index[domain] = p
    return index


def build_featured_name_index(featured: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for p in featured:
        key = normalize_name_key(p.get("name", ""))
        if key and key not in index:
            index[key] = p
    return index


def _bump_score_fields(product: Dict[str, Any], delta: int = 2, cap: int = 100) -> None:
    for field in ("trending_score", "hot_score", "final_score", "top_score"):
        try:
            value = int(product.get(field) or 0)
        except Exception:
            continue
        if value <= 0:
            continue
        product[field] = min(cap, value + delta)


def add_signal_to_product(product: Dict[str, Any], signal: Dict[str, Any], max_items: int = 5) -> bool:
    extra = product.get("extra") or {}
    if not isinstance(extra, dict):
        extra = {}

    signals = extra.get("signals") or []
    if not isinstance(signals, list):
        signals = []

    url = (signal.get("url") or "").strip()
    if url and any((s or {}).get("url") == url for s in signals if isinstance(s, dict)):
        return False

    signals.insert(0, signal)
    extra["signals"] = signals[:max_items]
    product["extra"] = extra
    return True


def enrich_featured_product(featured_product: Dict[str, Any], signal: Dict[str, Any], extracted: Dict[str, Any]) -> bool:
    changed = add_signal_to_product(featured_product, signal, max_items=5)
    if not changed:
        return False

    platform = (signal.get("platform") or "").lower()
    platform_label = "YouTube" if platform == "youtube" else ("X" if platform == "x" else platform.upper())

    # Update latest_news (no link)
    published_at = signal.get("published_at") or ""
    date_prefix = published_at[:10] if published_at else datetime.now().strftime("%Y-%m-%d")
    one_liner = (
        (extracted.get("why_matters") or "").strip() or
        (extracted.get("description") or "").strip() or
        (signal.get("title") or "").strip()
    )
    if len(one_liner) > 120:
        one_liner = one_liner[:117] + "..."

    featured_product["latest_news"] = f"{date_prefix}: 来自 {platform_label} 的一手提及：{one_liner}"

    # This drives dark horse freshness via backend product_sorting.get_effective_date()
    featured_product["news_updated_at"] = published_at or to_iso(datetime.now(timezone.utc))

    # Optional: small ranking bump (cap 100)
    _bump_score_fields(featured_product, delta=2, cap=100)
    return True


def merge_pending_candidates(existing: List[Dict[str, Any]], new_items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    by_key = {}
    for p in existing:
        key = normalize_name(p.get("name", "")) or normalize_domain(p.get("website", ""))
        if key and key not in by_key:
            by_key[key] = p

    added = 0
    for p in new_items:
        key = normalize_name(p.get("name", "")) or normalize_domain(p.get("website", ""))
        if not key or key in by_key:
            continue
        by_key[key] = p
        existing.append(p)
        added += 1

    existing.sort(key=lambda x: x.get("final_score", x.get("trending_score", 0)), reverse=True)
    return existing, added


def process_articles(
    articles: List[Dict[str, Any]],
    llm_type: str,
    llm_client: Any,
    existing_products: List[Dict[str, Any]],
    featured_index: Dict[str, Dict[str, Any]],
    featured_name_index: Optional[Dict[str, Dict[str, Any]]] = None,
    enrich_featured: bool = True,
    processed_cache: Optional[Set[str]] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """处理文章，提取产品 → enrich featured 或写入候选池"""
    new_candidates: List[Dict[str, Any]] = []
    enriched_count = 0
    processed_count = 0
    skipped_cache = 0

    for i, article in enumerate(articles):
        key = article_key(article)
        if processed_cache is not None and key in processed_cache:
            skipped_cache += 1
            continue

        title = (article.get("title") or "")[:80]
        source = article.get("source", "")

        print(f"\n[{processed_count + 1}/{len(articles)}] {source}")
        print(f"  📰 {title}...")
        processed_count += 1

        products = extract_products_with_llm(article, llm_type, llm_client)
        if not products:
            print("  ⏭️ 无产品信息")
            if processed_cache is not None:
                processed_cache.add(key)
            continue

        signal = build_signal(article)

        for product in products:
            validated = validate_product(
                product,
                article,
                llm_client,
                featured_index=featured_index,
                featured_name_index=featured_name_index,
                enrich_featured=enrich_featured,
            )
            if not validated:
                print(f"  ⏭️ {product.get('name', '?')} - 验证未通过")
                continue

            domain = normalize_domain(validated.get("website", ""))
            target_featured = None
            if enrich_featured and domain and domain in featured_index:
                target_featured = featured_index[domain]
            elif enrich_featured and featured_name_index:
                name_key = normalize_name_key(validated.get("name", ""))
                if name_key and name_key in featured_name_index:
                    target_featured = featured_name_index[name_key]

            if target_featured:
                if dry_run:
                    matched = normalize_domain(target_featured.get("website", "")) or "name-match"
                    print(f"  🧪 [DRY RUN] Enrich featured: {validated.get('name')} ({matched})")
                    enriched_count += 1
                else:
                    if enrich_featured_product(target_featured, signal, validated):
                        enriched_count += 1
                        print(f"  🔗 Enriched featured: {target_featured.get('name')} ← {signal.get('platform')}")
                continue

            if is_duplicate(validated, existing_products + new_candidates):
                print(f"  ⏭️ {validated.get('name', '?')} - 已存在")
                continue

            # Otherwise: save to candidates/pending_review.json for human review
            candidate = dict(validated)
            platform = (signal.get("platform") or "").lower()
            platform_label = "YouTube" if platform == "youtube" else ("X" if platform == "x" else platform)
            candidate["_candidate_reason"] = f"来自 {platform_label} 信号"

            # Attach signal evidence to candidate.extra.signals
            add_signal_to_product(candidate, signal, max_items=5)

            score = candidate.get("dark_horse_index", 0)
            why = (candidate.get("why_matters") or "")[:40]
            print(f"  ✅ Candidate: {candidate.get('name')} ({score}分) - {why}...")
            new_candidates.append(candidate)

        if processed_cache is not None:
            processed_cache.add(key)

        time.sleep(1)

    return {
        "new_candidates": new_candidates,
        "enriched_count": enriched_count,
        "processed_count": processed_count,
        "skipped_cache": skipped_cache,
    }


# ============================================
# CLI
# ============================================

def main():
    parser = argparse.ArgumentParser(description="RSS 新闻 → 产品数据转换")
    parser.add_argument("--limit", type=int, default=50, help="处理文章数量上限")
    parser.add_argument("--source", type=str, help="只处理指定来源的文章 (deprecated; use --sources)")
    parser.add_argument("--sources", type=str, default="", help="只处理指定来源 (逗号分隔，例如 youtube,x)")
    parser.add_argument("--dry-run", action="store_true", help="测试模式，不保存")
    parser.add_argument("--input", type=str, help="输入文件路径")
    parser.add_argument("--cache-file", type=str, default=DEFAULT_CACHE_FILE, help="缓存已处理文章 key 的文件路径")
    parser.add_argument("--enrich-featured", action="store_true", default=True, help="匹配到 featured 产品则写入信号/更新 latest_news")
    parser.add_argument("--no-enrich-featured", action="store_false", dest="enrich_featured", help="禁用 featured enrich")
    
    args = parser.parse_args()
    
    print("🔄 RSS 新闻 → 产品数据转换")
    print("=" * 50)
    
    # 读取新闻
    input_file = args.input or BLOGS_NEWS_FILE
    if not os.path.exists(input_file):
        print(f"❌ 新闻文件不存在: {input_file}")
        print("请先运行: python tools/rss_feeds.py")
        return
    
    with open(input_file, 'r') as f:
        articles = json.load(f)
    
    if not isinstance(articles, list):
        print(f"❌ 输入文件格式错误（期望 JSON 数组）: {input_file}")
        return

    normalized_articles = [normalize_article(a) for a in articles if isinstance(a, dict)]
    print(f"📰 读取 {len(normalized_articles)} 篇新闻")
    
    # 筛选文章
    sources = {s.strip().lower() for s in (args.sources or "").split(",") if s.strip()}
    filtered = filter_articles(normalized_articles, sources=sources or None, source_contains=args.source)
    print(f"🔍 筛选出 {len(filtered)} 篇包含产品信息的文章")
    
    if not filtered:
        print("⚠️ 没有找到包含产品信息的文章")
        return

    processed_cache = load_processed_cache(args.cache_file) if args.cache_file else set()
    if processed_cache:
        before = len(filtered)
        filtered = [a for a in filtered if article_key(a) not in processed_cache]
        skipped = before - len(filtered)
        if skipped:
            print(f"⏭️ 跳过已处理: {skipped} 篇")
    
    # 限制数量
    filtered = filtered[:args.limit]
    
    # 获取 LLM 客户端
    print("\n🤖 初始化 LLM...")
    llm_type, llm_client = get_llm_client()
    
    if not llm_client:
        print("❌ 没有可用的 LLM 客户端")
        print("请配置 PERPLEXITY_API_KEY")
        return
    
    print(f"  ✅ 使用 {llm_type}")
    
    # 加载已有产品
    featured_products = safe_load_json(PRODUCTS_FEATURED_FILE, []) or []
    if not isinstance(featured_products, list):
        featured_products = []
    featured_index = build_featured_index(featured_products)
    featured_name_index = build_featured_name_index(featured_products)

    pending_candidates = safe_load_json(PENDING_REVIEW_FILE, []) or []
    if not isinstance(pending_candidates, list):
        pending_candidates = []

    existing = featured_products + pending_candidates
    print(f"📦 Featured: {len(featured_products)} | Pending: {len(pending_candidates)}")
    
    # 处理文章
    print(f"\n🔄 开始处理 {len(filtered)} 篇文章...")
    result = process_articles(
        filtered,
        llm_type,
        llm_client,
        existing,
        featured_index=featured_index,
        featured_name_index=featured_name_index,
        enrich_featured=args.enrich_featured,
        processed_cache=processed_cache,
        dry_run=args.dry_run,
    )

    new_candidates = result.get("new_candidates") or []
    enriched_count = int(result.get("enriched_count") or 0)
    processed_count = int(result.get("processed_count") or 0)

    if not args.dry_run:
        if args.enrich_featured and enriched_count > 0:
            safe_save_json(PRODUCTS_FEATURED_FILE, featured_products)
            print(f"\n✅ 已更新 featured: +{enriched_count} 条信号 (latest_news/news_updated_at)")

        if new_candidates:
            pending_candidates, added = merge_pending_candidates(pending_candidates, new_candidates)
            if added:
                safe_save_json(PENDING_REVIEW_FILE, pending_candidates)
            print(f"\n✅ 已写入候选池: +{added} 个 → candidates/pending_review.json")

        if args.cache_file:
            save_processed_cache(args.cache_file, processed_cache)
    
    # 统计
    print("\n📊 统计:")
    print(f"  - 处理文章: {processed_count}")
    print(f"  - enrich featured: {enriched_count}")
    print(f"  - 新候选: {len(new_candidates)}")

    if new_candidates:
        scores = [p.get('dark_horse_index', 0) for p in new_candidates]
        print(f"  - 5分产品: {scores.count(5)}")
        print(f"  - 4分产品: {scores.count(4)}")
        print(f"  - 3分产品: {scores.count(3)}")
        print(f"  - 2分产品: {scores.count(2)}")


if __name__ == "__main__":
    main()
