#!/usr/bin/env python3
"""
搜索 Prompt 模块

职责：优化搜索查询，获取更精准的 AI 产品融资新闻

设计原则：
1. 搜索查询要具体、有时效性
2. 包含融资信号词 (funding, Series A, raised, 融资, 获投)
3. 排除噪音源 (工具目录、教程、旧新闻)
4. 按地区优化语言和关键词
"""

from datetime import datetime
from typing import Optional

# ═══════════════════════════════════════════════════════════════════════════════
# 搜索查询生成器 (用于 Perplexity Search API 的 query 参数)
# ═══════════════════════════════════════════════════════════════════════════════

def get_current_year() -> int:
    return datetime.now().year


def get_current_month() -> str:
    return datetime.now().strftime("%Y-%m")


# ─────────────────────────────────────────────────────────────────────────────
# 核心关键词库
# ─────────────────────────────────────────────────────────────────────────────

# 融资信号词 (必须包含至少一个)
FUNDING_SIGNALS = {
    "en": ["funding", "raised", "Series A", "Series B", "seed round", "valuation", "unicorn", "investment"],
    "zh": ["融资", "获投", "估值", "A轮", "B轮", "种子轮", "独角兽", "领投"],
    "ja": ["資金調達", "シリーズA", "評価額", "投資"],
    "ko": ["투자", "시리즈A", "평가액", "유니콘"],
}

# 时效性词 (确保获取最新新闻)
RECENCY_SIGNALS = {
    "en": [f"{get_current_year()}", "latest", "recent", "announces", "launches"],
    "zh": [f"{get_current_year()}", "最新", "刚刚", "宣布", "完成"],
    "ja": [f"{get_current_year()}", "最新", "発表"],
    "ko": [f"{get_current_year()}", "최신", "발표"],
}

# 排除词 (过滤噪音)
EXCLUDE_TERMS = {
    "en": ["-tutorial", "-guide", "-how to", "-best tools", "-list of"],
    "zh": ["-教程", "-指南", "-工具合集", "-盘点"],
}


# ─────────────────────────────────────────────────────────────────────────────
# 地区搜索查询模板
# ─────────────────────────────────────────────────────────────────────────────

