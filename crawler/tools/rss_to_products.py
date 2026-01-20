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
from datetime import datetime
from typing import List, Dict, Optional, Any
import argparse

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# ============================================
# 配置
# ============================================

DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
BLOGS_NEWS_FILE = os.path.join(DATA_DIR, 'blogs_news.json')
CANDIDATES_DIR = os.path.join(DATA_DIR, 'candidates')
PRODUCTS_FEATURED_FILE = os.path.join(DATA_DIR, 'products_featured.json')

# 确保目录存在
os.makedirs(CANDIDATES_DIR, exist_ok=True)

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
    """获取 LLM 客户端 (优先 Perplexity，其次 GLM)"""
    
    # 尝试 Perplexity
    perplexity_key = os.getenv('PERPLEXITY_API_KEY')
    if perplexity_key:
        try:
            from utils.perplexity_client import PerplexityClient
            client = PerplexityClient(api_key=perplexity_key)
            if client.is_available():
                return ("perplexity", client)
        except Exception as e:
            print(f"  ⚠️ Perplexity 初始化失败: {e}")
    
    # 尝试 GLM
    glm_key = os.getenv('ZHIPU_API_KEY')
    if glm_key:
        try:
            from zhipuai import ZhipuAI
            client = ZhipuAI(api_key=glm_key)
            return ("glm", client)
        except Exception as e:
            print(f"  ⚠️ GLM 初始化失败: {e}")
    
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
3. why_matters 必须具体，包含数字/事实，不要泛泛而谈
4. 如果文章只是行业分析/观点，has_product 设为 false

