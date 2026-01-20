#!/usr/bin/env python3
"""
自动发现全球 AI 产品 (v2.0 - 集成 Web Search MCP)

功能：
1. 使用 Zhipu Web Search MCP 实时搜索全球 AI 产品
2. 按地区分配搜索任务 (美国40%/中国25%/欧洲15%/日韩10%/东南亚10%)
3. 使用专业 Prompt 提取产品信息并评分
4. 自动分类到黑马(4-5分)/潜力股(2-3分)

用法：
    python tools/auto_discover.py                    # 运行所有地区
    python tools/auto_discover.py --region us       # 只搜索美国
    python tools/auto_discover.py --region cn       # 只搜索中国
    python tools/auto_discover.py --dry-run         # 预览不保存
    python tools/auto_discover.py --test-search     # 测试 Web Search MCP
"""

import json
import os
import sys
import argparse
import re
import time
import requests
from datetime import datetime, timezone
from urllib.parse import urlparse
import subprocess
from typing import Optional

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

# 智谱 AI 配置
API_RATE_LIMIT_DELAY = 3  # 每次 API 调用后等待秒数
ZHIPU_API_KEY = os.environ.get('ZHIPU_API_KEY', '9c842f4999534eeba595b9fd142a699a.XXaPIGhbZTdzYIu8')
ZHIPU_MODEL = 'glm-4.7'

# Web Search MCP 配置
WEB_SEARCH_MCP_URL = "https://open.bigmodel.cn/api/mcp/web_search/sse"
WEB_SEARCH_AUTH = ZHIPU_API_KEY

# Perplexity API 配置
PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY', '')
PERPLEXITY_MODEL = os.environ.get('PERPLEXITY_MODEL', 'sonar')  # sonar or sonar-pro

# Provider routing (toggle for testing)
USE_PERPLEXITY = os.environ.get('USE_PERPLEXITY', 'false').lower() == 'true'
REGION_PROVIDER_MAP = {
    'cn': 'glm',      # Always use GLM for Chinese content
    'us': 'perplexity' if USE_PERPLEXITY else 'glm',
    'eu': 'perplexity' if USE_PERPLEXITY else 'glm',
    'jp': 'perplexity' if USE_PERPLEXITY else 'glm',
    'kr': 'perplexity' if USE_PERPLEXITY else 'glm',
    'sea': 'perplexity' if USE_PERPLEXITY else 'glm',
}

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
KEYWORDS_HARDWARE = {
    "us": [
        "AI chip startup funding 2026",
        "humanoid robot company funding",
        "AI hardware startup Series A",
        "AI semiconductor startup investment",
        "robotics AI company raised funding",
        "AI accelerator chip startup",
        "edge AI hardware startup",
        "AI inference chip company",
        # 新增: 从 Product Hunt/Kickstarter 发现
        "AI wearable device startup 2026",
        "AI smart glasses startup funding",
        "AI robot kickstarter 2026",
    ],
    "cn": [
        "AI芯片 创业公司 融资",
        "人形机器人 创业公司",
        "AI硬件 融资 2026",
        "智能机器人 创业公司 A轮",
        "AI芯片 独角兽",
        "具身智能 创业公司",
        "边缘AI芯片 融资",
        # 新增: 从 36氪 发现
        "AI智能眼镜 创业公司",
        "AI可穿戴设备 融资 2026",
    ],
    "eu": [
        "European AI chip startup funding",
        "robotics startup Europe funding",
        "AI hardware company Germany UK",
        "semiconductor AI startup Europe",
        # 新增
        "AI robot startup Europe 2026",
    ],
    "jp": [
        "AI半導体 スタートアップ 資金調達",
        "ロボット AI企業 日本",
        "Japan robotics AI startup",
        "AI chip startup Japan",
    ],
    "kr": [
        "AI 반도체 스타트업 투자",
        "로봇 AI 기업 한국",
        "Korean AI chip startup",
    ],
    "sea": [
        "AI hardware startup Singapore",
        "robotics company Southeast Asia",
        "AI chip startup Asia",
    ],
}

# 兼容旧代码的别名
KEYWORDS_BY_REGION = KEYWORDS_SOFTWARE

