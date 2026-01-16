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

# 智谱 AI 配置
API_RATE_LIMIT_DELAY = 3  # 每次 API 调用后等待秒数
ZHIPU_API_KEY = os.environ.get('ZHIPU_API_KEY', '9c842f4999534eeba595b9fd142a699a.XXaPIGhbZTdzYIu8')
ZHIPU_MODEL = 'glm-4.7'

# Web Search MCP 配置
WEB_SEARCH_MCP_URL = "https://open.bigmodel.cn/api/mcp/web_search/sse"
WEB_SEARCH_AUTH = ZHIPU_API_KEY

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
# 专业 Prompts (遵循 INSTRUCTIONS.md 标准)
# ============================================

# Prompt B: 产品提取
PROMPT_PRODUCT_EXTRACTION = """你是 WeeklyAI 的 AI 产品分析师。从搜索结果中提取 AI 产品信息。

## 搜索结果
{search_results}

## 必须排除（不是黑马）：
- ❌ 已人尽皆知: ChatGPT, Midjourney, Cursor, Claude, Copilot, Gemini
- ❌ 开发库/模型: HuggingFace models, LangChain, PyTorch, TensorFlow
- ❌ 没有产品: 只有论文/demo/没官网
- ❌ 大厂产品: Google Gemini, Meta Llama, OpenAI GPT

## 优先收录：
- ✅ 融资新闻 (Series A/B, Seed, 估值)
- ✅ 创始人背景亮眼 (大厂高管出走创业)
- ✅ 品类创新 (开创新赛道)
- ✅ 社区热度 (ProductHunt Top 5)

## 返回 JSON (只返回 JSON，不要其他内容)
```json
[
  {{
    "name": "产品名",
    "website": "https://官网",
    "description": "一句话描述（中文）",
    "category": "coding/image/video/voice/writing/hardware/finance/education/healthcare/other",
    "region": "{region}",
    "funding_total": "$50M Series A",
    "why_matters": "为什么值得关注（要具体，2-3句话）",
    "latest_news": "2026-01: 具体事件",
    "source": "来源网站"
  }}
]
```

如果没有找到符合条件的产品，返回空数组 []。至少提取 3 个产品，最多 10 个。"""

# Prompt C: 黑马评分
PROMPT_DARK_HORSE_SCORING = """评估产品的"黑马指数"(1-5分)：

## 产品
{product}

## 评分标准
5分: 融资>$100M 或 顶级创始人背景 或 品类开创者 或 ARR>$50M
4分: 融资>$30M 或 YC/a16z投资 或 估值增长>3x 或 ARR>$10M
3分: 融资$5M-$30M 或 ProductHunt Top 5 或 本地市场热度高
2分: 有创新点但数据不足 或 早期产品有潜力
1分: 边缘产品 或 待验证 或 信息太少

## 返回格式（只返回 JSON，不要其他内容）
```json
{{
  "dark_horse_index": 4,
  "reason": "评分理由（具体说明依据）"
}}
```"""

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

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


def get_zhipu_client():
    """获取智谱 AI 客户端"""
    try:
        from zhipuai import ZhipuAI
        return ZhipuAI(api_key=ZHIPU_API_KEY)
    except ImportError:
        print("  Error: zhipuai SDK not installed. Run: pip install zhipuai")
        return None


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


def analyze_with_glm(content: str, task: str = "extract", region: str = "🇺🇸") -> dict:
    """
    使用 GLM-4.7 分析内容 (使用专业 Prompt)

    Args:
        content: 要分析的内容（搜索结果、产品信息等）
        task: 任务类型 (extract/score/translate)
        region: 地区标识

    Returns:
        分析结果字典
    """
    client = get_zhipu_client()
    if not client:
        return {}

    if task == "extract":
        # 使用专业的产品提取 Prompt
        prompt = PROMPT_PRODUCT_EXTRACTION.format(
            search_results=content[:10000],
            region=region
        )

    elif task == "score":
        # 使用专业的黑马评分 Prompt
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

    # 保存
    with open(target_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f"  Saved to: {target_file}")


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