SEARCH_QUERIES_BY_REGION = {
    "us": {
        "name": "🇺🇸 美国",
        "language": "en",
        "queries": [
            # 通用融资查询
            "AI startup funding {year} raised Series A B",
            "artificial intelligence company investment {year}",
            "AI unicorn startup valuation {year}",
            # YC/顶级 VC 定向
            "YC AI startup demo day {year}",
            "a]z Sequoia AI investment {year}",
            # 品类定向
            "AI coding assistant startup funding",
            "AI agent company raised {year}",
            "generative AI startup Series A {year}",
        ],
        "site_searches": [
            "site:techcrunch.com AI startup funding {year}",
            "site:venturebeat.com AI raises",
            "site:producthunt.com AI launch {month}",
            "site:news.ycombinator.com AI startup",
        ],
    },
    
    "cn": {
        "name": "🇨🇳 中国",
        "language": "zh",
        "queries": [
            # 通用融资查询
            "AI创业公司 融资 {year}",
            "人工智能 初创公司 A轮 B轮 {year}",
            "AIGC 融资 获投 {year}",
            "大模型 创业公司 估值 {year}",
            # 品类定向
            "AI Agent 融资 {year}",
            "AI编程 创业公司 融资",
            "具身智能 机器人 融资 {year}",
        ],
        "site_searches": [
            "site:36kr.com AI融资 {year}",
            "site:tmtpost.com 人工智能 融资",
            "site:jiqizhixin.com 融资",
            "site:itjuzi.com AI",
        ],
    },
    
    "eu": {
        "name": "🇪🇺 欧洲",
        "language": "en",
        "queries": [
            "European AI startup funding {year}",
            "UK AI company Series A {year}",
            "France Germany AI startup raised {year}",
            "Europe artificial intelligence investment {year}",
        ],
        "site_searches": [
            "site:sifted.eu AI funding {year}",
            "site:tech.eu AI startup raises",
            "site:eu-startups.com AI {year}",
        ],
    },
    
    "jp": {
        "name": "🇯🇵 日本",
        "language": "ja",
        "queries": [
            "AI スタートアップ 資金調達 {year}",
            "人工知能 企業 シリーズA {year}",
            "Japan AI startup funding {year}",
            "日本 AI 創業 投資 {year}",
        ],
        "site_searches": [
            "site:thebridge.jp AI startup",
            "site:jp.techcrunch.com AI 資金調達",
        ],
    },
    
    "kr": {
        "name": "🇰🇷 韩国",
        "language": "ko",
        "queries": [
            "AI 스타트업 투자 {year}",
            "한국 인공지능 기업 시리즈A",
            "Korean AI startup funding {year}",
            "Korea AI company investment {year}",
        ],
        "site_searches": [
            "site:platum.kr AI 스타트업",
            "site:besuccess.com AI funding",
        ],
    },
    
    "sea": {
        "name": "🇸🇬 东南亚",
        "language": "en",
        "queries": [
            "Singapore AI startup funding {year}",
            "Southeast Asia AI company raised {year}",
            "Indonesia Vietnam AI startup investment",
            "ASEAN artificial intelligence funding {year}",
        ],
        "site_searches": [
            "site:e27.co AI startup funding",
            "site:techinasia.com AI raises {year}",
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 搜索查询生成函数
# ─────────────────────────────────────────────────────────────────────────────

def generate_search_queries(
    region: str,
    query_type: str = "general",
    limit: int = 5,
    include_sites: bool = True
) -> list[str]:
    """
    生成优化的搜索查询列表
    
    Args:
        region: 地区代码 (us/cn/eu/jp/kr/sea)
        query_type: 查询类型 (general/sites/mixed)
        limit: 返回查询数量
        include_sites: 是否包含站点定向搜索
        
    Returns:
        优化后的搜索查询列表
    """
    config = SEARCH_QUERIES_BY_REGION.get(region, SEARCH_QUERIES_BY_REGION["us"])
    year = get_current_year()
    month = get_current_month()
    
    queries = []
    
    # 替换模板变量
    def fill_template(q: str) -> str:
        return q.format(year=year, month=month)
    
    if query_type == "general" or query_type == "mixed":
        queries.extend([fill_template(q) for q in config["queries"]])
    
    if (query_type == "sites" or query_type == "mixed") and include_sites:
        queries.extend([fill_template(q) for q in config.get("site_searches", [])])
    
    # 随机打乱并限制数量
    import random
    random.shuffle(queries)
    return queries[:limit]


def generate_discovery_query(
    region: str,
    category: Optional[str] = None,
    funding_stage: Optional[str] = None
) -> str:
    """
    生成单个精准的发现查询
    
    Args:
        region: 地区代码
        category: 产品类别 (coding/image/video/agent 等)
        funding_stage: 融资阶段 (seed/A/B/unicorn)
        
    Returns:
        优化后的搜索查询
    """
    config = SEARCH_QUERIES_BY_REGION.get(region, SEARCH_QUERIES_BY_REGION["us"])
    lang = config["language"]
    year = get_current_year()
    
    # 基础查询
    if lang == "zh":
        base = f"AI 创业公司 融资 {year}"
    else:
        base = f"AI startup funding {year}"
    
    # 添加类别
    category_terms = {
        "coding": {"en": "coding assistant developer tools", "zh": "编程 代码 开发工具"},
        "image": {"en": "image generation visual AI", "zh": "图像生成 视觉AI"},
        "video": {"en": "video generation AI", "zh": "视频生成 AI"},
        "agent": {"en": "AI agent autonomous", "zh": "AI Agent 智能体"},
        "voice": {"en": "voice AI speech synthesis", "zh": "语音 AI 语音合成"},
        "hardware": {"en": "AI chip hardware", "zh": "AI芯片 硬件"},
    }
    
    if category and category in category_terms:
        base = f"{category_terms[category].get(lang, category_terms[category]['en'])} {base}"
    
    # 添加融资阶段
    stage_terms = {
        "seed": {"en": "seed round", "zh": "种子轮"},
        "A": {"en": "Series A", "zh": "A轮"},
        "B": {"en": "Series B", "zh": "B轮"},
        "unicorn": {"en": "unicorn valuation $1B", "zh": "独角兽 估值"},
    }
    
    if funding_stage and funding_stage in stage_terms:
        base = f"{base} {stage_terms[funding_stage].get(lang, stage_terms[funding_stage]['en'])}"
    
    return base


# ─────────────────────────────────────────────────────────────────────────────
# Perplexity Search API 参数优化
# ─────────────────────────────────────────────────────────────────────────────

def get_search_params(region: str, recency: str = "week") -> dict:
    """
    获取地区优化的 Perplexity Search API 参数
    
    Perplexity Search API 参数说明:
    - country: ISO 国家代码 (US/CN/GB/DE/JP/KR/SG 等)
    - search_language_filter: 语言过滤 (最多 10 个 ISO 639-1 代码)
    - search_domain_filter: 域名过滤 (最多 20 个，"-" 前缀表示排除)
    - search_recency_filter: 时效性 (day/week/month/year)
    - max_results: 结果数量 (1-20)
    - max_tokens_per_page: 每页内容 token 数
    - max_tokens: 总内容 token 数 (最大 1,000,000)
    
    Args:
        region: 地区代码 (us/cn/eu/jp/kr/sea)
        recency: 时效性过滤 (day/week/month/year)
        
    Returns:
        API 参数字典
    """
    region_params = {
        "us": {
            "country": "US",
            "search_language_filter": ["en"],
            "search_domain_filter": [
                "-pinterest.com",
                "-quora.com",
                "-reddit.com",  # 排除社交媒体噪音
            ],
        },
        "cn": {
            "country": "CN",
            "search_language_filter": ["zh"],
            "search_domain_filter": [
                "-zhihu.com",  # 排除问答
                "-csdn.net",   # 排除技术博客
                "-jianshu.com",
            ],
        },
        "eu": {
            "country": "GB",  # 默认英国
            "search_language_filter": ["en", "de", "fr"],
        },
        "jp": {
            "country": "JP",
            "search_language_filter": ["ja", "en"],
        },
        "kr": {
            "country": "KR",
            "search_language_filter": ["ko", "en"],
        },
        "sea": {
            "country": "SG",
            "search_language_filter": ["en"],
        },
    }
    
    params = region_params.get(region, region_params["us"])
    
    # 通用参数
    params["max_results"] = 10
    params["max_tokens_per_page"] = 2048
    params["max_tokens"] = 25000
    
    # 时效性过滤 (确保获取最新新闻)
    if recency in ["day", "week", "month", "year"]:
        params["search_recency_filter"] = recency
    
    return params


def get_funding_search_params(region: str) -> dict:
    """
    获取针对融资新闻优化的搜索参数
    
    特点:
    - 只搜索最近一周的内容
    - 限定到可信媒体源
    - 排除社交媒体和问答网站
    """
    params = get_search_params(region, recency="week")
    
    # 针对融资新闻的优化域名过滤
    funding_sources = {
        "us": [
            "techcrunch.com",
            "venturebeat.com",
            "bloomberg.com",
            "forbes.com",
            "businessinsider.com",
        ],
        "cn": [
            "36kr.com",
            "tmtpost.com",
            "jiqizhixin.com",
            "itjuzi.com",
        ],
        "eu": [
            "sifted.eu",
            "tech.eu",
            "eu-startups.com",
        ],
        "jp": [
            "thebridge.jp",
            "techcrunch.jp",
        ],
        "kr": [
            "platum.kr",
        ],
        "sea": [
            "e27.co",
            "techinasia.com",
        ],
    }
    
    # 如果有特定地区的可信源，添加域名白名单模式
    # 注意: Perplexity API 不支持同时白名单和黑名单
    # 这里我们保留黑名单模式，只排除噪音源
    
    return params


# ─────────────────────────────────────────────────────────────────────────────
# 导出
# ─────────────────────────────────────────────────────────────────────────────

__all__ = [
    "SEARCH_QUERIES_BY_REGION",
    "generate_search_queries",
    "generate_discovery_query",
    "get_search_params",
    "FUNDING_SIGNALS",
    "RECENCY_SIGNALS",
]