# ============================================
# 站点定向搜索（直接搜索目标媒体）
# ============================================
SITE_SEARCHES = {
    "us": [
        "site:techcrunch.com AI startup funding",
        "site:producthunt.com AI launch 2026",
        "site:venturebeat.com AI funding",
        # 硬件站点 (新增)
        "site:producthunt.com AI hardware robot device 2026",
        "site:kickstarter.com AI robot wearable 2026",
    ],
    "cn": [
        "site:36kr.com AI融资",
        "site:tmtpost.com 人工智能",
        "site:jiqizhixin.com 融资",
        # 硬件站点 (新增)
        "site:36kr.com AI硬件 机器人 2026",
        "site:36kr.com 具身智能 人形机器人 2026",
    ],
    "eu": [
        "site:sifted.eu AI funding",
        "site:tech.eu AI startup",
        "site:eu-startups.com AI",
        # 硬件站点 (新增)
        "site:kickstarter.com AI robot Europe 2026",
    ],
    "jp": [
        "site:thebridge.jp AI startup",
        "site:jp.techcrunch.com AI",
        # 硬件站点 (新增)
        "site:kickstarter.com AI robot Japan 2026",
    ],
    "kr": [
        "site:platum.kr AI 스타트업",
        "site:besuccess.com AI",
    ],
    "sea": [
        "site:e27.co AI startup",
        "site:techinasia.com AI funding",
        # 硬件站点 (新增)
        "site:kickstarter.com AI hardware Singapore 2026",
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

## Output (JSON only)
```json
[{{"name": "...", "website": "https://...", "description": "中文描述(>20字)", "category": "coding|image|video|...", "region": "{region}", "funding_total": "$50M", "dark_horse_index": 4, "criteria_met": ["funding_signal"], "why_matters": "具体数字+差异化", "source": "...", "confidence": 0.85}}]
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

## 输出 (仅JSON)
```json
[{{"name": "产品名", "website": "https://...", "description": "中文描述(>20字)", "category": "coding|image|video|...", "region": "{region}", "funding_total": "$50M", "dark_horse_index": 4, "criteria_met": ["funding_signal"], "why_matters": "具体数字+差异化", "source": "...", "confidence": 0.85}}]
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
    """检查是否重复"""
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
    "ernie", "百度", "baidu", "智谱", "zhipu", "chatglm", "glm",
    "讯飞星火", "星火", "spark", "minimax", "abab",
    # 大厂产品
    "google gemini", "google bard", "meta llama", "llama",
    "microsoft copilot", "bing chat", "amazon q", "aws bedrock",
}


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
    
    # 修复缺少协议的 URL
    if not website.startswith(("http://", "https://")) and "." in website:
        website = f"https://{website}"
        product["website"] = website
    
    if website.lower() == "unknown":
        # 允许 unknown，但后续需要人工验证
        product["needs_verification"] = True
    elif not website.startswith(("http://", "https://")):
        return False, "invalid website URL"

    # 3. 检查 description 长度
    if len(description) < 20:
        return False, f"description too short ({len(description)} chars)"

    # 4. 检查 why_matters 是否太泛化
    why_lower = why_matters.lower()
    for generic in GENERIC_WHY_MATTERS:
        if generic in why_lower and len(why_matters) < 50:
            return False, f"generic why_matters: contains '{generic}'"

    # 5. 检查 why_matters 是否包含具体数字（融资/ARR/用户数）
    has_number = bool(re.search(r'[\$¥€]\d+|ARR|\d+[MBK万亿]|\d+%', why_matters))
    has_specific = any(kw in why_matters for kw in [
        '领投', '融资', '估值', '用户', '增长', 'ARR', '首创', '首个',
        '前OpenAI', '前Google', '前Meta', 'YC', 'a16z', 'Sequoia',
    ])
    if not has_number and not has_specific:
        return False, "why_matters lacks specific details"

    # 6. 检查 name 是否像新闻标题
    news_patterns = ['融资', '宣布', '发布', '获得', '完成', '推出', '上线']
    if any(p in name for p in news_patterns) and len(name) > 15:
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
    criteria = product.get("criteria_met", [])
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


def get_zhipu_client():
    """获取智谱 AI 客户端"""
    try:
        from zhipuai import ZhipuAI
        return ZhipuAI(api_key=ZHIPU_API_KEY)
    except ImportError:
        print("  Error: zhipuai SDK not installed. Run: pip install zhipuai")
        return None


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


def web_search_mcp(query: str, search_engine: str = "bing", count: int = 10) -> list:
    """
    使用 Zhipu Web Search MCP 进行实时网络搜索

    Args:
        query: 搜索关键词
        search_engine: 搜索引擎 (bing/sogou/quark/jina)
        count: 返回结果数量

    Returns:
        搜索结果列表 [{"title": "", "url": "", "content": ""}, ...]
    """
    # 使用智谱 AI API 进行 web_search 工具调用
    client = get_zhipu_client()
    if not client:
        return []

    try:
        print(f"  🔍 Web Search: {query[:50]}...")

        # 使用 GLM-4.7 的 web_search 工具
        response = client.chat.completions.create(
            model="glm-4-plus",  # 支持 web_search 的模型
            messages=[{
                "role": "user",
                "content": f"搜索最新的 AI 创业公司融资新闻: {query}"
            }],
            tools=[{
                "type": "web_search",
                "web_search": {
                    "enable": True,
                    "search_engine": search_engine,
                    "search_result": True
                }
            }],
            tool_choice="auto",
            max_tokens=4096
        )

        # 提取搜索结果
        results = []

        # 检查是否有 web_search 结果
        if hasattr(response, 'web_search') and response.web_search:
            for item in response.web_search:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", item.get("url", "")),
                    "content": item.get("content", item.get("snippet", ""))
                })

        # 如果没有结构化结果，从回复中提取
        if not results and response.choices:
            content = response.choices[0].message.content
            # 返回原始内容供后续处理
            results = [{"title": "Search Results", "url": "", "content": content}]

        print(f"  ✅ Found {len(results)} results")
        return results

    except Exception as e:
        print(f"  ❌ Web Search Error: {e}")
        # 降级：使用 GLM 知识库
        return []
    finally:
        time.sleep(API_RATE_LIMIT_DELAY)