def discover_by_region(region_key: str, dry_run: bool = False) -> dict:
    """
    使用 Web Search MCP 按地区发现 AI 产品

    Args:
        region_key: 地区代码 (us/cn/eu/jp/sea)
        dry_run: 预览模式

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
    keywords = config['keywords']

    print(f"\n{'='*60}")
    print(f"  🌍 Discovering AI Products: {region_name}")
    print(f"  📡 Search Engine: {search_engine}")
    print(f"  🔑 Keywords: {len(keywords)} queries")
    print(f"{'='*60}")

    existing = load_existing_products()
    all_products = []
    stats = {
        "region": region_key,
        "region_name": region_name,
        "search_results": 0,
        "products_found": 0,
        "products_saved": 0,
        "dark_horses": 0,
        "rising_stars": 0,
    }

    # 对每个关键词进行搜索
    for i, keyword in enumerate(keywords, 1):
        print(f"\n  [{i}/{len(keywords)}] Searching: {keyword[:40]}...")

        # 1. Web Search 获取实时结果
        search_results = web_search_mcp(keyword, search_engine)
        stats["search_results"] += len(search_results)

        if not search_results:
            print(f"    ⚠️ No results, using GLM knowledge...")
            # 降级：使用 GLM 知识库
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

        # 2. 用专业 Prompt 提取产品
        print(f"    📊 Extracting products with GLM...")

        # 映射地区代码到地区旗帜
        region_flag_map = {
            'us': '🇺🇸',
            'cn': '🇨🇳',
            'eu': '🇪🇺',
            'jp': '🇯🇵🇰🇷',
            'sea': '🇸🇬'
        }
        region_flag = region_flag_map.get(region_key, '🌍')

        products = analyze_with_glm(search_text, task="extract", region=region_flag)

        if not isinstance(products, list):
            products = []

        print(f"    ✅ Extracted {len(products)} products")
        stats["products_found"] += len(products)

        # 3. 对每个产品评分
        for product in products:
            if not product.get('name'):
                continue

            # 检查重复
            if is_duplicate(product.get('name', ''), product.get('website', ''), existing):
                print(f"    ⏭️ Skip duplicate: {product.get('name')}")
                continue

            # 补充信息
            product['region'] = region_flag
            product['discovered_at'] = datetime.utcnow().strftime('%Y-%m-%d')
            product['discovery_method'] = 'web_search_mcp'
            product['search_keyword'] = keyword

            # 4. 用专业 Prompt 评分
            print(f"    🎯 Scoring: {product.get('name')}...")
            score_result = analyze_with_glm(product, task="score")

            if score_result and 'dark_horse_index' in score_result:
                product['dark_horse_index'] = score_result['dark_horse_index']
                product['score_reason'] = score_result.get('reason', '')
            else:
                # 降级：使用规则评分
                product = analyze_and_score(product)

            score = product.get('dark_horse_index', 2)
            print(f"    📈 Score: {score}/5 - {product.get('score_reason', '')[:50]}...")

            # 5. 保存产品
            save_product(product, dry_run)
            stats["products_saved"] += 1

            if score >= 4:
                stats["dark_horses"] += 1
            else:
                stats["rising_stars"] += 1

            existing.add(product.get('name', '').lower())
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

    return stats


def discover_all_regions(dry_run: bool = False) -> list:
    """
    按地区权重发现所有地区的 AI 产品

    Returns:
        所有地区的统计信息
    """
    print("\n" + "="*70)
    print("  🌍 Global AI Product Discovery (Web Search MCP)")
    print("="*70)

    # 按权重排序
    sorted_regions = sorted(
        REGION_CONFIG.items(),
        key=lambda x: x[1]['weight'],
        reverse=True
    )

    all_stats = []
    for region_key, config in sorted_regions:
        print(f"\n  📍 {config['name']} (Weight: {config['weight']}%)")
        stats = discover_by_region(region_key, dry_run)
        all_stats.append(stats)

    # 汇总统计
    print("\n" + "="*70)
    print("  📊 Global Summary")
    print("="*70)

    total_search = sum(s.get('search_results', 0) for s in all_stats)
    total_found = sum(s.get('products_found', 0) for s in all_stats)
    total_saved = sum(s.get('products_saved', 0) for s in all_stats)
    total_dark_horses = sum(s.get('dark_horses', 0) for s in all_stats)
    total_rising_stars = sum(s.get('rising_stars', 0) for s in all_stats)

    print(f"  Total Search Results: {total_search}")
    print(f"  Total Products Found: {total_found}")
    print(f"  Total Products Saved: {total_saved}")
    print(f"  🏇 Total Dark Horses: {total_dark_horses}")
    print(f"  ⭐ Total Rising Stars: {total_rising_stars}")

    return all_stats


def test_web_search():
    """测试 Web Search MCP 连接"""
    print("\n" + "="*60)
    print("  🔍 Testing Web Search MCP")
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

    # 原有参数
    parser.add_argument('--source', '-s', help='指定渠道 (e.g., 36kr, producthunt)')
    parser.add_argument('--tier', '-t', type=int, choices=[1, 2, 3], help='只运行指定级别的渠道')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不保存')
    parser.add_argument('--schedule', action='store_true', help='设置定时任务')
    parser.add_argument('--list-sources', action='store_true', help='列出所有渠道')
    parser.add_argument('--list-regions', action='store_true', help='列出所有地区')
    parser.add_argument('--test', action='store_true', help='测试 GLM-4.7 连接')
    parser.add_argument('--test-search', action='store_true', help='测试 Web Search MCP')

    args = parser.parse_args()

    # 测试功能
    if args.test:
        test_glm_connection()
        return

    if args.test_search:
        test_web_search()
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

    if args.schedule:
        setup_schedule()
        return

    # 发现功能
    if args.region:
        # 新方式：按地区搜索
        if args.region == 'all':
            discover_all_regions(args.dry_run)
        else:
            discover_by_region(args.region, args.dry_run)
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
