#!/usr/bin/env python3
"""
自动发现全球 AI 产品 (v2.0 - Perplexity Search)

功能：
1. 使用 Perplexity Search API 实时搜索全球 AI 产品
2. 按地区分配搜索任务 (美国40%/中国25%/欧洲15%/日韩10%/东南亚10%)
3. 使用专业 Prompt 提取产品信息并评分
4. 自动分类到黑马(4-5分)/潜力股(2-3分)

用法：
    python tools/auto_discover.py                    # 运行所有地区
    python tools/auto_discover.py --region us       # 只搜索美国
    python tools/auto_discover.py --region cn       # 只搜索中国
    python tools/auto_discover.py --dry-run         # 预览不保存
"""

import json
import os
import sys
import argparse
import re
import requests
import time
from datetime import datetime
from urllib.parse import urlparse
from typing import Any, Dict, Optional, Tuple, List

# 添加父目录到路径（用于导入 utils）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入新的去重模块
try:
    from utils.dedup import DuplicateChecker, get_domain_key, normalize_name
    USE_NEW_DEDUP = True
except ImportError:
    USE_NEW_DEDUP = False
    print("⚠️  新去重模块未加载，使用旧逻辑")

# 加载 .env 文件（如果存在）
try:
    from dotenv import load_dotenv
    # 查找 .env 文件（在 crawler 目录下）
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Loaded .env from {env_path}")
except ImportError:
    pass  # dotenv 未安装，使用系统环境变量

# Perplexity API 配置
PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY', '')
PERPLEXITY_MODEL = os.environ.get('PERPLEXITY_MODEL', 'sonar')  # sonar or sonar-pro

# 智谱 GLM API 配置 (中国区)
ZHIPU_API_KEY = os.environ.get('ZHIPU_API_KEY', '')
GLM_MODEL = os.environ.get('GLM_MODEL', 'glm-4.7')  # 最新: glm-4.7 (200K context, 128K output)
GLM_SEARCH_ENGINE = os.environ.get('GLM_SEARCH_ENGINE', 'search_pro')
USE_GLM_FOR_CN = os.environ.get('USE_GLM_FOR_CN', 'true').lower() == 'true'

# Demand signals (HN + X)
ENABLE_DEMAND_SIGNALS = os.environ.get('ENABLE_DEMAND_SIGNALS', 'true').lower() == 'true'
DEMAND_WINDOW_DAYS = int(os.environ.get('DEMAND_WINDOW_DAYS', '7'))
DEMAND_MAX_PRODUCTS_PER_RUN = int(os.environ.get('DEMAND_MAX_PRODUCTS_PER_RUN', '25'))
DEMAND_OVERRIDE_MODE = os.environ.get('DEMAND_OVERRIDE_MODE', 'medium').strip().lower()
DEMAND_GITHUB_MAX_STAR_PAGES = int(os.environ.get('DEMAND_GITHUB_MAX_STAR_PAGES', '6'))
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
DEFAULT_OFFICIAL_HANDLES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data',
    'product_official_handles.json'
)
PRODUCT_OFFICIAL_HANDLES_FILE = os.environ.get(
    'PRODUCT_OFFICIAL_HANDLES_FILE',
    DEFAULT_OFFICIAL_HANDLES_FILE
)

# Provider routing (动态选择)
PROVIDER_NAME = "perplexity"  # 默认 provider，实际按区域动态选择

# ============================================
# 国家归属解析（公司归属优先）
# ============================================
UNKNOWN_COUNTRY_CODE = "UNKNOWN"
UNKNOWN_COUNTRY_NAME = "Unknown"
UNKNOWN_COUNTRY_DISPLAY = "Unknown"

COUNTRY_CODE_TO_NAME = {
    "US": "United States",
    "CN": "China",
    "SG": "Singapore",
    "JP": "Japan",
    "KR": "South Korea",
    "GB": "United Kingdom",
    "DE": "Germany",
    "FR": "France",
    "SE": "Sweden",
    "CA": "Canada",
    "IL": "Israel",
    "BE": "Belgium",
    "AE": "United Arab Emirates",
    "NL": "Netherlands",
    "CH": "Switzerland",
    "IN": "India",
}

COUNTRY_CODE_TO_FLAG = {
    "US": "🇺🇸",
    "CN": "🇨🇳",
    "SG": "🇸🇬",
    "JP": "🇯🇵",
    "KR": "🇰🇷",
    "GB": "🇬🇧",
    "DE": "🇩🇪",
    "FR": "🇫🇷",
    "SE": "🇸🇪",
    "CA": "🇨🇦",
    "IL": "🇮🇱",
    "BE": "🇧🇪",
    "AE": "🇦🇪",
    "NL": "🇳🇱",
    "CH": "🇨🇭",
    "IN": "🇮🇳",
}

COUNTRY_NAME_ALIASES = {
    "us": "US",
    "usa": "US",
    "united states": "US",
    "u.s.": "US",
    "america": "US",
    "美国": "US",
    "cn": "CN",
    "china": "CN",
    "prc": "CN",
    "中国": "CN",
    "sg": "SG",
    "singapore": "SG",
    "新加坡": "SG",
    "jp": "JP",
    "japan": "JP",
    "日本": "JP",
    "kr": "KR",
    "korea": "KR",
    "south korea": "KR",
    "韩国": "KR",
    "gb": "GB",
    "uk": "GB",
    "united kingdom": "GB",
    "britain": "GB",
    "england": "GB",
    "英国": "GB",
    "de": "DE",
    "germany": "DE",
    "德国": "DE",
    "fr": "FR",
    "france": "FR",
    "法国": "FR",
    "se": "SE",
    "sweden": "SE",
    "瑞典": "SE",
    "ca": "CA",
    "canada": "CA",
    "加拿大": "CA",
    "il": "IL",
    "israel": "IL",
    "以色列": "IL",
    "be": "BE",
    "belgium": "BE",
    "比利时": "BE",
    "ae": "AE",
    "uae": "AE",
    "united arab emirates": "AE",
    "阿联酋": "AE",
    "nl": "NL",
    "netherlands": "NL",
    "荷兰": "NL",
    "ch": "CH",
    "switzerland": "CH",
    "瑞士": "CH",
    "in": "IN",
    "india": "IN",
    "印度": "IN",
}

FLAG_TO_COUNTRY_CODE = {flag: code for code, flag in COUNTRY_CODE_TO_FLAG.items()}

# 这组 flag 在发现阶段通常代表“搜索市场”，不是公司归属国
DISCOVERY_REGION_FLAGS = {"🇺🇸", "🇨🇳", "🇪🇺", "🇯🇵🇰🇷", "🇸🇬", "🌍"}
REGION_DERIVED_COUNTRY_SOURCES = {"region:search_fallback", "region:fallback"}

COUNTRY_BY_CC_TLD = {
    "cn": "CN",
    "jp": "JP",
    "kr": "KR",
    "de": "DE",
    "fr": "FR",
    "se": "SE",
    "ca": "CA",
    "uk": "GB",
    "sg": "SG",
    "il": "IL",
    "be": "BE",
    "ae": "AE",
    "nl": "NL",
    "ch": "CH",
    "in": "IN",
}