def analyze_with_glm(content: str, task: str = "extract", region: str = "🇺🇸",
                     quota_remaining: dict = None, region_key: str = "us") -> dict:
    """
    使用 GLM-4.7 分析内容 (使用双语 Prompt - 合并提取+评分)

    Args:
        content: 要分析的内容（搜索结果、产品信息等）
        task: 任务类型 (extract/score/translate)
        region: 地区标识 (emoji flag)
        quota_remaining: 剩余配额 {"dark_horses": n, "rising_stars": m}
        region_key: 地区代码 (cn/us/eu/jp/kr/sea) 用于选择 prompt 语言

    Returns:
        分析结果字典
    """
    client = get_zhipu_client()
    if not client:
        return {}

    # 默认配额
    if quota_remaining is None:
        quota_remaining = DAILY_QUOTA.copy()

    if task == "extract":
        # 使用双语 prompt 选择器（合并提取+评分）
        prompt_template = get_extraction_prompt(region_key)
        prompt = prompt_template.format(
            search_results=content[:10000],
            region=region,
            quota_dark_horses=quota_remaining.get("dark_horses", 5),
            quota_rising_stars=quota_remaining.get("rising_stars", 10)
        )

    elif task == "score":
        # 保留单独评分功能（用于 fallback）
        prompt = PROMPT_DARK_HORSE_SCORING.format(
            product=json.dumps(content, ensure_ascii=False, indent=2)
        )

    elif task == "translate":
        prompt = f"""将以下内容翻译成中文，保持专业术语：

{content}

只返回翻译结果，不要其他内容。"""

    try:
        response = client.chat.completions.create(
            model=ZHIPU_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4096
        )

        result_text = response.choices[0].message.content

        # 提取 JSON
        if task in ["extract", "score"]:
            # 尝试提取 JSON
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result_text)
            if json_match:
                return json.loads(json_match.group(1))
            # 尝试直接解析
            try:
                return json.loads(result_text)
            except:
                return {}
        else:
            return {"text": result_text}

    except Exception as e:
        print(f"  GLM Error: {e}")
        return {}
    finally:
        # 限流：每次 API 调用后等待
        time.sleep(API_RATE_LIMIT_DELAY)