只返回 JSON，不要其他内容。"""


# ============================================
# LLM 调用
# ============================================

def extract_products_with_llm(article: Dict, llm_type: str, llm_client: Any) -> List[Dict]:
    """使用 LLM 从文章中提取产品信息"""
    
    title = article.get('title', '')
    source = article.get('source', '')
    content = article.get('summary', '')
    
    prompt = EXTRACTION_PROMPT.format(
        title=title,
        source=source,
        content=content
    )
    
    try:
        if llm_type == "perplexity":
            response = llm_client.analyze(prompt=prompt)
            # analyze 返回解析后的 JSON 或字符串
            if isinstance(response, dict):
                result_text = json.dumps(response)
            elif isinstance(response, list):
                result_text = json.dumps({"has_product": True, "products": response})
            else:
                result_text = str(response)
        
        elif llm_type == "glm":
            response = llm_client.chat.completions.create(
                model="glm-4-flash",
                messages=[
                    {"role": "system", "content": "你是一个 AI 产品分析师，专门从新闻中提取产品信息。只返回 JSON 格式。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
            )
            result_text = response.choices[0].message.content
        
        else:
            return []
        
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

def search_website(name: str, category: str, llm_type: str, llm_client: Any) -> str:
    """搜索产品官网"""
    if llm_type != "perplexity":
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


def validate_product(product: Dict, article: Dict, llm_type: str = None, llm_client: Any = None) -> Optional[Dict]:
    """验证和标准化产品数据"""
    
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
    
    # 获取网站 (先从产品提取，没有则搜索补充)
    website = product.get('website', '')
    if not website and llm_client:
        website = search_website(name, product.get('category', ''), llm_type, llm_client)
    
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
    
    # 标准化数据
    standardized = {
        "name": name,
        "slug": name.lower().replace(' ', '-').replace('.', '-'),
        "website": website,
        "description": product.get('description', '')[:200],
        "category": product.get('category', 'other'),
        "is_hardware": product.get('is_hardware', False),
        "hardware_category": product.get('hardware_category', ''),
        "is_big_company": is_big_company,  # 标记大公司产品
        "parent_company": parent_company,  # 母公司名称
        "funding_total": product.get('funding_total', ''),
        "funding_stage": product.get('funding_stage', ''),
        "founded_date": product.get('founded_date', ''),
        "region": product.get('region', '🇺🇸'),
        "dark_horse_index": min(5, max(1, int(score))),
        "why_matters": why_matters[:300],
        "criteria_met": [product.get('score_reason', '')],
        "discovered_at": datetime.now().strftime('%Y-%m-%d'),
        "source": article.get('source', ''),
        "source_url": article.get('link', ''),
        "source_title": article.get('title', ''),
    }
    
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
    products = []
    
    # 加载 featured 产品
    if os.path.exists(PRODUCTS_FEATURED_FILE):
        with open(PRODUCTS_FEATURED_FILE, 'r') as f:
            products.extend(json.load(f))
    
    # 加载候选池
    for filename in os.listdir(CANDIDATES_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(CANDIDATES_DIR, filename)
            with open(filepath, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    products.extend(data)
    
    return products


def filter_articles(articles: List[Dict], source_filter: str = None) -> List[Dict]:
    """筛选包含产品信息的文章"""
    filtered = []
    
    for article in articles:
        # 来源筛选
        if source_filter and source_filter.lower() not in article.get('source', '').lower():
            continue
        
        # 关键词筛选
        text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
        has_keyword = any(kw.lower() in text for kw in PRODUCT_KEYWORDS)
        
        if has_keyword or article.get('has_product_mention'):
            filtered.append(article)
    
    return filtered


def process_articles(
    articles: List[Dict],
    llm_type: str,
    llm_client: Any,
    existing_products: List[Dict],
    dry_run: bool = False
) -> List[Dict]:
    """处理文章，提取产品"""
    
    extracted_products = []
    
    for i, article in enumerate(articles):
        title = article.get('title', '')[:60]
        source = article.get('source', '')
        
        print(f"\n[{i+1}/{len(articles)}] {source}")
        print(f"  📰 {title}...")
        
        # 调用 LLM 提取
        products = extract_products_with_llm(article, llm_type, llm_client)
        
        if not products:
            print(f"  ⏭️ 无产品信息")
            continue
        
        for product in products:
            # 验证 (传递 LLM 客户端用于搜索网站)
            validated = validate_product(product, article, llm_type, llm_client)
            if not validated:
                print(f"  ⏭️ {product.get('name', '?')} - 验证未通过")
                continue
            
            # 去重
            if is_duplicate(validated, existing_products + extracted_products):
                print(f"  ⏭️ {validated['name']} - 已存在")
                continue
            
            score = validated['dark_horse_index']
            print(f"  ✅ {validated['name']} ({score}分) - {validated['why_matters'][:40]}...")
            extracted_products.append(validated)
        
        # 速率限制
        time.sleep(1)
    
    return extracted_products


def save_products(products: List[Dict], dry_run: bool = False):
    """保存产品到候选池"""
    if not products:
        print("\n📭 没有新产品需要保存")
        return
    
    if dry_run:
        print(f"\n🧪 [DRY RUN] 将保存 {len(products)} 个产品")
        return
    
    # 按日期保存
    today = datetime.now().strftime('%Y%m%d')
    filename = f"rss_candidates_{today}.json"
    filepath = os.path.join(CANDIDATES_DIR, filename)
    
    # 如果文件已存在，追加
    existing = []
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            existing = json.load(f)
    
    # 合并并去重
    all_products = existing + products
    seen = set()
    unique = []
    for p in all_products:
        key = p.get('name', '').lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    
    with open(filepath, 'w') as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 保存 {len(products)} 个新产品到 {filepath}")


# ============================================
# CLI
# ============================================

def main():
    parser = argparse.ArgumentParser(description="RSS 新闻 → 产品数据转换")
    parser.add_argument("--limit", type=int, default=50, help="处理文章数量上限")
    parser.add_argument("--source", type=str, help="只处理指定来源的文章")
    parser.add_argument("--dry-run", action="store_true", help="测试模式，不保存")
    parser.add_argument("--input", type=str, help="输入文件路径")
    
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
    
    print(f"📰 读取 {len(articles)} 篇新闻")
    
    # 筛选文章
    filtered = filter_articles(articles, args.source)
    print(f"🔍 筛选出 {len(filtered)} 篇包含产品信息的文章")
    
    if not filtered:
        print("⚠️ 没有找到包含产品信息的文章")
        return
    
    # 限制数量
    filtered = filtered[:args.limit]
    
    # 获取 LLM 客户端
    print("\n🤖 初始化 LLM...")
    llm_type, llm_client = get_llm_client()
    
    if not llm_client:
        print("❌ 没有可用的 LLM 客户端")
        print("请配置 PERPLEXITY_API_KEY 或 ZHIPU_API_KEY")
        return
    
    print(f"  ✅ 使用 {llm_type}")
    
    # 加载已有产品
    existing = load_existing_products()
    print(f"📦 已有 {len(existing)} 个产品")
    
    # 处理文章
    print(f"\n🔄 开始处理 {len(filtered)} 篇文章...")
    products = process_articles(
        filtered,
        llm_type,
        llm_client,
        existing,
        args.dry_run
    )
    
    # 保存
    save_products(products, args.dry_run)
    
    # 统计
    print("\n📊 统计:")
    print(f"  - 处理文章: {len(filtered)}")
    print(f"  - 提取产品: {len(products)}")
    
    if products:
        scores = [p.get('dark_horse_index', 0) for p in products]
        print(f"  - 5分产品: {scores.count(5)}")
        print(f"  - 4分产品: {scores.count(4)}")
        print(f"  - 3分产品: {scores.count(3)}")
        print(f"  - 2分产品: {scores.count(2)}")


if __name__ == "__main__":
    main()