def _extract_region_flag(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    match = re.search(r"[\U0001F1E6-\U0001F1FF]{2}", text)
    return match.group(0) if match else ""


def _normalize_country_code(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""

    upper = text.upper()
    if upper in COUNTRY_CODE_TO_NAME:
        return upper

    flag = _extract_region_flag(text)
    if flag and flag in FLAG_TO_COUNTRY_CODE:
        return FLAG_TO_COUNTRY_CODE[flag]

    normalized = re.sub(r"[_\-.]+", " ", text.lower()).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return COUNTRY_NAME_ALIASES.get(normalized, "")


def _country_code_from_website_tld(website: Any) -> str:
    raw = str(website or "").strip()
    if not raw:
        return ""
    if not raw.startswith(("http://", "https://")):
        raw = f"https://{raw}"

    try:
        host = (urlparse(raw).netloc or "").lower()
        host = host.split(":")[0]
        if host.startswith("www."):
            host = host[4:]
        if not host or "." not in host:
            return ""
        suffix = host.rsplit(".", 1)[-1]
        return COUNTRY_BY_CC_TLD.get(suffix, "")
    except Exception:
        return ""


def resolve_company_country(
    product: Dict[str, Any],
    fallback_region_flag: str = "",
) -> Tuple[str, str]:
    """
    解析产品公司归属国。

    优先级：
    1) 公司/创始相关显式字段
    2) 策展数据的 region（仅 curated，视为人工确认）
    3) 非发现阶段的 legacy region（如 🇩🇪 / 🇫🇷 这类单国旗）
    4) 官网 ccTLD（仅强指向国家）
    5) Unknown
    """
    country_source_hint = str(product.get("country_source") or "").strip().lower()
    skip_region_derived_country_fields = country_source_hint in REGION_DERIVED_COUNTRY_SOURCES

    explicit_fields = [
        "company_country_code",
        "company_country",
        "hq_country_code",
        "hq_country",
        "headquarters_country",
        "origin_country",
        "founder_country",
        "country_code",
        "country_name",
        "country",
        "nationality",
    ]

    for field in explicit_fields:
        if skip_region_derived_country_fields and field in {"country_code", "country_name", "country"}:
            # 兼容历史数据：这些字段可能由旧版 "region:search_fallback" 误推断而来
            continue
        code = _normalize_country_code(product.get(field))
        if code:
            return code, f"explicit:{field}"

    extra = product.get("extra")
    if isinstance(extra, dict):
        for field in explicit_fields:
            if skip_region_derived_country_fields and field in {"country_code", "country_name", "country"}:
                continue
            code = _normalize_country_code(extra.get(field))
            if code:
                return code, f"extra:{field}"

    for field in ("country_flag", "company_country_flag", "hq_country_flag"):
        if skip_region_derived_country_fields and field == "country_flag":
            continue
        code = _normalize_country_code(product.get(field))
        if code:
            return code, f"explicit:{field}"

    source = str(product.get("source") or "").strip().lower()
    region_flag = _extract_region_flag(product.get("region"))
    if source == "curated" and region_flag:
        code = FLAG_TO_COUNTRY_CODE.get(region_flag, "")
        if code:
            return code, "curated:region"

    # 发现阶段的 region 属于“检索市场”信号，默认不直接当公司国家
    if region_flag and region_flag not in DISCOVERY_REGION_FLAGS:
        code = FLAG_TO_COUNTRY_CODE.get(region_flag, "")
        if code:
            return code, "region:legacy"

    if fallback_region_flag and fallback_region_flag not in DISCOVERY_REGION_FLAGS:
        code = FLAG_TO_COUNTRY_CODE.get(fallback_region_flag, "")
        if code:
            return code, "region:fallback"

    cc_tld_code = _country_code_from_website_tld(product.get("website"))
    if cc_tld_code:
        return cc_tld_code, "website:cc_tld"

    return "", "unknown"


def apply_country_fields(product: Dict[str, Any], fallback_region_flag: str = "") -> None:
    """
    为产品写入统一国家字段，并保证未知时不输出错误国旗。
    """
    if fallback_region_flag:
        product["source_region"] = fallback_region_flag
    elif not product.get("source_region"):
        existing_region = str(product.get("region") or "").strip()
        if existing_region:
            product["source_region"] = existing_region

    code, country_source = resolve_company_country(product, fallback_region_flag=fallback_region_flag)
    if code:
        country_name = COUNTRY_CODE_TO_NAME.get(code, code)
        country_flag = COUNTRY_CODE_TO_FLAG.get(code, "")
        country_display = f"{country_flag} {country_name}".strip()
        product["country_code"] = code
        product["country_name"] = country_name
        product["country_flag"] = country_flag
        product["country_display"] = country_display
        product["country_source"] = country_source
        product["region"] = country_flag or country_name
        return

    product["country_code"] = UNKNOWN_COUNTRY_CODE
    product["country_name"] = UNKNOWN_COUNTRY_NAME
    product["country_flag"] = ""
    product["country_display"] = UNKNOWN_COUNTRY_DISPLAY
    product["country_source"] = "unknown"
    product["region"] = UNKNOWN_COUNTRY_DISPLAY


# ============================================
# 每日配额系统
# ============================================
import random

DAILY_QUOTA = {
    "dark_horses": 5,      # 4-5 分黑马产品
    "rising_stars": 10,    # 2-3 分潜力股
}

# 每地区最大产品数（防止单一地区主导）
REGION_MAX = {
    "us": 6, "cn": 4, "eu": 3, "jp": 2, "kr": 2, "sea": 2
}

MAX_ATTEMPTS = 3  # 最大搜索轮数

# GLM 并发/节流配置（中国区）
GLM_KEYWORD_DELAY = float(os.environ.get('GLM_KEYWORD_DELAY', '3'))  # 每个关键词之间的额外等待秒数
MAX_KEYWORDS_CN = int(os.environ.get('AUTO_DISCOVER_MAX_KEYWORDS_CN', '4'))  # 0=不限制
MAX_KEYWORDS_DEFAULT = int(os.environ.get('AUTO_DISCOVER_MAX_KEYWORDS', '0'))  # 0=不限制

# 成本优化配置
AUTO_DISCOVER_BUDGET_MODE = os.environ.get('AUTO_DISCOVER_BUDGET_MODE', 'adaptive').strip().lower()
if AUTO_DISCOVER_BUDGET_MODE not in {'adaptive', 'legacy'}:
    AUTO_DISCOVER_BUDGET_MODE = 'adaptive'
AUTO_DISCOVER_ROUND1_KEYWORDS = max(1, int(os.environ.get('AUTO_DISCOVER_ROUND1_KEYWORDS', '2')))
AUTO_DISCOVER_ROUND_EXPAND_STEP = max(1, int(os.environ.get('AUTO_DISCOVER_ROUND_EXPAND_STEP', '2')))
AUTO_DISCOVER_ENABLE_ANALYZE_GATE = os.environ.get('AUTO_DISCOVER_ENABLE_ANALYZE_GATE', 'true').lower() == 'true'
AUTO_DISCOVER_QUALITY_FALLBACK = os.environ.get('AUTO_DISCOVER_QUALITY_FALLBACK', 'true').lower() == 'true'
AUTO_DISCOVER_PROMPT_MAX_CHARS = max(1200, int(os.environ.get('AUTO_DISCOVER_PROMPT_MAX_CHARS', '6000')))
AUTO_DISCOVER_RESULT_SNIPPET_MAX_CHARS = max(120, int(os.environ.get('AUTO_DISCOVER_RESULT_SNIPPET_MAX_CHARS', '320')))

# ============================================
# 多语言关键词库（原生语言搜索效果更好）
# ============================================

# 软件 AI 关键词
KEYWORDS_SOFTWARE = {
    "us": [
        "AI startup funding 2026",
        "YC AI companies winter 2026",
        "AI Series A 2026",
        "artificial intelligence company raised funding",
        "AI unicorn startup valuation 2026",
        "AI agent startup funding",
        "generative AI startup Series A",
    ],
    "cn": [
        "AI融资 2026",
        "人工智能创业公司",
        "AIGC融资",
        "大模型创业",
        "AI创业公司 A轮 B轮",
        "人工智能 独角兽 估值",
        "AI Agent 创业公司",
    ],
    "eu": [
        "European AI startup funding 2026",
        "KI Startup Finanzierung",
        "AI Series A Europe",
        "UK France Germany AI startup",
    ],
    "jp": [
        "AI スタートアップ 資金調達 2026",
        "日本 AI企業 シリーズA",
        "人工知能 スタートアップ",
        "Japan AI startup funding",
    ],
    "kr": [
        "AI 스타트업 투자 2026",
        "한국 인공지능 기업",
        "AI 시리즈A",
        "Korean AI startup investment",
    ],
    "sea": [
        "Singapore AI startup funding 2026",
        "Southeast Asia AI company",
        "AI startup Indonesia Vietnam",
        "Tech in Asia artificial intelligence",
    ],
}

# 硬件 AI 关键词（专门搜索硬件产品）
# 分为两类：传统硬件（芯片/机器人）+ 创新形态（可穿戴/新形态）
KEYWORDS_HARDWARE = {
    "us": [
        # 传统硬件：芯片/机器人
        "AI chip startup funding 2026",
        "humanoid robot company funding",
        "AI semiconductor startup investment",
        "robotics AI company raised funding",
        # 创新形态硬件：可穿戴/新形态 (Friend Pendant 类)
        "AI pendant necklace wearable 2026",
        "AI companion device startup",
        "AI pin badge wearable assistant",
        "AI ring wearable startup",
        "AI glasses startup 2026",
        "AI wearable gadget viral",
        "AI hardware kickstarter indiegogo 2026",
        "AI assistant device form factor innovative",
        "screenless AI device wearable",
    ],
    "cn": [
        # 传统硬件
        "AI芯片 创业公司 融资",
        "人形机器人 创业公司",
        "具身智能 创业公司",
        # 创新形态硬件
        "AI智能眼镜 创业公司",
        "AI可穿戴设备 创业公司 2026",
        "AI项链 吊坠 智能设备",
        "AI戒指 智能穿戴",
        "AI硬件 众筹 创新",
        "AI随身设备 助手",
    ],
    "eu": [
        "European AI chip startup funding",
        "robotics startup Europe funding",
        # 创新形态
        "AI wearable startup Europe 2026",
        "AI glasses pendant Europe startup",
    ],
    "jp": [
        "AI半導体 スタートアップ 資金調達",
        "ロボット AI企業 日本",
        # 创新形态
        "AIウェアラブル スタートアップ 日本",
        "AIメガネ デバイス 日本",
    ],
    "kr": [
        "AI 반도체 스타트업 투자",
        "로봇 AI 기업 한국",
        # 创新形态
        "AI 웨어러블 스타트업 한국",
    ],
    "sea": [
        "AI hardware startup Singapore",
        "robotics company Southeast Asia",
        # 创新形态
        "AI wearable device startup Asia 2026",
    ],
}

# 兼容旧代码的别名
KEYWORDS_BY_REGION = KEYWORDS_SOFTWARE

# ============================================
# 站点定向搜索（直接搜索目标媒体）
# ============================================
SITE_SEARCHES = {
    "us": [
        # 科技媒体
        "site:techcrunch.com AI startup funding",
        "site:venturebeat.com AI funding",
        "site:wired.com AI hardware device",
        "site:theverge.com AI wearable gadget",
        # 产品发现平台 (创新形态硬件重点)
        "site:producthunt.com AI hardware wearable pendant 2026",
        "site:producthunt.com AI device companion assistant 2026",
        # 众筹平台 (早期创新硬件)
        "site:kickstarter.com AI wearable pendant necklace 2026",
        "site:kickstarter.com AI glasses ring device 2026",
        "site:indiegogo.com AI wearable assistant 2026",
    ],
    "cn": [
        "site:36kr.com AI融资",
        "site:tmtpost.com 人工智能",
        "site:jiqizhixin.com 融资",
        # 硬件创新
        "site:36kr.com AI硬件 可穿戴 智能设备 2026",
        "site:36kr.com 具身智能 人形机器人 2026",
        "site:36kr.com AI眼镜 智能穿戴 2026",
    ],
    "eu": [
        "site:sifted.eu AI funding",
        "site:tech.eu AI startup",
        "site:eu-startups.com AI",
        # 创新硬件
        "site:kickstarter.com AI wearable Europe 2026",
    ],
    "jp": [
        "site:thebridge.jp AI startup",
        "site:jp.techcrunch.com AI",
        # 创新硬件
        "site:kickstarter.com AI wearable Japan 2026",
    ],
    "kr": [
        "site:platum.kr AI 스타트업",
        "site:besuccess.com AI",
    ],
    "sea": [
        "site:e27.co AI startup",
        "site:techinasia.com AI funding",
        "site:kickstarter.com AI wearable Asia 2026",
    ],
}

def get_keywords_for_today(region: str, product_type: str = "mixed") -> list:
    """
    根据日期轮换关键词池
    
    Args:
        region: 地区代码 (us/cn/eu/jp/kr/sea)
        product_type: 产品类型 ("software"/"hardware"/"mixed")

    策略：
    - mixed 模式下硬件:软件 = 40%:60%
    - 每天轮换不同的关键词组合
    """
    day = datetime.now().weekday()

    if product_type == "hardware":
        # 只返回硬件关键词
        keywords = KEYWORDS_HARDWARE.get(region, KEYWORDS_HARDWARE["us"])
    elif product_type == "software":
        # 只返回软件关键词
        keywords = KEYWORDS_SOFTWARE.get(region, KEYWORDS_SOFTWARE["us"])
    else:
        # mixed 模式：40% 硬件 + 60% 软件
        hw_keywords = KEYWORDS_HARDWARE.get(region, KEYWORDS_HARDWARE["us"])
        sw_keywords = KEYWORDS_SOFTWARE.get(region, KEYWORDS_SOFTWARE["us"])
        site_searches = SITE_SEARCHES.get(region, [])
        
        # 计算数量：硬件 40%，软件 60%
        hw_count = max(2, len(hw_keywords) * 2 // 5)  # 至少 2 个硬件关键词
        sw_count = max(3, len(sw_keywords) * 3 // 5)  # 至少 3 个软件关键词
        
        # 根据星期几轮换
        hw_start = (day * 2) % max(1, len(hw_keywords))
        sw_start = (day * 2) % max(1, len(sw_keywords))
        
        hw_selected = (hw_keywords[hw_start:] + hw_keywords[:hw_start])[:hw_count]
        sw_selected = (sw_keywords[sw_start:] + sw_keywords[:sw_start])[:sw_count]
        
        keywords = hw_selected + sw_selected + site_searches[:1]

    # 随机打乱顺序
    shuffled = keywords.copy()
    random.shuffle(shuffled)
    return shuffled


def get_hardware_keywords(region: str) -> list:
    """获取硬件专用关键词"""
    return KEYWORDS_HARDWARE.get(region, KEYWORDS_HARDWARE["us"])


def is_hardware_query_text(query: str) -> bool:
    """基于关键词判断是否为硬件查询（混合模式路由用）"""
    q = query.lower()
    hardware_terms = [
        "hardware", "robot", "robotics", "chip", "semiconductor", "wearable",
        "glasses", "ring", "pendant", "device", "gadget", "embodied", "edge",
        "smart glasses", "kickstarter", "indiegogo", "crowdfunding",
        "硬件", "机器人", "人形机器人", "芯片", "半导体", "具身智能", "智能眼镜",
        "可穿戴", "吊坠", "戒指", "设备", "众筹",
    ]
    return any(term in q for term in hardware_terms)


def resolve_keyword_type(keyword: str, region_key: str, product_type: str) -> str:
    """混合模式下按关键词路由硬件/软件 prompt"""
    if product_type != "mixed":
        return product_type
    hw_keywords = set(get_hardware_keywords(region_key))
    if keyword in hw_keywords or is_hardware_query_text(keyword):
        return "hardware"
    return "software"

def get_software_keywords(region: str) -> list:
    """获取软件专用关键词"""
    return KEYWORDS_SOFTWARE.get(region, KEYWORDS_SOFTWARE["us"])

def get_region_order() -> list:
    """随机化地区搜索顺序，避免固定偏差"""
    regions = list(REGION_CONFIG.keys())
    random.shuffle(regions)
    return regions

# ============================================
# 地区配置 (按比例分配搜索任务)
# ============================================
REGION_CONFIG = {
    'us': {
        'name': '🇺🇸 美国',
        'weight': 40,  # 40%
        'search_engine': 'bing',
        'keywords': [
            'AI startup funding Series A B 2026',
            'artificial intelligence company raised funding',
            'YC AI startup demo day 2026',
            'AI unicorn startup valuation',
        ],
    },
    'cn': {
        'name': '🇨🇳 中国',
        'weight': 25,  # 25%
        'search_engine': 'sogou',
        'keywords': [
            'AI创业公司 融资 AIGC 大模型 获投',
            '人工智能 初创公司 A轮 B轮 融资',
            '大模型 创业公司 估值 融资新闻',
            'AIGC 独角兽 融资 2026',
        ],
    },
    'eu': {
        'name': '🇪🇺 欧洲',
        'weight': 15,  # 15%
        'search_engine': 'bing',
        'keywords': [
            'European AI startup funding Sifted',
            'Europe artificial intelligence company raised',
            'UK France Germany AI startup Series A',
        ],
    },
    'jp': {
        'name': '🇯🇵🇰🇷 日韩',
        'weight': 10,  # 10%
        'search_engine': 'bing',
        'keywords': [
            'Japan Korea AI startup funding',
            'Japanese artificial intelligence company raised',
            'Korean AI startup investment',
        ],
    },
    'sea': {
        'name': '🇸🇬 东南亚',
        'weight': 10,  # 10%
        'search_engine': 'bing',
        'keywords': [
            'Southeast Asia AI startup e27 funding',
            'Singapore Indonesia Vietnam AI company raised',
            'Tech in Asia artificial intelligence funding',
        ],
    },
}

# ============================================
# 项目路径设置 (必须在导入 prompts 之前)
# ============================================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
AUTO_DISCOVER_LOCK_FILE = os.environ.get(
    'AUTO_DISCOVER_LOCK_FILE',
    os.path.join(PROJECT_ROOT, 'logs', 'auto_discover.lock')
)
KEYWORD_YIELD_STATS_FILE = os.path.join(PROJECT_ROOT, 'data', 'metrics', 'keyword_yield_stats.json')

try:
    from utils.demand_signals import DemandSignalEngine, apply_demand_guardrail
    HAS_DEMAND_SIGNALS = True
except Exception as e:
    HAS_DEMAND_SIGNALS = False
    print(f"⚠️ demand_signals module not available: {e}")


def apply_keyword_limit(region_key: str, keywords: List[str]) -> List[str]:
    keyword_limit = 0
    if region_key == "cn" and MAX_KEYWORDS_CN > 0:
        keyword_limit = MAX_KEYWORDS_CN
    elif MAX_KEYWORDS_DEFAULT > 0:
        keyword_limit = MAX_KEYWORDS_DEFAULT
    if keyword_limit and len(keywords) > keyword_limit:
        return keywords[:keyword_limit]
    return keywords


def build_search_text(search_results: List[dict], snippet_limit: int = AUTO_DISCOVER_RESULT_SNIPPET_MAX_CHARS) -> str:
    blocks = []
    for r in search_results:
        title = str(r.get('title', 'No Title') or 'No Title').strip()
        url = str(r.get('url', 'N/A') or 'N/A').strip()
        date_text = str(r.get('date', '') or '').strip()
        raw_snippet = str(r.get('content', r.get('snippet', '')) or '').strip()
        snippet = raw_snippet[:snippet_limit]
        lines = [f"### {title}", f"URL: {url}"]
        if date_text:
            lines.append(f"Date: {date_text}")
        lines.append(snippet)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _extract_domain_from_result(result: dict) -> str:
    raw_url = str(result.get("url", "") or "").strip()
    if not raw_url:
        return ""
    try:
        parsed = urlparse(raw_url)
        host = (parsed.netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def should_analyze_search_results(search_results: List[dict], query: str) -> Tuple[bool, str]:
    query_text = str(query or "").lower()
    if "site:" in query_text:
        return True, "site_query_bypass"
    if len(search_results) < 3:
        return False, "too_few_results"

    domains = {_extract_domain_from_result(r) for r in search_results if _extract_domain_from_result(r)}
    if len(domains) < 2:
        return False, "too_few_domains"

    signal_terms = [
        "raise", "raised", "raises", "funding", "series a", "series b", "series c",
        "launch", "launched", "release", "released", "preview", "beta", "introduc", "unveil",
        "融资", "获投", "a轮", "b轮", "发布", "推出", "上线", "众筹",
    ]
    signal_blob = " ".join(
        f"{(r.get('title') or '').lower()} {(r.get('content', r.get('snippet', '')) or '').lower()}"
        for r in search_results
    )
    if not any(term in signal_blob for term in signal_terms):
        return False, "missing_signal_terms"
    return True, "signal_ok"


def _safe_load_json_dict(path: str) -> Dict[str, Any]:
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def _safe_save_json_dict(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_keyword_yield_stats() -> Dict[str, Any]:
    data = _safe_load_json_dict(KEYWORD_YIELD_STATS_FILE)
    if not data:
        return {
            "meta": {"updated_at": "", "version": "v1"},
            "keywords": {},
        }
    if not isinstance(data.get("keywords"), dict):
        data["keywords"] = {}
    if not isinstance(data.get("meta"), dict):
        data["meta"] = {"updated_at": "", "version": "v1"}
    return data


def rank_keywords_by_yield(region_key: str, keywords: List[str], stats: Dict[str, Any]) -> List[str]:
    if not keywords:
        return []
    region_stats = (stats.get("keywords") or {}).get(region_key, {})
    if not isinstance(region_stats, dict):
        return list(keywords)

    scored = []
    for idx, keyword in enumerate(keywords):
        row = region_stats.get(keyword) if isinstance(region_stats, dict) else None
        if not isinstance(row, dict):
            scored.append((0.0, 0, idx, keyword))
            continue
        saved = int(row.get("saved", 0) or 0)
        dark = int(row.get("dark_horses", 0) or 0)
        searches = int(row.get("searches", 0) or 0)
        precision = (saved / searches) if searches > 0 else 0.0
        dh_boost = (dark / max(saved, 1))
        score = precision * 0.7 + dh_boost * 0.3
        scored.append((score, saved, idx, keyword))

    scored.sort(key=lambda x: (x[0], x[1], -x[2]), reverse=True)
    return [row[3] for row in scored]


def update_keyword_yield_stats(
    stats: Dict[str, Any],
    *,
    region_key: str,
    keyword: str,
    searches: int = 0,
    extracted: int = 0,
    saved: int = 0,
    dark_horses: int = 0,
) -> None:
    if not keyword:
        return
    keywords_bucket = stats.setdefault("keywords", {})
    if not isinstance(keywords_bucket, dict):
        keywords_bucket = {}
        stats["keywords"] = keywords_bucket
    region_bucket = keywords_bucket.setdefault(region_key, {})
    if not isinstance(region_bucket, dict):
        region_bucket = {}
        keywords_bucket[region_key] = region_bucket
    row = region_bucket.setdefault(keyword, {})
    if not isinstance(row, dict):
        row = {}
        region_bucket[keyword] = row

    row["searches"] = int(row.get("searches", 0) or 0) + int(max(searches, 0))
    row["extracted"] = int(row.get("extracted", 0) or 0) + int(max(extracted, 0))
    row["saved"] = int(row.get("saved", 0) or 0) + int(max(saved, 0))
    row["dark_horses"] = int(row.get("dark_horses", 0) or 0) + int(max(dark_horses, 0))
    row["last_seen"] = datetime.utcnow().strftime("%Y-%m-%d")


def flush_keyword_yield_stats(stats: Dict[str, Any]) -> None:
    meta = stats.get("meta")
    if not isinstance(meta, dict):
        meta = {}
        stats["meta"] = meta
    meta["updated_at"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    meta["version"] = "v1"
    _safe_save_json_dict(KEYWORD_YIELD_STATS_FILE, stats)

# ============================================
# Prompt 模块 (独立优化的搜索和分析 Prompt)
# ============================================

# 导入模块化 Prompt
try:
    from prompts.search_prompts import (
        generate_search_queries,
        generate_discovery_query,
        get_search_params,
        SEARCH_QUERIES_BY_REGION,
    )
    from prompts.analysis_prompts import (
        ANALYSIS_PROMPT_EN,
        ANALYSIS_PROMPT_CN,
        SCORING_PROMPT,
        get_analysis_prompt,
        get_scoring_prompt,
        get_hardware_analysis_prompt,
        validate_hardware_product,
        WELL_KNOWN_PRODUCTS as PROMPT_WELL_KNOWN,
        GENERIC_WHY_MATTERS as PROMPT_GENERIC,
    )
    USE_MODULAR_PROMPTS = True
    print("✅ Loaded modular prompts from prompts/")
except ImportError as e:
    USE_MODULAR_PROMPTS = False
    print(f"⚠️ prompts/ module not found: {e}")

# Fallback: 内联 Prompt（当模块未加载时使用）
if not USE_MODULAR_PROMPTS:
    # 英文版 Prompt (us/eu/jp/kr/sea)
    ANALYSIS_PROMPT_EN = """You are WeeklyAI's AI Product Analyst. Extract and score AI products from search results.

## Search Results
{search_results}

## STRICT EXCLUSIONS (Never Include):
- Well-Known: ChatGPT, Claude, Gemini, Copilot, DALL-E, Sora, Midjourney, Cursor, Perplexity
- Not Products: LangChain, PyTorch, papers only, tool directories
- Big Tech: Google Gemini, Meta Llama, Microsoft Copilot

## DARK HORSE (4-5) - Must meet ≥2:
| growth_anomaly | founder_background | funding_signal | category_innovation | community_buzz |

**5 points**: Funding >$100M OR Top-tier founder OR Category creator
**4 points**: Funding >$30M OR YC/a16z backed OR ARR >$10M

## RISING STAR (2-3) - Need 1:
**3 points**: Funding $1M-$5M OR ProductHunt top 10
**2 points**: Just launched, clear innovation

## CRITICAL: why_matters must have specific numbers!
✅ GOOD: "Sequoia领投$50M，8个月ARR从0到$10M"
❌ BAD: "This is a promising AI product"

## CRITICAL: Company Country Verification
- `region` is search market only, not company nationality.
- Fill `company_country` using evidence from search results.
- If uncertain, set `company_country` to "unknown" and lower confidence.

## Output (JSON only)
```json
[{{"name": "...", "website": "https://...", "description": "中文描述(>20字)", "category": "coding|image|video|...", "region": "{region}", "company_country": "US|CN|unknown", "company_country_confidence": 0.8, "funding_total": "$50M", "dark_horse_index": 4, "criteria_met": ["funding_signal"], "why_matters": "具体数字+差异化", "source": "...", "confidence": 0.85}}]
```

Quota: Dark Horses: {quota_dark_horses} | Rising Stars: {quota_rising_stars}
Return [] if nothing qualifies."""

    # 中文版 Prompt (cn)
    ANALYSIS_PROMPT_CN = """你是 WeeklyAI 的 AI 产品分析师。从搜索结果中提取并评分 AI 产品。

## 搜索结果
{search_results}

## 严格排除：
- 已知名: ChatGPT, Claude, Gemini, Cursor, Kimi, 豆包, 通义千问, 文心一言
- 非产品: LangChain, PyTorch, 只有论文/demo
- 大厂: Google Gemini, 百度文心, 阿里通义

## 黑马 (4-5分) - 满足≥2条:
| growth_anomaly | founder_background | funding_signal | category_innovation | community_buzz |

**5分**: 融资>$100M 或 顶级创始人 或 品类开创者
**4分**: 融资>$30M 或 YC/a16z背书 或 ARR>$10M

## 潜力股 (2-3分) - 满足1条:
**3分**: 融资$1M-$5M 或 ProductHunt Top 10
**2分**: 刚发布但有明显创新

## why_matters 必须有具体数字!
✅ GOOD: "Sequoia领投$50M，8个月ARR从0到$10M"
❌ BAD: "这是一个很有潜力的AI产品"

## 关键：公司国籍校验
- `region` 只是搜索市场，不是公司国籍。
- 根据搜索结果证据填写 `company_country`。
- 不确定时必须填 `"company_country": "unknown"` 并降低置信度。

## 输出 (仅JSON)
```json
[{{"name": "产品名", "website": "https://...", "description": "中文描述(>20字)", "category": "coding|image|video|...", "region": "{region}", "company_country": "US|CN|unknown", "company_country_confidence": 0.8, "funding_total": "$50M", "dark_horse_index": 4, "criteria_met": ["funding_signal"], "why_matters": "具体数字+差异化", "source": "...", "confidence": 0.85}}]
```

配额: 黑马: {quota_dark_horses} | 潜力股: {quota_rising_stars}
没有符合条件的返回 []。"""

    # 评分 Prompt
    SCORING_PROMPT = """评估产品的"黑马指数"(1-5分)：

## 产品
{product}

## 评分标准
5分: 融资>$100M 或 顶级创始人背景 或 品类开创者
4分: 融资>$30M 或 YC/a16z投资 或 ARR>$10M
3分: 融资$5M-$30M 或 ProductHunt Top 5
2分: 有创新点但数据不足
1分: 边缘产品或待验证

## 返回格式（仅JSON）
```json
{{"dark_horse_index": 4, "criteria_met": ["funding_signal"], "reason": "评分理由"}}
```"""


def get_extraction_prompt(region_key: str) -> str:
    """
    根据地区选择合适的分析 prompt
    
    Args:
        region_key: 地区代码 (cn/us/eu/jp/kr/sea)

    Returns:
        对应地区的 prompt 模板
    """
    if region_key == "cn":
        return ANALYSIS_PROMPT_CN
    else:
        return ANALYSIS_PROMPT_EN


# 别名：兼容旧代码
PROMPT_EXTRACTION_EN = ANALYSIS_PROMPT_EN if not USE_MODULAR_PROMPTS else ANALYSIS_PROMPT_EN
PROMPT_EXTRACTION_CN = ANALYSIS_PROMPT_CN if not USE_MODULAR_PROMPTS else ANALYSIS_PROMPT_CN
PROMPT_DARK_HORSE_SCORING = SCORING_PROMPT if not USE_MODULAR_PROMPTS else SCORING_PROMPT

# 数据文件路径
DARK_HORSES_DIR = os.path.join(PROJECT_ROOT, 'data', 'dark_horses')
RISING_STARS_DIR = os.path.join(PROJECT_ROOT, 'data', 'rising_stars')
CANDIDATES_DIR = os.path.join(PROJECT_ROOT, 'data', 'candidates')


def acquire_process_lock(lock_path: str):
    """单实例锁，避免并发运行导致 API 并发超限"""
    try:
        import fcntl
    except ImportError:
        print("⚠️ fcntl not available; skipping process lock")
        return None, True

    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    lock_file = open(lock_path, 'w')
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_file.close()
        return None, False

    lock_file.write(f"{os.getpid()}\n{datetime.utcnow().isoformat()}Z\n")
    lock_file.flush()
    return lock_file, True

# 渠道配置
SOURCES = {
    # 美国渠道
    'techcrunch': {
        'name': 'TechCrunch',
        'region': '🇺🇸',
        'url': 'https://techcrunch.com/category/artificial-intelligence/',
        'rss': 'https://techcrunch.com/category/artificial-intelligence/feed/',
        'keywords': ['raises', 'Series A', 'Series B', 'funding', 'AI startup'],
        'tier': 1,
    },
    'producthunt': {
        'name': 'ProductHunt',
        'region': '🇺🇸',
        'url': 'https://www.producthunt.com/topics/artificial-intelligence',
        'api': 'https://api.producthunt.com/v2/api/graphql',
        'keywords': ['AI', 'machine learning', 'LLM'],
        'tier': 2,
    },
    'ycombinator': {
        'name': 'Y Combinator',
        'region': '🇺🇸',
        'url': 'https://www.ycombinator.com/companies?tags=AI',
        'keywords': ['YC', 'Demo Day'],
        'tier': 1,
    },

    # 中国渠道
    '36kr': {
        'name': '36氪',
        'region': '🇨🇳',
        'url': 'https://36kr.com/information/AI/',
        'rss': 'https://36kr.com/feed',
        'keywords': ['AI融资', '人工智能', 'AIGC', '大模型', '获投'],
        'tier': 1,
    },
    'itjuzi': {
        'name': 'IT桔子',
        'region': '🇨🇳',
        'url': 'https://www.itjuzi.com/investevent',
        'keywords': ['AI', '人工智能', '机器学习'],
        'tier': 1,
    },
    'jiqizhixin': {
        'name': '机器之心',
        'region': '🇨🇳',
        'url': 'https://www.jiqizhixin.com/',
        'rss': 'https://www.jiqizhixin.com/rss',
        'keywords': ['AI', '融资', '创业'],
        'tier': 2,
    },

    # 欧洲渠道
    'sifted': {
        'name': 'Sifted',
        'region': '🇪🇺',
        'url': 'https://sifted.eu/sector/artificial-intelligence',
        'keywords': ['AI', 'funding', 'European startup'],
        'tier': 1,
    },
    'eu_startups': {
        'name': 'EU-Startups',
        'region': '🇪🇺',
        'url': 'https://www.eu-startups.com/category/artificial-intelligence/',
        'rss': 'https://www.eu-startups.com/feed/',
        'keywords': ['AI', 'raises', 'funding'],
        'tier': 2,
    },

    # 日韩渠道
    'bridge': {
        'name': 'Bridge',
        'region': '🇯🇵',
        'url': 'https://thebridge.jp/en/',
        'keywords': ['AI', 'startup', 'funding', 'Japan'],
        'tier': 1,
    },
    'platum': {
        'name': 'Platum',
        'region': '🇰🇷',
        'url': 'https://platum.kr/archives/category/ai',
        'keywords': ['AI', 'startup', 'Korea'],
        'tier': 1,
    },

    # 东南亚渠道
    'e27': {
        'name': 'e27',
        'region': '🇸🇬',
        'url': 'https://e27.co/tag/artificial-intelligence/',
        'keywords': ['AI', 'Southeast Asia', 'funding'],
        'tier': 1,
    },
    'techinasia': {
        'name': 'Tech in Asia',
        'region': '🇸🇬',
        'url': 'https://www.techinasia.com/tag/artificial-intelligence',
        'keywords': ['AI', 'Asia', 'startup'],
        'tier': 1,
    },
}


def get_current_week():
    """获取当前周数"""
    now = datetime.now()
    return f"{now.year}_{now.isocalendar()[1]:02d}"


def load_existing_products():
    """加载所有已存在的产品名称和网址"""
    existing = set()

    # 加载黑马
    if os.path.exists(DARK_HORSES_DIR):
        for f in os.listdir(DARK_HORSES_DIR):
            if f.endswith('.json'):
                with open(os.path.join(DARK_HORSES_DIR, f), 'r') as file:
                    products = json.load(file)
                    for p in products:
                        existing.add(p.get('name', '').lower())
                        existing.add(p.get('website', '').lower())

    # 加载潜力股
    if os.path.exists(RISING_STARS_DIR):
        for f in os.listdir(RISING_STARS_DIR):
            if f.endswith('.json'):
                with open(os.path.join(RISING_STARS_DIR, f), 'r') as file:
                    products = json.load(file)
                    for p in products:
                        existing.add(p.get('name', '').lower())
                        existing.add(p.get('website', '').lower())

    return existing


def is_duplicate(name: str, website: str, existing: set) -> bool:
    """
    检查是否重复（基础版本）
    
    使用名称和网站的精确匹配
    """
    return name.lower() in existing or website.lower() in existing


def normalize_url(url: str) -> str:
    """
    标准化 URL，提取主域名用于去重

    "https://www.example.com/page" → "example.com"
    """
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        return domain.lower()
    except:
        return url.lower()


# ============================================
# 增强去重检查器（使用新模块）
# ============================================

class EnhancedDuplicateChecker:
    """
    增强的去重检查器
    
    结合新的 dedup 模块和旧的逻辑
    """
    
    def __init__(self, existing_products: list):
        """
        初始化检查器
        
        Args:
            existing_products: 已有产品列表
        """
        self.existing_products = existing_products
        
        # 使用新模块
        if USE_NEW_DEDUP:
            self.checker = DuplicateChecker(
                existing_products,
                similarity_threshold=0.90,
                check_similarity=True
            )
        else:
            self.checker = None
        
        # 旧索引（作为 fallback）
        self.existing_names = set()
        self.existing_domains = set()
        
        for p in existing_products:
            name = p.get('name', '').lower().strip()
            if name:
                self.existing_names.add(name)
            
            website = p.get('website', '')
            if website:
                domain = normalize_url(website)
                if domain:
                    self.existing_domains.add(domain)
    
    def is_duplicate(self, product: dict) -> tuple:
        """
        检查产品是否重复
        
        Returns:
            (是否重复, 重复原因)
        """
        name = product.get('name', '')
        website = product.get('website', '')
        
        # 优先使用新模块
        if self.checker:
            return self.checker.is_duplicate(product)
        
        # Fallback 到旧逻辑
        name_lower = name.lower().strip()
        if name_lower in self.existing_names:
            return True, f"名称重复: {name}"
        
        if website:
            domain = normalize_url(website)
            if domain and domain in self.existing_domains:
                return True, f"域名重复: {domain}"
        
        return False, None
    
    def add_product(self, product: dict):
        """添加新产品到索引"""
        if self.checker:
            self.checker.add_product(product)
        
        # 同时更新旧索引
        name = product.get('name', '').lower().strip()
        if name:
            self.existing_names.add(name)
        
        website = product.get('website', '')
        if website:
            domain = normalize_url(website)
            if domain:
                self.existing_domains.add(domain)


def verify_url_exists(url: str, timeout: int = 5) -> bool:
    """
    验证 URL 是否真实存在（可访问）
    
    Args:
        url: 要验证的 URL
        timeout: 超时时间（秒）
        
    Returns:
        True 如果 URL 可访问，False 否则
    """
    if not url or url.lower() == "unknown":
        return False
    
    try:
        # 确保有协议
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        
        # 禁用 SSL 警告（LibreSSL 版本问题）
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # 发送 GET 请求（HEAD 有时被拒绝）
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; WeeklyAI Bot)"},
            verify=False,  # 禁用 SSL 验证（LibreSSL 兼容性）
            stream=True  # 不下载内容
        )
        response.close()
        return response.status_code < 400
    except requests.exceptions.RequestException:
        return False


def is_duplicate_domain(product: dict, existing_domains: set) -> bool:
    """检查域名是否已存在"""
    domain = normalize_url(product.get("website", ""))
    return domain in existing_domains if domain else False


# ============================================
# 质量过滤器
# ============================================

# 泛化的 why_matters 黑名单（会被过滤掉）
GENERIC_WHY_MATTERS = [
    "很有潜力",
    "值得关注",
    "有前景",
    "表现不错",
    "团队背景不错",
    "融资情况良好",
    "市场前景广阔",
    "技术实力强",
    "用户反馈良好",
    "增长迅速",
]

# 知名产品排除名单（不是黑马）
WELL_KNOWN_PRODUCTS = {
    # 国际知名 AI 产品
    "chatgpt", "openai", "claude", "anthropic", "gemini", "bard",
    "copilot", "github copilot", "dall-e", "dall-e 3", "sora",
    "midjourney", "stable diffusion", "stability ai",
    "cursor", "perplexity", "elevenlabs", "eleven labs",
    "synthesia", "runway", "runway ml", "pika", "pika labs",
    "bolt.new", "bolt", "v0.dev", "v0", "replit", "together ai", "groq",
    "character.ai", "character ai", "jasper", "jasper ai",
    "notion ai", "grammarly", "copy.ai", "writesonic",
    "huggingface", "hugging face", "langchain", "llamaindex",
    # 中国知名 AI 产品
    "kimi", "月之暗面", "moonshot", "doubao", "豆包", "字节跳动",
    "tongyi", "通义千问", "通义", "qwen", "wenxin", "文心一言", "文心",
    "ernie", "百度", "baidu",
    "讯飞星火", "星火", "spark", "minimax", "abab",
    # 大厂产品
    "google gemini", "google bard", "meta llama", "llama",
    "microsoft copilot", "bing chat", "amazon q", "aws bedrock",
}

# ── 不可信 source 黑名单 ─────────────────────────────────────────────
UNTRUSTED_SOURCES = {
    # 零售平台
    "楽天市場", "rakuten", "眼鏡市場", "amazon", "taobao", "淘宝",
    "京东", "jd.com", "天猫", "aliexpress", "ebay",
    # 视频平台
    "youtube", "bilibili", "tiktok", "抖音", "快手",
    # 社交媒体
    "twitter", "x.com", "微博", "weibo", "知乎", "zhihu",
    "reddit", "facebook", "instagram",
}

# source_url 域名黑名单（防 source 字段被模型伪造）
UNTRUSTED_SOURCE_DOMAINS = {
    # 零售/电商
    "rakuten.co.jp", "item.rakuten.co.jp", "amazon.com", "amazon.co.jp",
    "taobao.com", "tmall.com", "jd.com", "aliexpress.com", "ebay.com",
    # 视频/短视频
    "youtube.com", "youtu.be", "bilibili.com", "tiktok.com", "douyin.com", "kuaishou.com",
    # 社交/社区
    "x.com", "twitter.com", "weibo.com", "zhihu.com", "reddit.com", "facebook.com", "instagram.com",
}

PLACEHOLDER_SOURCE_DOMAINS = {
    "example.com", "example.org", "example.net", "localhost", "127.0.0.1",
}

# ── 博客标题特征词 ────────────────────────────────────────────────────
BLOG_TITLE_MARKERS = [
    "：", "？", "！", "如何", "什么是", "为什么", "的下一个",
    "风口", "趋势", "未来", "盘点", "合集", "Top",
]

# ── 通用概念名（不是产品名）────────────────────────────────────────────
GENERIC_CONCEPT_NAMES = [
    "AI随身设备", "AI智能助手", "智能穿戴设备", "AI硬件",
    "AI眼镜", "AI助手", "智能硬件", "AI可穿戴",
    "AI wearable", "AI device", "AI hardware", "smart glasses",
]


def validate_source(product: dict) -> tuple[bool, str]:
    """验证产品来源是否可信"""
    source = product.get("source", "").strip().lower()
    source_url = product.get("source_url", "").strip().lower()

    if not source:
        source = ""

    for untrusted in UNTRUSTED_SOURCES:
        if source and untrusted.lower() in source:
            return False, f"untrusted source: {source}"

    if source_url:
        domain = normalize_url(source_url)
        if domain in PLACEHOLDER_SOURCE_DOMAINS:
            return False, f"placeholder source_url domain: {domain}"
        for blocked in UNTRUSTED_SOURCE_DOMAINS:
            if blocked in domain:
                return False, f"untrusted source_url domain: {domain}"

    return True, "source ok"


def validate_product_name(name: str) -> tuple[bool, str]:
    """验证产品名是否像真正的产品名（不是博客标题或通用概念）"""
    if not name:
        return False, "empty name"

    # 检查博客标题特征
    if len(name) > 10:
        matching_markers = [m for m in BLOG_TITLE_MARKERS if m in name]
        if len(matching_markers) >= 1:
            return False, f"name looks like blog title (markers: {matching_markers})"

    # 检查通用概念名
    name_lower = name.lower().strip()
    for concept in GENERIC_CONCEPT_NAMES:
        if name_lower == concept.lower() or name_lower.startswith(concept.lower()):
            return False, f"name is generic concept: {concept}"

    return True, "name ok"


def validate_against_search_results(
    product: dict, search_results: list
) -> tuple[bool, str]:
    """
    交叉验证：产品名是否在搜索结果中出现过。
    这是防止 LLM 幻觉的最重要检查。

    Args:
        product: 提取的产品
        search_results: 原始搜索结果列表 (SearchResult 对象或字典)

    Returns:
        (是否通过, 原因)
    """
    if not search_results:
        return True, "no search results to cross-check"

    name = product.get("name", "").strip()
    if not name:
        return False, "no name"

    # 将所有搜索结果的文本合并
    search_text_combined = ""
    for r in search_results:
        if isinstance(r, dict):
            search_text_combined += " " + (r.get("title", "") + " " +
                                           r.get("content", "") + " " +
                                           r.get("snippet", "") + " " +
                                           r.get("url", ""))
        elif hasattr(r, 'title'):
            search_text_combined += " " + (r.title + " " + r.snippet + " " + r.url)

    search_text_lower = search_text_combined.lower()

    # 检查产品名（或其主要部分）是否在搜索结果中出现
    name_lower = name.lower()

    # 精确匹配
    if name_lower in search_text_lower:
        return True, "exact match in search results"

    # 部分匹配（对于中文名可能需要）: 至少 3 个字符的子串
    name_parts = name.split()
    for part in name_parts:
        if len(part) >= 3 and part.lower() in search_text_lower:
            return True, f"partial match: {part}"

    # 对于中文名，检查连续 3+ 字符
    if any('\u4e00' <= c <= '\u9fff' for c in name):
        for i in range(len(name) - 2):
            chunk = name[i:i+3]
            if chunk.lower() in search_text_lower:
                return True, f"chinese partial match: {chunk}"

    # source_url 检查：如果产品的 source_url 在搜索结果中
    source_url = product.get("source_url", "")
    if source_url:
        for r in search_results:
            r_url = r.get("url", "") if isinstance(r, dict) else getattr(r, 'url', '')
            if source_url == r_url:
                return True, "source_url matches search result"

    return False, f"product '{name}' not found in search results (possible hallucination)"


def validate_product(product: dict) -> tuple[bool, str]:
    """
    验证产品质量，返回 (是否通过, 原因)

    过滤条件:
    1. 必须有有效的 website URL
    2. description 必须 >20 字符
    3. why_matters 不能是泛化描述
    4. name 不能是新闻标题
    5. 知名产品排除（使用 WELL_KNOWN_PRODUCTS）
    6. 黑马(4-5分)必须满足至少2条标准 (criteria_met)
    7. 置信度检查 (confidence >= 0.6)
    """
    name = product.get("name", "").strip()
    website = product.get("website", "").strip()
    description = product.get("description", "").strip()
    why_matters = product.get("why_matters", "").strip()

    # 0a. 检查产品名是否合法（防博客标题/通用概念）
    name_valid, name_reason = validate_product_name(name)
    if not name_valid:
        return False, name_reason

    # 0b. 检查来源是否可信（防零售/视频/社交平台）
    source_valid, source_reason = validate_source(product)
    if not source_valid:
        return False, source_reason

    # 1. 检查必填字段
    if not name:
        return False, "missing name"
    if not description:
        return False, "missing description"
    if not why_matters:
        return False, "missing why_matters"

    # 2. 检查 website
    if not website:
        return False, "missing website"
    if website.lower() == "unknown":
        return False, "unknown website not allowed"
    
    # 修复缺少协议的 URL
    if not website.startswith(("http://", "https://")) and "." in website:
        website = f"https://{website}"
        product["website"] = website
    
    if website.lower() == "unknown":
        return False, "unknown website not allowed"
    elif not website.startswith(("http://", "https://")):
        return False, "invalid website URL"

    # 3. 检查 description 长度
    if len(description) < 20:
        return False, f"description too short ({len(description)} chars)"

    # 4. 检查 why_matters 是否太泛化
    #    Fix: use OR — reject if contains generic phrase OR is too short.
    #    Previous AND logic allowed very short generic texts through.
    why_lower = why_matters.lower()
    for generic in GENERIC_WHY_MATTERS:
        if generic in why_lower or len(why_matters) < 30:
            return False, f"generic why_matters: contains '{generic}' or too short ({len(why_matters)} chars)"

    # 5. 检查 why_matters 是否包含具体数字（融资/ARR/用户数）
    has_number = bool(re.search(r'[\$¥€]\d+|ARR|\d+[MBK万亿]|\d+%', why_matters))
    has_specific = any(kw in why_matters for kw in [
        '领投', '融资', '估值', '用户', '增长', 'ARR', '首创', '首个',
        '前OpenAI', '前Google', '前Meta', 'YC', 'a16z', 'Sequoia',
    ])
    if not has_number and not has_specific:
        return False, "why_matters lacks specific details"

    # 6. 检查 name 是否像新闻标题（中文区更容易把标题当产品名）
    news_patterns = [
        '融资', '宣布', '发布', '获得', '完成', '推出', '上线',
        '投资', '领投', '参投', '被投', '收购', '估值',
        '独家', '爆料', '报道', '曝光', '传出', '消息', '传闻',
    ]
    if any(p in name for p in news_patterns) and len(name) >= 8:
        return False, "name looks like news headline"

    # 7. 检查是否是知名产品
    name_lower = name.lower()
    if name_lower in WELL_KNOWN_PRODUCTS:
        return False, f"well-known product: {name}"
    # 检查部分匹配（例如 "ChatGPT Plus" 包含 "chatgpt"）
    for known in WELL_KNOWN_PRODUCTS:
        if known in name_lower or name_lower in known:
            return False, f"well-known product match: {known}"

    # 8. 检查黑马(4-5分)是否满足至少1条标准（放宽要求）
    # 注：原来要求 ≥2 条标准太严格，导致产出太少
    score = product.get("dark_horse_index", 0)
    if isinstance(score, str):
        try:
            score = int(float(score))
        except ValueError:
            score = 0
    criteria = product.get("criteria_met", [])
    if not isinstance(criteria, list):
        criteria = [criteria] if criteria else []
    if score >= 5 and len(criteria) < 2:
        # 5分黑马需要 ≥2 条标准
        return False, f"5-star dark_horse needs ≥2 criteria (has {len(criteria)})"
    if score == 4 and len(criteria) < 1:
        # 4分黑马只需要 ≥1 条标准
        return False, f"4-star dark_horse needs ≥1 criteria (has {len(criteria)})"

    # 9. 检查置信度（如果有）
    confidence = product.get("confidence", 1.0)
    if confidence < 0.6:
        return False, f"low confidence ({confidence:.2f})"

    # 10. Default missing categories to ["other"]
    cats = product.get("categories")
    if not cats or not isinstance(cats, list) or len(cats) == 0:
        product["categories"] = ["other"]

    # 11. Default missing/null region
    region = product.get("region")
    if not region or not isinstance(region, str) or not region.strip():
        product["region"] = UNKNOWN_COUNTRY_DISPLAY

    return True, "passed"


def load_existing_domains() -> set:
    """加载所有已存在的产品域名"""
    domains = set()

    for dir_path in [DARK_HORSES_DIR, RISING_STARS_DIR]:
        if os.path.exists(dir_path):
            for f in os.listdir(dir_path):
                if f.endswith('.json'):
                    try:
                        with open(os.path.join(dir_path, f), 'r') as file:
                            products = json.load(file)
                            for p in products:
                                domain = normalize_url(p.get('website', ''))
                                if domain:
                                    domains.add(domain)
                    except:
                        pass

    return domains


def get_perplexity_client():
    """
    获取 Perplexity 客户端

    Returns:
        PerplexityClient 实例或 None
    """
    if not PERPLEXITY_API_KEY:
        print("  ⚠️ PERPLEXITY_API_KEY not set")
        return None

    try:
        from utils.perplexity_client import PerplexityClient
        client = PerplexityClient(api_key=PERPLEXITY_API_KEY)
        if client.is_available():
            return client
        return None
    except ImportError as e:
        print(f"  ⚠️ perplexity_client module not found: {e}")
        return None


def get_glm_client():
    """
    获取 GLM (智谱) 客户端

    Returns:
        GLMClient 实例或 None
    """
    if not ZHIPU_API_KEY:
        print("  ⚠️ ZHIPU_API_KEY not set")
        return None

    try:
        from utils.glm_client import GLMClient
        client = GLMClient(api_key=ZHIPU_API_KEY)
        if client.is_available():
            return client
        return None
    except ImportError as e:
        print(f"  ⚠️ glm_client module not found: {e}")
        return None


def get_provider_for_region(region_key: str) -> str:
    """
    根据地区返回搜索 provider

    路由规则:
    - cn (中国) → GLM (如果可用且启用)
    - 其他地区 → Perplexity

    Args:
        region_key: 地区代码 (us/cn/eu/jp/kr/sea)

    Returns:
        provider 名称 ("glm" 或 "perplexity")
    """
    if region_key == "cn" and ZHIPU_API_KEY and USE_GLM_FOR_CN:
        return "glm"
    return "perplexity"


def perplexity_search(
    query: str,
    count: int = 10,
    region: Optional[str] = None,
    domain_filter: Optional[list] = None
) -> list:
    """
    使用 Perplexity Search API 进行实时 Web 搜索
    
    Args:
        query: 搜索查询
        count: 结果数量
        region: 地区代码 (us/cn/eu/jp/kr/sea)
        domain_filter: 域名过滤 (["techcrunch.com", "-reddit.com"] 等)
    
    Returns:
        [{"title": "", "url": "", "content": ""}, ...]
    """
    client = get_perplexity_client()
    if not client:
        return []
    
    try:
        if region:
            results = client.search_by_region(
                query,
                region=region,
                max_results=count
            )
        else:
            results = client.search(
                query,
                max_results=count,
                domain_filter=domain_filter
            )
        return [r.to_dict() for r in results]
    
    except Exception as e:
        print(f"  ❌ Perplexity Search Error: {e}")
        return []


def analyze_with_perplexity(content: str, task: str = "extract", region: str = "🇺🇸",
                            quota_remaining: dict = None, region_key: str = "us",
                            product_type: str = "mixed") -> dict:
    """
    使用 Perplexity Sonar 模型分析内容

    用于产品提取和评分。

    Args:
        content: 要分析的内容（搜索结果文本）
        task: 任务类型 (extract/score)
        region: 地区标识 (emoji flag)
        quota_remaining: 剩余配额 {"dark_horses": n, "rising_stars": m}
        region_key: 地区代码 (cn/us/eu/jp/kr/sea) 用于选择 prompt 语言

    Returns:
        解析后的 JSON（产品列表或评分结果）
    """
    client = get_perplexity_client()
    if not client:
        return {}

    if quota_remaining is None:
        quota_remaining = DAILY_QUOTA.copy()

    # 构建 prompt
    if task == "extract":
        if USE_MODULAR_PROMPTS and product_type == "hardware":
            prompt = get_hardware_analysis_prompt(
                search_results=content[:AUTO_DISCOVER_PROMPT_MAX_CHARS],
                region=region,
                quota_dark_horses=quota_remaining.get("dark_horses", 5),
                quota_rising_stars=quota_remaining.get("rising_stars", 10)
            )
        elif USE_MODULAR_PROMPTS:
            prompt = get_analysis_prompt(
                region_key=region_key,
                search_results=content[:AUTO_DISCOVER_PROMPT_MAX_CHARS],
                quota_dark_horses=quota_remaining.get("dark_horses", 5),
                quota_rising_stars=quota_remaining.get("rising_stars", 10),
                region_flag=region
            )
        else:
            prompt_template = get_extraction_prompt(region_key)
            prompt = prompt_template.format(
                search_results=content[:AUTO_DISCOVER_PROMPT_MAX_CHARS],
                region=region,
                quota_dark_horses=quota_remaining.get("dark_horses", 5),
                quota_rising_stars=quota_remaining.get("rising_stars", 10)
            )
    elif task == "score":
        prompt = SCORING_PROMPT.format(
            product=json.dumps(content, ensure_ascii=False, indent=2)
        ) if 'SCORING_PROMPT' in dir() else f"Score this product: {content}"
    else:
        return {}

    try:
        # 使用 analyze 方法 (Sonar Chat Completions)
        result = client.analyze(
            prompt=prompt,
            temperature=0.3,  # 低温度获得更稳定输出
            max_tokens=4096
        )
        return result if isinstance(result, (dict, list)) else {}

    except Exception as e:
        print(f"  ❌ Perplexity Analysis Error: {e}")
        return {}


# ============================================
# GLM (智谱) 搜索和分析函数 (中国区)
# ============================================

def glm_search(
    query: str,
    count: int = 10,
    region: Optional[str] = None,
) -> list:
    """
    使用 GLM 联网搜索 API 进行中国区搜索

    Args:
        query: 搜索查询
        count: 结果数量
        region: 地区代码 (主要用于 cn)

    Returns:
        [{"title": "", "url": "", "content": ""}, ...]
    """
    client = get_glm_client()
    if not client:
        return []

    try:
        results = client.search_by_region(
            query,
            region=region or "cn",
            max_results=count
        )
        return [r.to_dict() for r in results]

    except Exception as e:
        print(f"  ❌ GLM Search Error: {e}")
        return []


def analyze_with_glm(content: str, task: str = "extract", region: str = "🇨🇳",
                     quota_remaining: dict = None, region_key: str = "cn",
                     product_type: str = "mixed") -> dict:
    """
    使用 GLM 模型分析内容 (中国区)

    Args:
        content: 要分析的内容（搜索结果文本）
        task: 任务类型 (extract/score)
        region: 地区标识 (emoji flag)
        quota_remaining: 剩余配额 {"dark_horses": n, "rising_stars": m}
        region_key: 地区代码

    Returns:
        解析后的 JSON（产品列表或评分结果）
    """
    client = get_glm_client()
    if not client:
        return {}

    if quota_remaining is None:
        quota_remaining = DAILY_QUOTA.copy()

    # 构建 prompt (中国区使用中文 prompt)
    if task == "extract":
        if USE_MODULAR_PROMPTS and product_type == "hardware":
            prompt = get_hardware_analysis_prompt(
                search_results=content[:AUTO_DISCOVER_PROMPT_MAX_CHARS],
                region=region,
                quota_dark_horses=quota_remaining.get("dark_horses", 5),
                quota_rising_stars=quota_remaining.get("rising_stars", 10)
            )
        elif USE_MODULAR_PROMPTS:
            prompt = get_analysis_prompt(
                region_key=region_key,
                search_results=content[:AUTO_DISCOVER_PROMPT_MAX_CHARS],
                quota_dark_horses=quota_remaining.get("dark_horses", 5),
                quota_rising_stars=quota_remaining.get("rising_stars", 10),
                region_flag=region
            )
        else:
            prompt_template = get_extraction_prompt("cn")
            prompt = prompt_template.format(
                search_results=content[:AUTO_DISCOVER_PROMPT_MAX_CHARS],
                region=region,
                quota_dark_horses=quota_remaining.get("dark_horses", 5),
                quota_rising_stars=quota_remaining.get("rising_stars", 10)
            )

        # GLM is more likely to hallucinate websites / output headline-like names.
        # Add strict guardrails to keep results traceable and reduce junk entries.
        prompt += """

## GLM 额外要求（必须遵守，违反任何一条则不输出该产品）

### 反幻觉规则（最重要！）

1. **只提取搜索结果中明确提到的产品**。
   - 如果搜索结果中没有提到某个产品的名字，绝对不要输出它。
   - 不要从你的训练知识中"补充"产品。搜索结果里没有的 = 不存在。
   - 输出产品数量不能超过搜索结果中实际提到的不同产品数量。

2. `source_url` 必须精确复制自上方搜索结果中的 `Source URL:` 行。
   - 找不到可对应的 URL，就不要输出该产品。
   - 不允许编造 source_url，也不允许留空。

3. `website` 只有在搜索结果文本里「明确出现官网域名」时才填写。
   - 无法确认真实官网时：**不要输出该产品**（不要写 unknown）。
   - 不要凭感觉猜测官网（如把公司名拼成 .com/.ai）。

### 产品名称规则

4. `name` 必须是一个明确的「产品/公司名」，不能是：
   - 新闻标题或描述句（禁止包含：投资/领投/融资/独家/爆料/报道/曝光/消息/传闻/如何/什么是/风口/趋势）
   - 通用概念（如"AI随身设备"、"AI智能助手"、"智能穿戴设备"）
   - 博客文章标题（含"：""？""！"等标点的长句）

### 来源可信度规则

5. `source` 必须是权威媒体或产品平台，以下来源不可信，不要使用：
   - 零售平台：楽天市場、眼鏡市場、Amazon、淘宝、京东
   - 视频平台：YouTube、Bilibili、TikTok
   - 社交媒体：Twitter/X、微博、知乎
   - 如果搜索结果全部来自以上不可信来源，返回空数组 `[]`
"""
    elif task == "score":
        prompt = SCORING_PROMPT.format(
            product=json.dumps(content, ensure_ascii=False, indent=2)
        ) if 'SCORING_PROMPT' in dir() else f"评分产品: {content}"
    else:
        return {}

    try:
        result = client.analyze(
            prompt=prompt,
            temperature=0.3,
            max_tokens=4096
        )
        return result if isinstance(result, (dict, list)) else {}

    except Exception as e:
        print(f"  ❌ GLM Analysis Error: {e}")
        return {}


# ============================================
# Provider Routing Functions
# ============================================

def search_with_provider(query: str, region_key: str, search_engine: str = "bing") -> list:
    """
    根据地区路由搜索请求

    路由规则:
    - cn (中国) → GLM 联网搜索 (如果可用)
    - 其他地区 → Perplexity Search API

    Args:
        query: 搜索查询
        region_key: 地区代码 (us/cn/eu/jp/kr/sea)
        search_engine: 搜索引擎 (已弃用，保留兼容)

    Returns:
        搜索结果列表
    """
    provider = get_provider_for_region(region_key)

    if provider == "glm":
        print(f"    🔍 Using GLM for {region_key}")
        return glm_search(query, region=region_key)
    else:
        print(f"    🔍 Using Perplexity for {region_key}")
        return perplexity_search(query, region=region_key)


def analyze_with_provider(content, task: str, region_key: str, region_flag: str = "🇺🇸",
                          quota_remaining: dict = None, product_type: str = "mixed"):
    """
    根据地区路由分析请求

    路由规则:
    - cn (中国) → GLM 模型分析 (如果可用)
    - 其他地区 → Perplexity Sonar 分析

    Args:
        content: 要分析的内容
        task: 任务类型 (extract/score)
        region_key: 地区代码 (us/cn/eu/jp/kr/sea)
        region_flag: 地区标识 (emoji)
        quota_remaining: 剩余配额

    Returns:
        分析结果
    """
    provider = get_provider_for_region(region_key)

    if provider == "glm":
        return analyze_with_glm(content, task, region_flag, quota_remaining, region_key, product_type)
    else:
        return analyze_with_perplexity(content, task, region_flag, quota_remaining, region_key, product_type)


def fetch_url_content(url: str) -> str:
    """抓取 URL 内容"""
    try:
        import urllib.request
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8', errors='ignore')

            # 简单提取正文（去除 HTML 标签）
            content = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', content)
            content = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', content)
            content = re.sub(r'<[^>]+>', ' ', content)
            content = re.sub(r'\s+', ' ', content)
            return content[:15000]  # 限制长度
    except Exception as e:
        print(f"  Fetch error: {e}")
        return ""


def _normalize_match_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'\s+', '', text.lower())


def _score_search_result_for_name(name: str, result: dict) -> int:
    name_norm = _normalize_match_text(name)
    if not name_norm or len(name_norm) < 3:
        return -1

    title = _normalize_match_text(result.get('title', ''))
    content = _normalize_match_text(result.get('content') or result.get('snippet', ''))
    url = (result.get('url', '') or '').lower()

    score = 0
    if name_norm in title:
        score += 5
    if name_norm in content:
        score += 3
    if name_norm in url:
        score += 2

    tokens = re.findall(r'[a-z0-9]{3,}', name.lower())
    for token in tokens:
        if token in title:
            score += 2
        elif token in content:
            score += 1
        elif token in url:
            score += 1

    return score


def attach_source_url(product: dict, search_results: list, min_score: int = 4) -> None:
    """为产品匹配搜索结果 URL (用于后续官网解析)"""
    if product.get('source_url'):
        return

    name = product.get('name', '').strip()
    if not name or not search_results:
        return

    best_result = None
    best_score = -1
    for result in search_results:
        score = _score_search_result_for_name(name, result)
        if score > best_score:
            best_score = score
            best_result = result

    if best_result and best_score >= min_score:
        url = best_result.get('url', '')
        if url:
            product['source_url'] = url
        title = best_result.get('title', '')
        if title:
            product['source_title'] = title


def fetch_with_provider(source_config: dict, limit: int = 10) -> list:
    """
    使用 Provider 路由分析来源页面内容

    策略：
    1. 先尝试抓取网页
    2. 根据地区选择 Provider (cn→GLM, 其他→Perplexity) 提取并评分
    """
    source_name = source_config['name']
    region_flag = source_config['region']
    url = source_config.get('url', '')

    region_key_map = {
        '🇺🇸': 'us', '🇨🇳': 'cn', '🇪🇺': 'eu',
        '🇯🇵': 'jp', '🇰🇷': 'kr', '🇸🇬': 'sea'
    }
    region_key = region_key_map.get(region_flag, 'us')
    provider = get_provider_for_region(region_key)

    print(f"  Fetching: {url}")

    # 抓取网页内容
    content = fetch_url_content(url)
    products = []

    if content and len(content) > 500:
        print(f"  Analyzing page content with {provider}...")
        products = analyze_with_provider(content, task="extract", region_key=region_key, region_flag=region_flag)
        if not isinstance(products, list):
            products = []

    print(f"  Found {len(products)} potential products")

    # 补充信息并评分
    result = []
    for p in products[:limit]:
        # 添加来源信息
        p['source'] = source_name
        p['source_region'] = region_flag
        p['discovered_at'] = datetime.utcnow().strftime('%Y-%m-%d')
        if url and not p.get('source_url'):
            p['source_url'] = url
        apply_country_fields(p, fallback_region_flag=region_flag)

        score_result = analyze_with_provider(p, task="score", region_key=region_key, region_flag=region_flag)
        if isinstance(score_result, dict) and score_result:
            p['dark_horse_index'] = score_result.get('score', p.get('dark_horse_index', 2))
            if 'reason' in score_result:
                p['score_reason'] = score_result['reason']

        if 'dark_horse_index' not in p:
            p = analyze_and_score(p)

        result.append(p)

    return result


# 保持向后兼容的别名
fetch_with_perplexity = fetch_with_provider


def analyze_and_score(product: dict) -> dict:
    """
    使用 AI 分析产品并评分

    评分标准：
    - 5分: 融资 >$100M 或 顶级创始人 或 品类开创者
    - 4分: 融资 >$30M 或 YC/顶级VC
    - 3分: 融资 >$5M 或 ProductHunt Top 5
    - 2分: 有潜力但数据不足
    - 1分: 边缘
    """
    funding = product.get('funding_total', '')
    source = product.get('source', '')

    # 简单的规则评分（可以替换为 AI 评分）
    score = 2  # 默认

    # 解析融资金额
    funding_amount = 0
    if funding:
        match = re.search(r'\$?([\d.]+)\s*([BMK])?', funding, re.I)
        if match:
            amount = float(match.group(1))
            unit = (match.group(2) or '').upper()
            if unit == 'B':
                funding_amount = amount * 1000
            elif unit == 'M':
                funding_amount = amount
            elif unit == 'K':
                funding_amount = amount / 1000
            else:
                funding_amount = amount

    # 评分逻辑
    if funding_amount >= 100:
        score = 5
    elif funding_amount >= 30:
        score = 4
    elif funding_amount >= 5:
        score = 3
    elif source in ['Y Combinator', 'ProductHunt']:
        score = 3

    product['dark_horse_index'] = score
    return product


def _coerce_score(value, default: int = 2) -> int:
    try:
        score = int(float(str(value)))
    except Exception:
        score = default
    return max(1, min(5, score))


def _ensure_criteria_list(product: dict) -> list:
    criteria = product.get('criteria_met', [])
    if isinstance(criteria, list):
        out = [str(c).strip() for c in criteria if str(c).strip()]
    elif criteria:
        out = [str(criteria).strip()]
    else:
        out = []
    product['criteria_met'] = out
    return out


def _add_criteria(product: dict, tag: str) -> None:
    tag = str(tag or '').strip()
    if not tag:
        return
    criteria = _ensure_criteria_list(product)
    if tag not in criteria:
        criteria.append(tag)
        product['criteria_met'] = criteria


def _parse_funding_amount_musd(funding_text: str) -> float:
    text = str(funding_text or '').strip()
    if not text:
        return 0.0
    match = re.search(r'\$?\s*([\d,.]+)\s*([BMK]?)', text, re.IGNORECASE)
    if not match:
        return 0.0
    try:
        amount = float(match.group(1).replace(',', ''))
    except Exception:
        return 0.0
    unit = (match.group(2) or '').upper()
    if unit == 'B':
        amount *= 1000.0
    elif unit == 'K':
        amount /= 1000.0
    return amount


def _has_strong_supply_signal(product: dict) -> bool:
    funding = _parse_funding_amount_musd(product.get('funding_total', ''))
    if funding >= 30.0:
        return True

    criteria = [str(c).lower() for c in _ensure_criteria_list(product)]
    if any(k in criteria for k in ['funding_signal', 'top_vc_backing', 'founder_background', 'category_creator']):
        return True

    why_matters = str(product.get('why_matters', '')).lower()
    strong_markers = ['sequoia', 'a16z', 'benchmark', 'accel', 'greylock', 'yc', 'y combinator', 'top-tier']
    return any(m in why_matters for m in strong_markers)


def _apply_demand_signals_and_guardrail(
    product: dict,
    *,
    demand_engine,
    llm_score: int,
    override_mode: str,
) -> tuple[int, str]:
    """
    Enrich product with demand signals and apply scoring guardrail.

    Returns:
        (new_score, guardrail_applied)
    """
    if not demand_engine:
        return llm_score, "none"

    result = demand_engine.collect_for_product(product)
    demand_payload = result.get('demand') or {}
    community_verdict = result.get('community_verdict')
    criteria_tags = result.get('criteria_tags') or []

    extra = product.get('extra')
    if not isinstance(extra, dict):
        extra = {}
    extra['demand'] = demand_payload
    product['extra'] = extra

    if isinstance(community_verdict, dict):
        product['community_verdict'] = community_verdict

    for tag in criteria_tags:
        _add_criteria(product, tag)

    has_supply = _has_strong_supply_signal(product)
    new_score, applied, reason = apply_demand_guardrail(
        llm_score=llm_score,
        demand_payload=demand_payload,
        has_strong_supply_signal=has_supply,
        mode=override_mode,
    )

    demand_payload['guardrail_applied'] = applied
    demand_payload['guardrail_reason'] = reason
    extra['demand'] = demand_payload
    product['extra'] = extra

    if applied == 'upgraded':
        _add_criteria(product, 'demand_guardrail_upgraded')
    elif applied == 'downgraded':
        _add_criteria(product, 'demand_guardrail_downgraded')

    return new_score, applied


def save_product(product: dict, dry_run: bool = False):
    """保存产品到相应目录"""
    score = product.get('dark_horse_index', 2)
    week = get_current_week()

    if score >= 4:
        # 黑马
        target_dir = DARK_HORSES_DIR
        target_file = os.path.join(target_dir, f'week_{week}.json')
    else:
        # 潜力股
        target_dir = RISING_STARS_DIR
        target_file = os.path.join(target_dir, f'global_{week}.json')

    if dry_run:
        print(f"  [DRY RUN] Would save to: {target_file}")
        print(f"  {json.dumps(product, ensure_ascii=False, indent=2)}")
        return

    # 确保目录存在
    os.makedirs(target_dir, exist_ok=True)

    # 加载现有数据
    if os.path.exists(target_file):
        with open(target_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
    else:
        products = []

    # 添加新产品
    products.append(product)

    # 保存到分类文件
    with open(target_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f"  Saved to: {target_file}")
    
    # 同时同步到 products_featured.json（前端数据源）
    sync_to_featured(product)


def sync_to_featured(product: dict):
    """
    同步产品到 products_featured.json（前端数据源）
    
    这样发现的产品可以直接在前端显示
    """
    if product.get('dark_horse_index', 0) < 2:
        print(f"  ⏭️ Skip featured (score < 2): {product.get('name')}")
        return
    featured_file = os.path.join(PROJECT_ROOT, 'data', 'products_featured.json')
    
    try:
        # 加载现有数据
        if os.path.exists(featured_file):
            with open(featured_file, 'r', encoding='utf-8') as f:
                featured = json.load(f)
        else:
            featured = []
        
        # 检查是否已存在（website 优先，其次 name）
        existing_websites = {normalize_url(p.get('website', '')) for p in featured}
        def _safe_name_key(value: str) -> str:
            if not value:
                return ""
            try:
                return normalize_name(value) if callable(globals().get("normalize_name")) else "".join(
                    ch for ch in value.lower() if ch.isalnum()
                )
            except Exception:
                return "".join(ch for ch in value.lower() if ch.isalnum())

        existing_names = {_safe_name_key(p.get('name', '')) for p in featured}
        product_domain = normalize_url(product.get('website', ''))
        product_name_key = _safe_name_key(product.get('name', ''))

        if product_domain and product_domain in existing_websites:
            print(f"  📋 Already in featured (domain): {product.get('name')}")
            return
        if (not product_domain) and product_name_key and product_name_key in existing_names:
            print(f"  📋 Already in featured (name): {product.get('name')}")
            return
        
        # 转换字段格式（适配前端）
        apply_country_fields(product, fallback_region_flag=str(product.get('source_region') or product.get('region') or '').strip())
        featured_product = {
            'name': product.get('name'),
            'description': product.get('description'),
            'website': product.get('website'),
            'logo_url': product.get('logo_url') or product.get('logo', ''),
            'categories': [product.get('category', 'other')],
            'dark_horse_index': product.get('dark_horse_index', 2),
            'why_matters': product.get('why_matters', ''),
            'funding_total': product.get('funding_total', ''),
            'region': product.get('region', UNKNOWN_COUNTRY_DISPLAY),
            'country_code': product.get('country_code', UNKNOWN_COUNTRY_CODE),
            'country_name': product.get('country_name', UNKNOWN_COUNTRY_NAME),
            'country_flag': product.get('country_flag', ''),
            'country_display': product.get('country_display', UNKNOWN_COUNTRY_DISPLAY),
            'country_source': product.get('country_source', 'unknown'),
            'source_region': product.get('source_region', ''),
            'source': product.get('source', 'auto_discover'),
            'source_url': product.get('source_url', ''),
            'source_title': product.get('source_title', ''),
            'website_source': product.get('website_source', ''),
            'community_verdict': product.get('community_verdict'),
            'extra': product.get('extra', {}) if isinstance(product.get('extra'), dict) else {},
            'discovered_at': product.get('discovered_at', datetime.utcnow().strftime('%Y-%m-%d')),
            'first_seen': datetime.utcnow().isoformat() + 'Z',
            # 计算分数（用于排序）
            'final_score': product.get('dark_horse_index', 2) * 20,
            'trending_score': product.get('dark_horse_index', 2) * 18,
        }
        
        # 添加到列表开头（最新的在前面）
        featured.insert(0, featured_product)
        
        # 保存
        with open(featured_file, 'w', encoding='utf-8') as f:
            json.dump(featured, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ Synced to featured: {product.get('name')}")
        
    except Exception as e:
        print(f"  ⚠️ Failed to sync to featured: {e}")


def discover_from_source(source_key: str, dry_run: bool = False):
    """从单个渠道发现产品"""
    if source_key not in SOURCES:
        print(f"Unknown source: {source_key}")
        return

    config = SOURCES[source_key]
    print(f"\n{'='*50}")
    print(f"  Discovering from: {config['name']} {config['region']}")
    print(f"{'='*50}")

    existing = load_existing_products()

    # 使用 Perplexity 发现产品
    products = fetch_with_perplexity(config)

    new_count = 0
    for product in products:
        if is_duplicate(product.get('name', ''), product.get('website', ''), existing):
            print(f"  Skip duplicate: {product.get('name')}")
            continue

        # 如果评分缺失，使用规则评分
        if 'dark_horse_index' not in product:
            product = analyze_and_score(product)

        save_product(product, dry_run)
        new_count += 1
        existing.add(product.get('name', '').lower())

    print(f"\n  Found {new_count} new products from {config['name']}")


def discover_all(dry_run: bool = False, tier: int = None):
    """从所有渠道发现产品"""
    for source_key, config in SOURCES.items():
        if tier and config.get('tier', 1) > tier:
            continue
        discover_from_source(source_key, dry_run)


# ============================================
# 新增：基于地区的 Perplexity 搜索发现
# ============================================

def discover_by_region(region_key: str, dry_run: bool = False, product_type: str = "mixed") -> dict:
    """
    使用 Perplexity Search API 按地区发现 AI 产品（增强版：带质量过滤和关键词轮换）

    Args:
        region_key: 地区代码 (us/cn/eu/jp/kr/sea)
        dry_run: 预览模式
        product_type: 产品类型 (software/hardware/mixed)

    Returns:
        统计信息
    """
    if region_key not in REGION_CONFIG:
        print(f"❌ Unknown region: {region_key}")
        print(f"   Available: {', '.join(REGION_CONFIG.keys())}")
        return {"error": f"Unknown region: {region_key}"}

    config = REGION_CONFIG[region_key]
    region_name = config['name']
    search_engine = config['search_engine']
    current_provider = get_provider_for_region(region_key)

    # 使用关键词轮换（支持产品类型）
    keyword_stats = load_keyword_yield_stats()
    keywords = get_keywords_for_today(region_key, product_type)
    keywords = apply_keyword_limit(region_key, keywords)
    if AUTO_DISCOVER_BUDGET_MODE == "adaptive":
        keywords = rank_keywords_by_yield(region_key, keywords, keyword_stats)

    keyword_limit = 0
    if region_key == "cn" and MAX_KEYWORDS_CN > 0:
        keyword_limit = MAX_KEYWORDS_CN
    elif MAX_KEYWORDS_DEFAULT > 0:
        keyword_limit = MAX_KEYWORDS_DEFAULT

    type_label = {"software": "💻 软件", "hardware": "🔧 硬件", "mixed": "📊 混合(40%硬件+60%软件)"}.get(product_type, "混合")

    print(f"\n{'='*60}")
    print(f"  🌍 Discovering AI Products: {region_name}")
    print(f"  📡 Search Engine: {search_engine}")
    print(f"  🤖 Provider: {current_provider}")
    print(f"  📦 Product Type: {type_label}")
    print(f"  💸 Budget Mode: {AUTO_DISCOVER_BUDGET_MODE}")
    print(f"  🧪 Analyze Gate: {'on' if AUTO_DISCOVER_ENABLE_ANALYZE_GATE else 'off'}")
    print(f"  🔑 Keywords: {len(keywords)} queries (day {datetime.now().weekday()})")
    if keyword_limit:
        print(f"  🧯 Keyword limit: {keyword_limit}")
    print(f"{'='*60}")

    # 使用增强去重检查器
    featured_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "products_featured.json")
    existing_products = []
    if os.path.exists(featured_path):
        with open(featured_path, 'r', encoding='utf-8') as f:
            existing_products = json.load(f)
    
    dedup_checker = EnhancedDuplicateChecker(existing_products)
    all_products = []
    quality_rejections = []
    demand_engine = None
    demand_processed = 0
    demand_upgraded = 0
    demand_downgraded = 0

    if ENABLE_DEMAND_SIGNALS and HAS_DEMAND_SIGNALS:
        demand_engine = DemandSignalEngine(
            window_days=DEMAND_WINDOW_DAYS,
            strict_x_official=True,
            official_handles_path=PRODUCT_OFFICIAL_HANDLES_FILE,
            perplexity_api_key=PERPLEXITY_API_KEY,
            github_token=GITHUB_TOKEN,
            github_max_star_pages=DEMAND_GITHUB_MAX_STAR_PAGES,
        )

    stats = {
        "region": region_key,
        "region_name": region_name,
        "search_results": 0,
        "products_found": 0,
        "products_saved": 0,
        "dark_horses": 0,
        "rising_stars": 0,
        "duplicates_skipped": 0,
        "quality_rejections": 0,
        "demand_processed": 0,
        "demand_upgraded": 0,
        "demand_downgraded": 0,
    }

    deferred_keywords: List[Tuple[str, str, List[dict], str]] = []
    region_flag_map = {
        'us': '🇺🇸', 'cn': '🇨🇳', 'eu': '🇪🇺',
        'jp': '🇯🇵🇰🇷', 'kr': '🇰🇷', 'sea': '🇸🇬'
    }
    region_flag = region_flag_map.get(region_key, '🌍')

    def _run_extract_for_keyword(
        keyword: str,
        keyword_type: str,
        search_results: List[dict],
        *,
        bypass_gate: bool = False,
    ) -> Tuple[int, int, int]:
        nonlocal demand_processed, demand_upgraded, demand_downgraded
        keyword_saved = 0
        keyword_dark_horses = 0
        current_provider = get_provider_for_region(region_key)

        if AUTO_DISCOVER_ENABLE_ANALYZE_GATE and not bypass_gate:
            analyze_ok, analyze_reason = should_analyze_search_results(search_results, keyword)
            if not analyze_ok:
                deferred_keywords.append((keyword, keyword_type, search_results, analyze_reason))
                print(f"    ⏭️ Analyze gate skipped: {analyze_reason}")
                return 0, 0, 0

        search_text = build_search_text(search_results)
        if not search_text.strip():
            return 0, 0, 0

        print(f"    📊 Extracting products with {current_provider}...")
        products = analyze_with_provider(
            search_text,
            "extract",
            region_key,
            region_flag,
            product_type=keyword_type
        )
        if not isinstance(products, list):
            products = []

        print(f"    ✅ Extracted {len(products)} products")
        stats["products_found"] += len(products)

        for product in products:
            name = product.get('name', '')
            if not name:
                continue

            is_dup, dup_reason = dedup_checker.is_duplicate(product)
            if is_dup:
                stats["duplicates_skipped"] += 1
                print(f"    ⏭️ Skip duplicate: {dup_reason}")
                continue

            attach_source_url(product, search_results)

            if current_provider == "glm":
                xref_valid, xref_reason = validate_against_search_results(
                    product, search_results
                )
                if not xref_valid:
                    stats["quality_rejections"] += 1
                    quality_rejections.append({"name": name, "reason": xref_reason})
                    print(f"    🚫 Hallucination filter: {name} ({xref_reason})")
                    continue

            is_hardware = (
                keyword_type == "hardware" or
                product.get("category") == "hardware" or
                product.get("is_hardware", False)
            )
            if is_hardware:
                product.setdefault("category", "hardware")
                product["is_hardware"] = True
            if is_hardware and USE_MODULAR_PROMPTS:
                is_valid, reason = validate_hardware_product(product)
            else:
                is_valid, reason = validate_product(product)
            if not is_valid:
                stats["quality_rejections"] += 1
                quality_rejections.append({"name": name, "reason": reason})
                print(f"    ❌ Quality fail: {name} ({reason})")
                continue

            product['source_region'] = region_flag
            product['discovered_at'] = datetime.utcnow().strftime('%Y-%m-%d')
            product['discovery_method'] = f'{current_provider}_search'
            product['search_keyword'] = keyword
            apply_country_fields(product, fallback_region_flag=region_flag)

            score = product.get('dark_horse_index')
            if score is None:
                print(f"    🎯 Fallback scoring: {product.get('name')}...")
                product = analyze_and_score(product)
                score = product.get('dark_horse_index', 2)
            score = _coerce_score(score, default=2)
            product['dark_horse_index'] = score

            guardrail_applied = "none"
            if demand_engine and demand_processed < max(DEMAND_MAX_PRODUCTS_PER_RUN, 0):
                try:
                    score, guardrail_applied = _apply_demand_signals_and_guardrail(
                        product,
                        demand_engine=demand_engine,
                        llm_score=score,
                        override_mode=DEMAND_OVERRIDE_MODE,
                    )
                    demand_processed += 1
                    if guardrail_applied == 'upgraded':
                        demand_upgraded += 1
                    elif guardrail_applied == 'downgraded':
                        demand_downgraded += 1
                    product['dark_horse_index'] = score
                    print(f"    🧭 Demand guardrail: {guardrail_applied} (score={score})")
                except Exception as e:
                    print(f"    ⚠️ Demand signal failed: {e}")
            elif demand_engine and DEMAND_MAX_PRODUCTS_PER_RUN >= 0 and demand_processed >= DEMAND_MAX_PRODUCTS_PER_RUN:
                print("    ⏭️ Demand skipped: per-run limit reached")

            criteria = product.get('criteria_met', [])
            print(f"    📈 Score: {score}/5 | Criteria: {criteria}")

            website = product.get('website', '')
            if not dry_run and website and website.lower() != 'unknown':
                if not verify_url_exists(website, timeout=5):
                    print(f"    ⚠️ URL not accessible: {website}")
                    product['needs_verification'] = True

            save_product(product, dry_run)
            stats["products_saved"] += 1
            keyword_saved += 1

            if score >= 4:
                stats["dark_horses"] += 1
                keyword_dark_horses += 1
            else:
                stats["rising_stars"] += 1

            dedup_checker.add_product(product)
            all_products.append(product)

        return keyword_saved, keyword_dark_horses, len(products)

    # 对每个关键词进行搜索
    for i, keyword in enumerate(keywords, 1):
        print(f"\n  [{i}/{len(keywords)}] Searching: {keyword[:50]}...")
        keyword_type = resolve_keyword_type(keyword, region_key, product_type)

        search_results = search_with_provider(keyword, region_key, search_engine)
        stats["search_results"] += len(search_results)
        if not search_results:
            update_keyword_yield_stats(
                keyword_stats,
                region_key=region_key,
                keyword=keyword,
                searches=1,
            )
            continue

        saved_count, dark_count, extracted_count = _run_extract_for_keyword(
            keyword,
            keyword_type,
            search_results,
            bypass_gate=False,
        )
        update_keyword_yield_stats(
            keyword_stats,
            region_key=region_key,
            keyword=keyword,
            searches=1,
            extracted=extracted_count,
            saved=saved_count,
            dark_horses=dark_count,
        )

        current_provider = get_provider_for_region(region_key)
        if current_provider == "glm" and GLM_KEYWORD_DELAY > 0 and i < len(keywords):
            print(f"  ⏳ GLM cooldown: sleeping {GLM_KEYWORD_DELAY:.1f}s")
            time.sleep(GLM_KEYWORD_DELAY)

    # Analyze gate 保底回放：当本轮产出偏低时，回放被 gate 拦截的关键词
    min_expected_saves = max(1, len(keywords) // 4)
    if AUTO_DISCOVER_ENABLE_ANALYZE_GATE and deferred_keywords and stats["products_saved"] < min_expected_saves:
        print(f"\n  ♻️ Replaying deferred keywords due to low yield ({stats['products_saved']} < {min_expected_saves})")
        for keyword, keyword_type, search_results, reason in deferred_keywords:
            print(f"  ↩ Replaying: {keyword[:50]}... (gate reason: {reason})")
            saved_count, dark_count, extracted_count = _run_extract_for_keyword(
                keyword,
                keyword_type,
                search_results,
                bypass_gate=True,
            )
            update_keyword_yield_stats(
                keyword_stats,
                region_key=region_key,
                keyword=keyword,
                searches=0,
                extracted=extracted_count,
                saved=saved_count,
                dark_horses=dark_count,
            )

    flush_keyword_yield_stats(keyword_stats)

    # 打印统计
    print(f"\n{'='*60}")
    print(f"  📊 Summary for {region_name}")
    print(f"{'='*60}")
    print(f"  Search Results: {stats['search_results']}")
    print(f"  Products Found: {stats['products_found']}")
    print(f"  Products Saved: {stats['products_saved']}")
    print(f"  🏇 Dark Horses (4-5): {stats['dark_horses']}")
    print(f"  ⭐ Rising Stars (2-3): {stats['rising_stars']}")
    print(f"  Duplicates Skipped: {stats['duplicates_skipped']}")
    print(f"  Quality Rejections: {stats['quality_rejections']}")
    if demand_engine:
        stats["demand_processed"] = demand_processed
        stats["demand_upgraded"] = demand_upgraded
        stats["demand_downgraded"] = demand_downgraded
        print(
            "  Demand Signals: "
            f"processed={demand_processed}, upgraded={demand_upgraded}, downgraded={demand_downgraded}"
        )

    if quality_rejections:
        print(f"\n  Top rejection reasons:")
        reason_counts = {}
        for rej in quality_rejections:
            reason = rej['reason']
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1])[:3]:
            print(f"    - {reason}: {count}")

    return stats


def discover_all_regions(dry_run: bool = False, product_type: str = "mixed") -> dict:
    """
    带配额系统的全球 AI 产品发现

    目标配额：
    - 黑马 (4-5分): 5 个/天
    - 潜力股 (2-3分): 10 个/天
    
    Args:
        dry_run: 预览模式
        product_type: 产品类型 (software/hardware/mixed)

    Returns:
        详细的发现报告
    """
    start_time = datetime.now()
    today_str = start_time.strftime('%Y-%m-%d')

    type_label = {"software": "💻 软件", "hardware": "🔧 硬件", "mixed": "📊 混合(40%硬件+60%软件)"}.get(product_type, "混合")
    
    print("\n" + "═"*70)
    print(f"  🌍 Daily AI Product Discovery - {today_str}")
    print("═"*70)
    print(f"  📊 Quota: {DAILY_QUOTA['dark_horses']} Dark Horses + {DAILY_QUOTA['rising_stars']} Rising Stars")
    print(f"  📦 Product Type: {type_label}")
    print(f"  🔄 Max Attempts: {MAX_ATTEMPTS} rounds")
    print(f"  💸 Budget Mode: {AUTO_DISCOVER_BUDGET_MODE}")
    print(f"  🧪 Analyze Gate: {'on' if AUTO_DISCOVER_ENABLE_ANALYZE_GATE else 'off'}")
    print(f"  🛟 Quality Fallback: {'on' if AUTO_DISCOVER_QUALITY_FALLBACK else 'off'}")
    print(f"  📅 Keyword Pool: Day {datetime.now().weekday()} (0=Mon)")
    glm_status = 'enabled' if (ZHIPU_API_KEY and USE_GLM_FOR_CN) else 'disabled'
    pplx_status = 'enabled' if PERPLEXITY_API_KEY else 'missing key'
    print(f"  🤖 Provider: Perplexity ({pplx_status}) | GLM-cn ({glm_status})")
    print("═"*70)

    # 初始化跟踪
    found = {"dark_horses": 0, "rising_stars": 0}
    region_yield = {k: 0 for k in REGION_CONFIG.keys()}
    provider_stats = {"perplexity": 0, "glm": 0}
    duplicates_skipped = 0
    quality_rejections = []
    attempts = 0
    unique_domains = set()
    demand_processed = 0
    demand_upgraded = 0
    demand_downgraded = 0
    demand_engine = None
    keyword_stats = load_keyword_yield_stats()

    featured_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "products_featured.json")
    existing_products = []
    if os.path.exists(featured_path):
        with open(featured_path, 'r', encoding='utf-8') as f:
            existing_products = json.load(f)

    dedup_checker = EnhancedDuplicateChecker(existing_products)
    if ENABLE_DEMAND_SIGNALS and HAS_DEMAND_SIGNALS:
        demand_engine = DemandSignalEngine(
            window_days=DEMAND_WINDOW_DAYS,
            strict_x_official=True,
            official_handles_path=PRODUCT_OFFICIAL_HANDLES_FILE,
            perplexity_api_key=PERPLEXITY_API_KEY,
            github_token=GITHUB_TOKEN,
            github_max_star_pages=DEMAND_GITHUB_MAX_STAR_PAGES,
        )

    region_flag_map = {
        'us': '🇺🇸', 'cn': '🇨🇳', 'eu': '🇪🇺',
        'jp': '🇯🇵🇰🇷', 'kr': '🇰🇷', 'sea': '🇸🇬'
    }
    keyword_pools: Dict[str, List[str]] = {}
    keyword_cursors = {k: 0 for k in REGION_CONFIG.keys()}
    prev_round_region_saved = {k: 1 for k in REGION_CONFIG.keys()}

    def quotas_met():
        return (found["dark_horses"] >= DAILY_QUOTA["dark_horses"] and
                found["rising_stars"] >= DAILY_QUOTA["rising_stars"])

    def get_category(score):
        return "dark_horses" if score >= 4 else "rising_stars"

    def get_keyword_pool(region_key: str) -> List[str]:
        if region_key in keyword_pools:
            return keyword_pools[region_key]
        pool = get_keywords_for_today(region_key, product_type)
        pool = apply_keyword_limit(region_key, pool)
        if AUTO_DISCOVER_BUDGET_MODE == "adaptive":
            pool = rank_keywords_by_yield(region_key, pool, keyword_stats)
        keyword_pools[region_key] = pool
        return pool

    def select_keywords_for_round(region_key: str, attempt: int) -> List[str]:
        pool = get_keyword_pool(region_key)
        if AUTO_DISCOVER_BUDGET_MODE == "legacy":
            return pool[:2] if attempt > 1 else list(pool)

        cursor = keyword_cursors.get(region_key, 0)
        if cursor >= len(pool):
            return []
        if attempt == 1:
            take = AUTO_DISCOVER_ROUND1_KEYWORDS
        else:
            if prev_round_region_saved.get(region_key, 0) <= 0:
                return []
            take = AUTO_DISCOVER_ROUND_EXPAND_STEP
        end = min(len(pool), cursor + max(1, take))
        selected = pool[cursor:end]
        keyword_cursors[region_key] = end
        return selected

    def process_keyword(
        *,
        region_key: str,
        search_engine: str,
        keyword: str,
        keyword_type: str,
        quota_remaining: Dict[str, int],
        deferred_queue: List[Tuple[str, str, List[dict], str]],
        search_results_override: Optional[List[dict]] = None,
        bypass_gate: bool = False,
    ) -> int:
        nonlocal duplicates_skipped, demand_processed, demand_upgraded, demand_downgraded

        search_requests = 0
        if search_results_override is None:
            search_results = search_with_provider(keyword, region_key, search_engine)
            search_requests = 1
        else:
            search_results = list(search_results_override)

        if not search_results:
            update_keyword_yield_stats(
                keyword_stats,
                region_key=region_key,
                keyword=keyword,
                searches=search_requests,
            )
            return 0

        if AUTO_DISCOVER_ENABLE_ANALYZE_GATE and not bypass_gate:
            analyze_ok, analyze_reason = should_analyze_search_results(search_results, keyword)
            if not analyze_ok:
                deferred_queue.append((keyword, keyword_type, search_results, analyze_reason))
                print(f"    ⏭️ Analyze gate skipped: {analyze_reason}")
                update_keyword_yield_stats(
                    keyword_stats,
                    region_key=region_key,
                    keyword=keyword,
                    searches=search_requests,
                )
                return 0

        search_text = build_search_text(search_results)
        if not search_text.strip():
            update_keyword_yield_stats(
                keyword_stats,
                region_key=region_key,
                keyword=keyword,
                searches=search_requests,
            )
            return 0

        region_flag = region_flag_map.get(region_key, '🌍')
        products = analyze_with_provider(
            search_text,
            "extract",
            region_key,
            region_flag,
            quota_remaining,
            product_type=keyword_type
        )
        if not isinstance(products, list):
            products = []

        print(f"    📦 Extracted: {len(products)} candidates")
        saved_count = 0
        dark_count = 0
        current_provider = get_provider_for_region(region_key)

        for product in products:
            if quotas_met():
                break

            name = product.get('name', '')
            if not name:
                continue

            is_dup, dup_reason = dedup_checker.is_duplicate(product)
            if is_dup:
                duplicates_skipped += 1
                print(f"    ⏭️ Skip: {dup_reason}")
                continue

            attach_source_url(product, search_results)

            if current_provider == "glm":
                xref_valid, xref_reason = validate_against_search_results(product, search_results)
                if not xref_valid:
                    quality_rejections.append({"name": name, "reason": xref_reason})
                    print(f"    🚫 Hallucination filter: {name} ({xref_reason})")
                    continue

            is_hardware = (
                keyword_type == "hardware" or
                product.get("category") == "hardware" or
                product.get("is_hardware", False)
            )
            if is_hardware:
                product.setdefault("category", "hardware")
                product["is_hardware"] = True
            if is_hardware and USE_MODULAR_PROMPTS:
                is_valid, reason = validate_hardware_product(product)
            else:
                is_valid, reason = validate_product(product)
            if not is_valid:
                quality_rejections.append({"name": name, "reason": reason})
                print(f"    ❌ Quality fail: {name} ({reason})")
                continue

            score = product.get('dark_horse_index')
            if score is None:
                product = analyze_and_score(product)
                score = product.get('dark_horse_index', 2)
            score = _coerce_score(score, default=2)
            product['dark_horse_index'] = score

            guardrail_applied = "none"
            if demand_engine and demand_processed < max(DEMAND_MAX_PRODUCTS_PER_RUN, 0):
                try:
                    score, guardrail_applied = _apply_demand_signals_and_guardrail(
                        product,
                        demand_engine=demand_engine,
                        llm_score=score,
                        override_mode=DEMAND_OVERRIDE_MODE,
                    )
                    demand_processed += 1
                    if guardrail_applied == 'upgraded':
                        demand_upgraded += 1
                    elif guardrail_applied == 'downgraded':
                        demand_downgraded += 1
                    product['dark_horse_index'] = score
                    print(f"    🧭 Demand guardrail: {guardrail_applied} (score={score})")
                except Exception as e:
                    print(f"    ⚠️ Demand signal failed: {e}")
            elif demand_engine and DEMAND_MAX_PRODUCTS_PER_RUN >= 0 and demand_processed >= DEMAND_MAX_PRODUCTS_PER_RUN:
                print("    ⏭️ Demand skipped: per-run limit reached")

            category = get_category(score)
            if found[category] >= DAILY_QUOTA[category]:
                print(f"    ⏭️ {category} quota full, skip: {name}")
                continue
            if region_yield[region_key] >= REGION_MAX.get(region_key, 3):
                print(f"    ⏭️ Region max reached, skip: {name}")
                continue

            product['source_region'] = region_flag
            product['discovered_at'] = datetime.utcnow().strftime('%Y-%m-%d')
            product['discovery_method'] = f'{current_provider}_search'
            product['search_keyword'] = keyword
            apply_country_fields(product, fallback_region_flag=region_flag)
            save_product(product, dry_run)

            found[category] += 1
            region_yield[region_key] += 1
            provider_stats[current_provider] = provider_stats.get(current_provider, 0) + 1
            dedup_checker.add_product(product)
            saved_count += 1
            if category == "dark_horses":
                dark_count += 1

            website = product.get('website', '')
            if website:
                unique_domains.add(normalize_url(website))

            status_icon = "🦄" if category == "dark_horses" else "⭐"
            print(f"    {status_icon} SAVED: {name} (score={score}, {category}, {current_provider})")

        update_keyword_yield_stats(
            keyword_stats,
            region_key=region_key,
            keyword=keyword,
            searches=search_requests,
            extracted=len(products),
            saved=saved_count,
            dark_horses=dark_count,
        )
        return saved_count

    # 主发现循环
    while not quotas_met() and attempts < MAX_ATTEMPTS:
        attempts += 1
        print(f"\n{'─'*70}")
        print(f"  🔄 Round {attempts}/{MAX_ATTEMPTS}")
        print(f"  Progress: DH {found['dark_horses']}/{DAILY_QUOTA['dark_horses']} | RS {found['rising_stars']}/{DAILY_QUOTA['rising_stars']}")
        print(f"{'─'*70}")

        round_region_saved = {k: 0 for k in REGION_CONFIG.keys()}
        region_order = get_region_order()

        for region_key in region_order:
            if region_yield[region_key] >= REGION_MAX.get(region_key, 3):
                print(f"\n  ⏭️ Skip {region_key}: region max reached ({region_yield[region_key]})")
                continue
            if quotas_met():
                break

            config = REGION_CONFIG[region_key]
            region_name = config['name']
            search_engine = config['search_engine']
            current_provider = get_provider_for_region(region_key)
            keywords_this_round = select_keywords_for_round(region_key, attempts)
            if not keywords_this_round:
                print(f"\n  ⏭️ {region_name} | no keywords in this round")
                continue

            print(f"\n  📍 {region_name} | Provider: {current_provider} | Keywords: {len(keywords_this_round)}")
            quota_remaining = {
                "dark_horses": DAILY_QUOTA["dark_horses"] - found["dark_horses"],
                "rising_stars": DAILY_QUOTA["rising_stars"] - found["rising_stars"],
            }
            deferred_keywords: List[Tuple[str, str, List[dict], str]] = []

            for idx, keyword in enumerate(keywords_this_round, 1):
                if quotas_met():
                    break
                print(f"\n    🔍 Searching: {keyword[:50]}...")
                keyword_type = resolve_keyword_type(keyword, region_key, product_type)
                saved = process_keyword(
                    region_key=region_key,
                    search_engine=search_engine,
                    keyword=keyword,
                    keyword_type=keyword_type,
                    quota_remaining=quota_remaining,
                    deferred_queue=deferred_keywords,
                )
                round_region_saved[region_key] += saved

                if current_provider == "glm" and GLM_KEYWORD_DELAY > 0 and idx < len(keywords_this_round):
                    print(f"    ⏳ GLM cooldown: sleeping {GLM_KEYWORD_DELAY:.1f}s")
                    time.sleep(GLM_KEYWORD_DELAY)

            if AUTO_DISCOVER_ENABLE_ANALYZE_GATE and deferred_keywords and round_region_saved[region_key] == 0 and not quotas_met():
                print(f"    ♻️ Replaying deferred keywords for {region_key} (no saves in round)")
                for keyword, keyword_type, cached_results, reason in deferred_keywords:
                    if quotas_met():
                        break
                    print(f"    ↩ Replaying: {keyword[:50]}... (gate reason: {reason})")
                    saved = process_keyword(
                        region_key=region_key,
                        search_engine=search_engine,
                        keyword=keyword,
                        keyword_type=keyword_type,
                        quota_remaining=quota_remaining,
                        deferred_queue=[],
                        search_results_override=cached_results,
                        bypass_gate=True,
                    )
                    round_region_saved[region_key] += saved

        prev_round_region_saved = round_region_saved

    if (
        AUTO_DISCOVER_BUDGET_MODE == "adaptive"
        and AUTO_DISCOVER_QUALITY_FALLBACK
        and not quotas_met()
    ):
        print("\n  🛟 Quality fallback: quotas unmet after adaptive rounds, replaying remaining keywords in legacy mode")
        for region_key in get_region_order():
            if quotas_met():
                break
            if region_yield[region_key] >= REGION_MAX.get(region_key, 3):
                continue
            config = REGION_CONFIG[region_key]
            search_engine = config['search_engine']
            pool = get_keyword_pool(region_key)
            cursor = keyword_cursors.get(region_key, 0)
            remaining = pool[cursor:]
            if not remaining:
                continue
            quota_remaining = {
                "dark_horses": DAILY_QUOTA["dark_horses"] - found["dark_horses"],
                "rising_stars": DAILY_QUOTA["rising_stars"] - found["rising_stars"],
            }
            print(f"  ↪ {region_key}: fallback keywords={len(remaining)}")
            for keyword in remaining:
                if quotas_met():
                    break
                keyword_type = resolve_keyword_type(keyword, region_key, product_type)
                process_keyword(
                    region_key=region_key,
                    search_engine=search_engine,
                    keyword=keyword,
                    keyword_type=keyword_type,
                    quota_remaining=quota_remaining,
                    deferred_queue=[],
                )
            keyword_cursors[region_key] = len(pool)

    flush_keyword_yield_stats(keyword_stats)

    # ═══════════════════════════════════════════════════════════════════
    # 生成详细报告
    # ═══════════════════════════════════════════════════════════════════
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    dh_status = "✅" if found["dark_horses"] >= DAILY_QUOTA["dark_horses"] else "⚠️"
    rs_status = "✅" if found["rising_stars"] >= DAILY_QUOTA["rising_stars"] else "⚠️"

    print("\n" + "═"*70)
    print(f"  Daily Discovery Report - {today_str}")
    print("═"*70)
    print(f"  Quotas:     Dark Horses: {found['dark_horses']}/{DAILY_QUOTA['dark_horses']} {dh_status}  Rising Stars: {found['rising_stars']}/{DAILY_QUOTA['rising_stars']} {rs_status}")
    print(f"  Attempts:   {attempts} rounds")
    print(f"  Duration:   {duration:.1f} seconds")
    print(f"  Regions:    {', '.join(f'{k}: {v}' for k, v in region_yield.items() if v > 0)}")
    print(f"  Providers:  {', '.join(f'{k}: {v}' for k, v in provider_stats.items() if v > 0)}")
    print(f"  Total saved: {found['dark_horses'] + found['rising_stars']}")
    print(f"  Duplicates skipped: {duplicates_skipped}")
    print(f"  Quality rejections: {len(quality_rejections)}")
    if demand_engine:
        print(
            "  Demand signals: "
            f"processed={demand_processed}, upgraded={demand_upgraded}, downgraded={demand_downgraded}"
        )

    if quality_rejections:
        print("\n  Quality rejection reasons:")
        reason_counts = {}
        for rej in quality_rejections:
            reason = rej['reason']
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"    - {reason}: {count}")

    print("═"*70)

    # 返回报告数据
    return {
        "date": today_str,
        "found": found,
        "quota": DAILY_QUOTA,
        "attempts": attempts,
        "region_yield": region_yield,
        "provider_stats": provider_stats,
        "unique_domains": len(unique_domains),
        "duplicates_skipped": duplicates_skipped,
        "quality_rejections": len(quality_rejections),
        "demand_processed": demand_processed,
        "demand_upgraded": demand_upgraded,
        "demand_downgraded": demand_downgraded,
        "duration_seconds": duration,
        "quotas_met": quotas_met(),
    }


def test_perplexity():
    """测试 Perplexity Search API 连接"""
    print("\n" + "="*60)
    print("  🔍 Testing Perplexity Search API")
    print("="*60)

    # 检查 API Key
    if not PERPLEXITY_API_KEY:
        print("\n  ❌ PERPLEXITY_API_KEY not set")
        print("  Set it with: export PERPLEXITY_API_KEY=pplx_xxx")
        return

    print(f"  API Key: {PERPLEXITY_API_KEY[:12]}...")
    print(f"  Model: {PERPLEXITY_MODEL}")
    # 尝试导入新模块
    try:
        from utils.perplexity_client import PerplexityClient
        client = PerplexityClient()
        print(f"  Client Status: {client.get_status()}")
    except ImportError as e:
        print(f"  ⚠️ SDK not installed: {e}")
        print("  Install with: pip install perplexityai")

    # 测试搜索
    test_queries = [
        ("us", "AI startup funding 2026"),
        ("cn", "AI融资 2026"),
    ]

    for region, query in test_queries:
        print(f"\n  📍 Testing region={region}: {query}")
        results = perplexity_search(query, count=3, region=region)

        if results:
            print(f"  ✅ Found {len(results)} results")
            for i, r in enumerate(results[:2], 1):
                title = r.get('title', 'No Title')[:50]
                url = r.get('url', 'N/A')[:60]
                print(f"    {i}. {title}...")
                print(f"       URL: {url}")
        else:
            print(f"  ⚠️ No results")

    print("\n  ✅ Perplexity test completed!")


def test_glm():
    """测试 GLM (智谱) 联网搜索 API 连接"""
    print("\n" + "="*60)
    print("  🔍 Testing GLM (智谱) Web Search API")
    print("="*60)

    # 检查 API Key
    if not ZHIPU_API_KEY:
        print("\n  ❌ ZHIPU_API_KEY not set")
        print("  Set it with: export ZHIPU_API_KEY=your-api-key")
        return

    print(f"  API Key: {ZHIPU_API_KEY[:12]}...")
    print(f"  Model: {GLM_MODEL}")
    print(f"  Search Engine: {GLM_SEARCH_ENGINE}")
    print(f"  USE_GLM_FOR_CN: {USE_GLM_FOR_CN}")

    # 尝试导入模块
    try:
        from utils.glm_client import GLMClient
        client = GLMClient()
        print(f"  Client Status: {client.get_status()}")
    except ImportError as e:
        print(f"  ⚠️ glm_client module not found: {e}")
        print("  Make sure utils/glm_client.py exists")
        print("  Install SDK with: pip install zhipuai")
        return

    if not client.is_available():
        print("\n  ❌ GLM client not available")
        print("  Install SDK with: pip install zhipuai")
        return

    # 测试搜索
    test_queries = [
        "AI创业公司 融资 2026",
        "AI芯片 独角兽",
    ]

    for query in test_queries:
        print(f"\n  📍 Testing: {query}")
        results = glm_search(query, count=3)

        if results:
            print(f"  ✅ Found {len(results)} results")
            for i, r in enumerate(results[:2], 1):
                title = r.get('title', 'No Title')[:50]
                url = r.get('url', 'N/A')[:60]
                print(f"    {i}. {title}...")
                print(f"       URL: {url}")
        else:
            print(f"  ⚠️ No results")

    print("\n  ✅ GLM test completed!")


def test_provider_routing():
    """测试 Provider 路由逻辑"""
    print("\n" + "="*60)
    print("  🔀 Testing Provider Routing")
    print("="*60)

    regions = ['us', 'cn', 'eu', 'jp', 'kr', 'sea']

    print("\n  Provider routing results:")
    print(f"  ZHIPU_API_KEY set: {bool(ZHIPU_API_KEY)}")
    print(f"  USE_GLM_FOR_CN: {USE_GLM_FOR_CN}")
    print()

    for region in regions:
        provider = get_provider_for_region(region)
        icon = "🇨🇳" if provider == "glm" else "🌐"
        print(f"    {region:5} → {provider:12} {icon}")

    print("\n  ✅ Routing test completed!")


def setup_schedule():
    """设置定时任务（macOS/Linux）"""
    script_path = os.path.abspath(__file__)

    # 生成 cron 任务
    cron_line = f"0 9 * * * cd {PROJECT_ROOT} && /usr/bin/python3 {script_path} >> /tmp/auto_discover.log 2>&1"

    print("\n设置定时任务（每天早上9点运行）：")
    print("-" * 50)
    print("运行以下命令添加 cron 任务：")
    print(f"\n  (crontab -l 2>/dev/null; echo \"{cron_line}\") | crontab -")
    print("\n或者使用 launchd (macOS)：")
    print(f"  创建 ~/Library/LaunchAgents/com.weeklyai.autodiscover.plist")


def main():
    parser = argparse.ArgumentParser(
        description='自动发现全球 AI 产品 (v2.0 - Perplexity Search)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法：
  # 按地区搜索（推荐，使用 Perplexity Search）
  python tools/auto_discover.py --region us      # 搜索美国 AI 产品
  python tools/auto_discover.py --region cn      # 搜索中国 AI 产品
  python tools/auto_discover.py --region eu      # 搜索欧洲 AI 产品
  python tools/auto_discover.py --region jp      # 搜索日韩 AI 产品
  python tools/auto_discover.py --region sea     # 搜索东南亚 AI 产品
  python tools/auto_discover.py --region all     # 搜索所有地区

  # 按渠道搜索（旧方式）
  python tools/auto_discover.py --source 36kr    # 从 36氪 发现
  python tools/auto_discover.py --source producthunt

  # 其他选项
  python tools/auto_discover.py --dry-run        # 预览不保存
"""
    )

    # 新增：地区参数
    parser.add_argument('--region', '-r',
                        choices=['us', 'cn', 'eu', 'jp', 'sea', 'all'],
                        help='按地区搜索 (us/cn/eu/jp/sea/all)')
    
    # 新增：产品类型参数
    parser.add_argument('--type', '-T',
                        choices=['software', 'hardware', 'mixed'],
                        default='mixed',
                        help='产品类型 (software/hardware/mixed，默认 mixed=40%%硬件+60%%软件)')

    # 原有参数
    parser.add_argument('--source', '-s', help='指定渠道 (e.g., 36kr, producthunt)')
    parser.add_argument('--tier', '-t', type=int, choices=[1, 2, 3], help='只运行指定级别的渠道')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不保存')
    parser.add_argument('--schedule', action='store_true', help='设置定时任务')
    parser.add_argument('--list-sources', action='store_true', help='列出所有渠道')
    parser.add_argument('--list-regions', action='store_true', help='列出所有地区')
    parser.add_argument('--list-keywords', action='store_true', help='列出关键词（按类型）')
    parser.add_argument('--test-perplexity', action='store_true', help='测试 Perplexity Search API')
    parser.add_argument('--test-glm', action='store_true', help='测试 GLM (智谱) 联网搜索 API')
    parser.add_argument('--test-routing', action='store_true', help='测试 Provider 路由逻辑')
    parser.add_argument('--no-lock', action='store_true', help='禁用单实例锁（不建议）')

    args = parser.parse_args()

    # 测试功能
    if args.test_perplexity:
        test_perplexity()
        return

    if args.test_glm:
        test_glm()
        return

    if args.test_routing:
        test_provider_routing()
        return

    # 列表功能
    if args.list_sources:
        print("\n可用渠道：")
        print("-" * 60)
        for key, config in SOURCES.items():
            print(f"  {key:15} {config['region']} {config['name']:20} Tier {config.get('tier', 1)}")
        return

    if args.list_regions:
        print("\n可用地区：")
        print("-" * 60)
        for key, config in REGION_CONFIG.items():
            print(f"  {key:5} {config['name']:15} 权重:{config['weight']:2}% 搜索引擎:{config['search_engine']}")
        return
    
    if args.list_keywords:
        region = args.region or 'us'
        print(f"\n关键词列表 (地区: {region})：")
        print("-" * 60)
        print("\n🔧 硬件关键词:")
        for kw in get_hardware_keywords(region):
            print(f"  - {kw}")
        print("\n💻 软件关键词:")
        for kw in get_software_keywords(region):
            print(f"  - {kw}")
        print(f"\n📊 Mixed 模式关键词 (40%硬件 + 60%软件):")
        for kw in get_keywords_for_today(region, "mixed"):
            print(f"  - {kw}")
        return

    if args.schedule:
        setup_schedule()
        return

    should_lock = not (
        args.list_sources or args.list_regions or args.list_keywords or
        args.test_perplexity or args.test_glm or args.test_routing or
        args.schedule
    )
    if should_lock and not args.no_lock:
        _lock_handle, acquired = acquire_process_lock(AUTO_DISCOVER_LOCK_FILE)
        if not acquired:
            print(f"\n⛔ Another auto_discover process is running.")
            print(f"   Lock file: {AUTO_DISCOVER_LOCK_FILE}")
            print("   If you are sure it's stale, delete the lock file and retry.")
            return

    # 发现功能
    if args.region:
        # 新方式：按地区搜索
        product_type = getattr(args, 'type', 'mixed')
        if args.region == 'all':
            discover_all_regions(args.dry_run, product_type)
        else:
            discover_by_region(args.region, args.dry_run, product_type)
    elif args.source:
        # 旧方式：按渠道搜索
        discover_from_source(args.source, args.dry_run)
    else:
        # 默认：运行所有地区的 Perplexity Search
        print("\n💡 提示：使用 --region 参数进行地区搜索（推荐）")
        print("   示例: python tools/auto_discover.py --region us")
        print("   或者: python tools/auto_discover.py --region all")
        print("\n   使用 --source 参数进行旧渠道搜索")
        print("   示例: python tools/auto_discover.py --source 36kr")
        print("\n运行 --help 查看所有选项")


if __name__ == '__main__':
    main()