def analyze_with_perplexity(content: str, task: str = "extract", region: str = "🇺🇸",
                            quota_remaining: dict = None, region_key: str = "us") -> dict:
    """
    使用 Perplexity Sonar 模型分析内容
    
    与 analyze_with_glm() 接口相同，用于产品提取和评分。
    
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
        prompt_template = get_extraction_prompt(region_key)
        prompt = prompt_template.format(
            search_results=content[:10000],
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
# Provider Routing Functions
# ============================================

def get_provider_for_region(region_key: str) -> str:
    """Get provider name for region"""
    return REGION_PROVIDER_MAP.get(region_key, 'glm')


def search_with_provider(query: str, region_key: str, search_engine: str = "bing") -> list:
    """Route search to appropriate provider"""
    provider = get_provider_for_region(region_key)
    if provider == 'perplexity':
        return perplexity_search(query)
    else:
        return web_search_mcp(query, search_engine)


def analyze_with_provider(content, task: str, region_key: str, region_flag: str = "🇺🇸",
                          quota_remaining: dict = None):
    """
    Route analysis to appropriate provider

    Args:
        content: 要分析的内容
        task: 任务类型 (extract/score)
        region_key: 地区代码 (cn/us/eu/jp/kr/sea) 用于选择 provider 和 prompt 语言
        region_flag: 地区标识 (emoji flag)
        quota_remaining: 剩余配额
    """
    provider = get_provider_for_region(region_key)
    if provider == 'perplexity':
        return analyze_with_perplexity(content, task, region_flag, quota_remaining, region_key)
    else:
        return analyze_with_glm(content, task, region_flag, quota_remaining, region_key)


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


def search_with_glm(query: str, region: str = "🇺🇸") -> list:
    """
    使用 GLM-4.7 的知识库搜索 AI 产品

    GLM-4.7 有较新的知识，可以直接询问最新的 AI 产品
    """
    client = get_zhipu_client()
    if not client:
        return []

    if region == "🇨🇳":
        prompt = f"""请列出最近（2024-2025年）{query}相关的 AI 创业公司/产品，特别是：
- 获得融资的公司
- 有创新产品的公司
- 在行业内有影响力的公司

返回 JSON 数组格式：
```json
[
  {{
    "name": "公司/产品名",
    "website": "官网（如果知道）",
    "description": "一句话描述",
    "funding": "融资信息（如果知道）",
    "category": "分类",
    "why_matters": "为什么值得关注"
  }}
]
```
只返回 JSON，至少返回 5 个产品。"""
    else:
        prompt = f"""List recent (2024-2025) AI startups/products related to {query}, especially:
- Companies that raised funding
- Companies with innovative products
- Influential companies in the industry

Return JSON array format:
```json
[
  {{
    "name": "Company/Product name",
    "website": "Website if known",
    "description": "One sentence description",
    "funding": "Funding info if known",
    "category": "Category",
    "why_matters": "Why it matters"
  }}
]
```
Return JSON only, at least 5 products."""

    try:
        response = client.chat.completions.create(
            model=ZHIPU_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=4096
        )

        result_text = response.choices[0].message.content

        # 提取 JSON
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result_text)
        if json_match:
            return json.loads(json_match.group(1))
        try:
            return json.loads(result_text)
        except:
            return []

    except Exception as e:
        print(f"  GLM Search Error: {e}")
        return []
    finally:
        time.sleep(API_RATE_LIMIT_DELAY)


def fetch_with_glm(source_config: dict, limit: int = 10) -> list:
    """
    使用 GLM-4.7 从渠道发现产品

    策略：
    1. 先尝试抓取网页
    2. 如果网页内容不足，使用 GLM 知识库搜索
    3. 用 GLM 评分
    """
    source_name = source_config['name']
    region = source_config['region']
    url = source_config.get('url', '')
    keywords = source_config.get('keywords', [])

    print(f"  Fetching: {url}")

    # 抓取网页内容
    content = fetch_url_content(url)
    products = []

    if content and len(content) > 500:
        print(f"  Analyzing page content with GLM-4.7...")
        products = analyze_with_glm(content, task="extract")
        if not isinstance(products, list):
            products = []

    # 如果网页提取失败，使用 GLM 知识库搜索
    if len(products) < 3:
        print(f"  Page content insufficient, using GLM knowledge search...")
        search_query = ' '.join(keywords[:3]) if keywords else source_name
        products = search_with_glm(search_query, region)
        if not isinstance(products, list):
            products = []

    print(f"  Found {len(products)} potential products")

    # 补充信息并评分
    result = []
    for p in products[:limit]:
        # 添加来源信息
        p['source'] = source_name
        p['region'] = region
        p['discovered_at'] = datetime.utcnow().strftime('%Y-%m-%d')

        # 用 GLM 评分
        score_result = analyze_with_glm(p, task="score")
        if score_result:
            p['dark_horse_index'] = score_result.get('score', 2)
            if 'reason' in score_result:
                p['score_reason'] = score_result['reason']

        result.append(p)

    return result


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
        
        # 检查是否已存在（按 website 去重）
        existing_websites = {normalize_url(p.get('website', '')) for p in featured}
        product_domain = normalize_url(product.get('website', ''))
        
        if product_domain and product_domain in existing_websites:
            print(f"  📋 Already in featured: {product.get('name')}")
            return
        
        # 转换字段格式（适配前端）
        featured_product = {
            'name': product.get('name'),
            'description': product.get('description'),
            'website': product.get('website'),
            'logo_url': product.get('logo', ''),
            'categories': [product.get('category', 'other')],
            'dark_horse_index': product.get('dark_horse_index', 2),
            'why_matters': product.get('why_matters', ''),
            'funding_total': product.get('funding_total', ''),
            'region': product.get('region', '🌍'),
            'source': product.get('source', 'auto_discover'),
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

    # 使用 GLM-4.7 发现产品
    products = fetch_with_glm(config)

    new_count = 0
    for product in products:
        if is_duplicate(product.get('name', ''), product.get('website', ''), existing):
            print(f"  Skip duplicate: {product.get('name')}")
            continue

        # 如果 GLM 没有评分，使用规则评分
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
# 新增：基于地区的 Web Search 发现
# ============================================

def discover_by_region(region_key: str, dry_run: bool = False, product_type: str = "mixed") -> dict:
    """
    使用 Web Search MCP 按地区发现 AI 产品（增强版：带质量过滤和关键词轮换）

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

    # 使用关键词轮换（支持产品类型）
    keywords = get_keywords_for_today(region_key, product_type)

    # Get provider for this region
    provider = get_provider_for_region(region_key)

    type_label = {"software": "💻 软件", "hardware": "🔧 硬件", "mixed": "📊 混合(40%硬件+60%软件)"}.get(product_type, "混合")
    
    print(f"\n{'='*60}")
    print(f"  🌍 Discovering AI Products: {region_name}")
    print(f"  📡 Search Engine: {search_engine}")
    print(f"  🤖 Provider: {provider}")
    print(f"  📦 Product Type: {type_label}")
    print(f"  🔑 Keywords: {len(keywords)} queries (day {datetime.now().weekday()})")
    print(f"{'='*60}")

    existing_names = load_existing_products()
    existing_domains = load_existing_domains()
    all_products = []
    quality_rejections = []

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
    }

    # 对每个关键词进行搜索
    for i, keyword in enumerate(keywords, 1):
        print(f"\n  [{i}/{len(keywords)}] Searching: {keyword[:50]}...")

        # 1. Search using provider routing
        search_results = search_with_provider(keyword, region_key, search_engine)
        stats["search_results"] += len(search_results)

        if not search_results:
            print(f"    ⚠️ No results, using GLM knowledge...")
            search_results = search_with_glm(keyword, region_name)

        # 将搜索结果格式化为文本
        search_text = "\n\n".join([
            f"### {r.get('title', 'No Title')}\n"
            f"URL: {r.get('url', 'N/A')}\n"
            f"{r.get('content', r.get('snippet', ''))}"
            for r in search_results
        ])

        if not search_text.strip():
            continue

        # 2. Extract products using provider routing
        print(f"    📊 Extracting products with {provider}...")

        region_flag_map = {
            'us': '🇺🇸', 'cn': '🇨🇳', 'eu': '🇪🇺',
            'jp': '🇯🇵🇰🇷', 'kr': '🇰🇷', 'sea': '🇸🇬'
        }
        region_flag = region_flag_map.get(region_key, '🌍')

        products = analyze_with_provider(search_text, "extract", region_key, region_flag)

        if not isinstance(products, list):
            products = []

        print(f"    ✅ Extracted {len(products)} products")
        stats["products_found"] += len(products)

        # 3. 对每个产品评分
        for product in products:
            name = product.get('name', '')
            if not name:
                continue

            # 域名去重
            domain = normalize_url(product.get('website', ''))
            if domain and domain in existing_domains:
                stats["duplicates_skipped"] += 1
                print(f"    ⏭️ Skip duplicate domain: {domain}")
                continue

            # 名称去重
            if is_duplicate(name, product.get('website', ''), existing_names):
                stats["duplicates_skipped"] += 1
                print(f"    ⏭️ Skip duplicate name: {name}")
                continue

            # 质量验证
            is_valid, reason = validate_product(product)
            if not is_valid:
                stats["quality_rejections"] += 1
                quality_rejections.append({"name": name, "reason": reason})
                print(f"    ❌ Quality fail: {name} ({reason})")
                continue

            # 补充信息
            product['region'] = region_flag
            product['discovered_at'] = datetime.utcnow().strftime('%Y-%m-%d')
            product['discovery_method'] = f'{provider}_search'
            product['search_keyword'] = keyword

            # 4. 使用合并 prompt 的评分（无需额外 API 调用）
            # 如果提取结果已包含 dark_horse_index，直接使用
            # 否则使用规则评分作为 fallback
            score = product.get('dark_horse_index')
            if score is None:
                print(f"    🎯 Fallback scoring: {product.get('name')}...")
                product = analyze_and_score(product)
                score = product.get('dark_horse_index', 2)

            criteria = product.get('criteria_met', [])
            print(f"    📈 Score: {score}/5 | Criteria: {criteria}")

            # 5. URL 验证（可选，跳过 dry_run 模式）
            website = product.get('website', '')
            if not dry_run and website and website.lower() != 'unknown':
                if not verify_url_exists(website, timeout=5):
                    print(f"    ⚠️ URL not accessible: {website}")
                    product['needs_verification'] = True
                    # 不拒绝，但标记需要人工验证

            # 6. 保存产品
            save_product(product, dry_run)
            stats["products_saved"] += 1

            if score >= 4:
                stats["dark_horses"] += 1
            else:
                stats["rising_stars"] += 1

            existing_names.add(name.lower())
            if domain:
                existing_domains.add(domain)
            all_products.append(product)

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
    print(f"  📅 Keyword Pool: Day {datetime.now().weekday()} (0=Mon)")
    print(f"  🤖 Perplexity: {'enabled' if USE_PERPLEXITY else 'disabled'}")
    print("═"*70)

    # 初始化跟踪
    found = {"dark_horses": 0, "rising_stars": 0}
    region_yield = {k: 0 for k in REGION_CONFIG.keys()}
    provider_stats = {"glm": 0, "perplexity": 0}  # Track provider usage
    unique_domains = set()
    duplicates_skipped = 0
    quality_rejections = []
    attempts = 0

    # 加载已存在的域名
    existing_domains = load_existing_domains()
    existing_names = load_existing_products()

    def quotas_met():
        return (found["dark_horses"] >= DAILY_QUOTA["dark_horses"] and
                found["rising_stars"] >= DAILY_QUOTA["rising_stars"])

    def get_category(score):
        return "dark_horses" if score >= 4 else "rising_stars"

    # 主发现循环
    while not quotas_met() and attempts < MAX_ATTEMPTS:
        attempts += 1
        print(f"\n{'─'*70}")
        print(f"  🔄 Round {attempts}/{MAX_ATTEMPTS}")
        print(f"  Progress: DH {found['dark_horses']}/{DAILY_QUOTA['dark_horses']} | RS {found['rising_stars']}/{DAILY_QUOTA['rising_stars']}")
        print(f"{'─'*70}")

        # 随机化地区顺序
        region_order = get_region_order()

        for region_key in region_order:
            # 检查地区配额
            if region_yield[region_key] >= REGION_MAX.get(region_key, 3):
                print(f"\n  ⏭️ Skip {region_key}: region max reached ({region_yield[region_key]})")
                continue

            # 检查全局配额
            if quotas_met():
                break

            config = REGION_CONFIG[region_key]
            region_name = config['name']
            search_engine = config['search_engine']

            # 获取今日关键词（带轮换，支持产品类型）
            keywords = get_keywords_for_today(region_key, product_type)
            # 每轮只取部分关键词，避免重复
            keywords_this_round = keywords[:2] if attempts > 1 else keywords

            # Get provider for this region
            provider = get_provider_for_region(region_key)
            print(f"\n  📍 {region_name} | Provider: {provider} | Keywords: {len(keywords_this_round)}")

            # 计算剩余配额（传给 prompt）
            quota_remaining = {
                "dark_horses": DAILY_QUOTA["dark_horses"] - found["dark_horses"],
                "rising_stars": DAILY_QUOTA["rising_stars"] - found["rising_stars"],
            }

            for keyword in keywords_this_round:
                if quotas_met():
                    break

                print(f"\n    🔍 Searching: {keyword[:50]}...")

                # 1. Search using provider routing
                search_results = search_with_provider(keyword, region_key, search_engine)

                if not search_results:
                    search_results = search_with_glm(keyword, region_name)

                if not search_results:
                    continue

                # 格式化搜索结果
                search_text = "\n\n".join([
                    f"### {r.get('title', 'No Title')}\n"
                    f"URL: {r.get('url', 'N/A')}\n"
                    f"{r.get('content', r.get('snippet', ''))}"
                    for r in search_results
                ])

                if not search_text.strip():
                    continue

                # 2. Extract products using provider routing
                region_flag_map = {
                    'us': '🇺🇸', 'cn': '🇨🇳', 'eu': '🇪🇺',
                    'jp': '🇯🇵🇰🇷', 'kr': '🇰🇷', 'sea': '🇸🇬'
                }
                region_flag = region_flag_map.get(region_key, '🌍')

                products = analyze_with_provider(
                    search_text,
                    "extract",
                    region_key,
                    region_flag,
                    quota_remaining
                )

                if not isinstance(products, list):
                    products = []

                print(f"    📦 Extracted: {len(products)} candidates")

                # 3. 处理每个产品
                for product in products:
                    if quotas_met():
                        break

                    name = product.get('name', '')
                    if not name:
                        continue

                    # 域名去重
                    domain = normalize_url(product.get('website', ''))
                    if domain in existing_domains or domain in unique_domains:
                        duplicates_skipped += 1
                        print(f"    ⏭️ Dup domain: {domain}")
                        continue

                    # 名称去重
                    if is_duplicate(name, product.get('website', ''), existing_names):
                        duplicates_skipped += 1
                        print(f"    ⏭️ Dup name: {name}")
                        continue

                    # 质量验证
                    is_valid, reason = validate_product(product)
                    if not is_valid:
                        quality_rejections.append({"name": name, "reason": reason})
                        print(f"    ❌ Quality fail: {name} ({reason})")
                        continue

                    # 补充元信息
                    product['region'] = region_flag
                    product['discovered_at'] = datetime.utcnow().strftime('%Y-%m-%d')
                    product['discovery_method'] = f'{provider}_search'
                    product['search_keyword'] = keyword

                    # 使用合并 prompt 的评分（无需额外 API 调用）
                    # 如果提取结果已包含 dark_horse_index，直接使用
                    # 否则使用规则评分作为 fallback
                    score = product.get('dark_horse_index')
                    if score is None:
                        product = analyze_and_score(product)
                        score = product.get('dark_horse_index', 2)

                    category = get_category(score)

                    # 检查分类配额
                    if found[category] >= DAILY_QUOTA[category]:
                        print(f"    ⏭️ {category} quota full, skip: {name}")
                        continue

                    # 检查地区配额
                    if region_yield[region_key] >= REGION_MAX.get(region_key, 3):
                        print(f"    ⏭️ Region max reached, skip: {name}")
                        continue

                    # 保存
                    save_product(product, dry_run)

                    # 更新计数
                    found[category] += 1
                    region_yield[region_key] += 1
                    provider_stats[provider] += 1  # Track provider usage
                    unique_domains.add(domain)
                    existing_names.add(name.lower())

                    status_icon = "🦄" if category == "dark_horses" else "⭐"
                    print(f"    {status_icon} SAVED: {name} (score={score}, {category}, {provider})")

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
    print(f"  Unique domains found: {len(unique_domains)}")
    print(f"  Duplicates skipped: {duplicates_skipped}")
    print(f"  Quality rejections: {len(quality_rejections)}")

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
        "duration_seconds": duration,
        "quotas_met": quotas_met(),
    }


def test_web_search():
    """测试 Web Search MCP 连接"""
    print("\n" + "="*60)
    print("  🔍 Testing Web Search MCP (Zhipu)")
    print("="*60)

    test_queries = [
        ("bing", "AI startup funding 2026"),
        ("sogou", "AI创业公司 融资 2026"),
    ]

    for engine, query in test_queries:
        print(f"\n  Testing: {engine} - {query}")
        results = web_search_mcp(query, engine, count=3)

        if results:
            print(f"  ✅ Success! Found {len(results)} results")
            for i, r in enumerate(results[:2], 1):
                print(f"    {i}. {r.get('title', 'No Title')[:50]}...")
        else:
            print(f"  ⚠️ No results (may fallback to GLM knowledge)")


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
    print(f"  USE_PERPLEXITY: {USE_PERPLEXITY}")
    
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


def test_glm_connection():
    """测试 GLM-4.7 连接"""
    print("\n测试 GLM-4.7 连接...")
    print(f"  API Key: {ZHIPU_API_KEY[:20]}...")
    print(f"  Model: {ZHIPU_MODEL}")

    client = get_zhipu_client()
    if not client:
        print("  ❌ 无法创建客户端，请安装: pip install zhipuai")
        return False

    try:
        response = client.chat.completions.create(
            model=ZHIPU_MODEL,
            messages=[{"role": "user", "content": "你好，请用一句话介绍自己"}],
            max_tokens=100
        )
        result = response.choices[0].message.content
        print(f"  ✅ 连接成功!")
        print(f"  GLM 回复: {result}")
        return True
    except Exception as e:
        print(f"  ❌ 连接失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='自动发现全球 AI 产品 (v2.0 - Web Search MCP)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法：
  # 按地区搜索（推荐，使用 Web Search MCP）
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
  python tools/auto_discover.py --test           # 测试 GLM 连接
  python tools/auto_discover.py --test-search    # 测试 Web Search MCP
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
    parser.add_argument('--test', action='store_true', help='测试 GLM-4.7 连接')
    parser.add_argument('--test-search', action='store_true', help='测试 Web Search MCP (Zhipu)')
    parser.add_argument('--test-perplexity', action='store_true', help='测试 Perplexity Search API')

    args = parser.parse_args()

    # 测试功能
    if args.test:
        test_glm_connection()
        return

    if args.test_search:
        test_web_search()
        return
    
    if args.test_perplexity:
        test_perplexity()
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
        # 默认：运行所有地区的 Web Search
        print("\n💡 提示：使用 --region 参数进行地区搜索（推荐）")
        print("   示例: python tools/auto_discover.py --region us")
        print("   或者: python tools/auto_discover.py --region all")
        print("\n   使用 --source 参数进行旧渠道搜索")
        print("   示例: python tools/auto_discover.py --source 36kr")
        print("\n运行 --help 查看所有选项")


if __name__ == '__main__':
    main()
