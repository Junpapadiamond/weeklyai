#!/usr/bin/env python3
"""
分析 Prompt 模块

职责：从搜索结果中提取 AI 产品信息并评分

设计原则：
1. 结构化输出 (严格 JSON 格式)
2. 具体的评分标准 (黑马 4-5 分 / 潜力股 2-3 分)
3. 质量红线 (why_matters 必须有具体数字)
4. 明确的排除名单 (已知名产品、大厂产品、开发库)
"""

from typing import Optional

# ═══════════════════════════════════════════════════════════════════════════════
# 产品分析 Prompt (从搜索结果提取产品)
# ═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# 英文版 Prompt (us/eu/jp/kr/sea)
# ─────────────────────────────────────────────────────────────────────────────

ANALYSIS_PROMPT_EN = """You are WeeklyAI's AI Product Discovery Analyst.

## Your Task
Extract AI startup/product information from the search results below and score them.

## Search Results
{search_results}

---

## STRICT EXCLUSIONS (NEVER Include These)

### 1. Well-Known Products (already famous)
ChatGPT, Claude, Gemini, Copilot, DALL-E, Sora, Midjourney, Stable Diffusion,
Cursor, Perplexity, ElevenLabs, Synthesia, Runway, Pika, Bolt.new, v0.dev,
Replit, Character.AI, Jasper, Notion AI, Grammarly, Copy.ai

### 2. Big Tech Products
Google Gemini, Meta Llama, Microsoft Copilot, Amazon Bedrock, Apple Intelligence

### 3. Not Products (Dev Tools / Libraries / Models)
LangChain, PyTorch, TensorFlow, HuggingFace models, GitHub repos without product,
Papers only, Demos without official website

### 4. Tool Directories / Lists
"Best AI tools for X", "Top 10 AI tools", "AI tool collection"

---

## DARK HORSE SCORING (4-5 points) - Must meet ≥2 criteria

| Dimension | Signal | Example |
|-----------|--------|---------|
| 🚀 growth_anomaly | Rapid funding, ARR >100% YoY | Lovable: 0 to unicorn in 8mo |
| 👤 founder_background | Ex-OpenAI/Google/Meta exec | SSI: Ilya Sutskever |
| 💰 funding_signal | Seed >$50M, 3x valuation growth | LMArena: $1.7B in 4mo |
| 🆕 category_innovation | First of its kind | World Labs: first commercial world model |
| 🔥 community_buzz | HN/Reddit viral but still small | - |

**5 points**: Funding >$100M OR Top-tier founder OR Category creator
**4 points**: Funding >$30M OR YC/a16z backed OR ARR >$10M

---

## RISING STAR SCORING (2-3 points) - Need only 1 criterion

**3 points**: Funding $1M-$5M OR ProductHunt top 10 OR Strong local traction
**2 points**: Just launched, clear innovation, but limited data

---

## CRITICAL: why_matters Quality Requirements

❌ **REJECT** generic descriptions:
- "This is a promising AI product"
- "Worth watching"
- "Strong team background"

✅ **REQUIRE** specific details:
- "Sequoia led $50M Series A, ARR grew from $0 to $10M in 8 months, first AI-native code editor"
- "Ex-OpenAI co-founder, focused on safe AGI, $1B valuation at first round"

---

## CRITICAL: Website URL Extraction!

The search results above are news ARTICLE URLs, NOT company websites.
You MUST extract the company's OFFICIAL website from the article content:

1. Look for company official URLs mentioned IN the snippet text (e.g., "visit example.com")
2. For well-known patterns: {{company}}.com, {{company}}.ai, {{company}}.io
3. If you're confident about the company name, construct the likely URL

Examples:
- "Linker Vision" → website: "https://linkervision.com" or "https://linkervision.ai"
- "Tucuvi" → website: "https://tucuvi.com"
- "Elyos AI" → website: "https://elyos.ai"

⚠️ If you cannot determine a valid website, still include the product but set:
   "website": "unknown" and "needs_verification": true

The source_url field should contain the NEWS ARTICLE URL from search results.

## Output Format (JSON ONLY)

Return a JSON array. If no qualifying products found, return `[]`.

```json
[
  {{
    "name": "Product Name",
    "website": "https://company-website.com",  // MUST be from search results!
    "description": "One-sentence description in Chinese (>20 chars)",
    "category": "coding|image|video|voice|writing|hardware|finance|education|healthcare|agent|other",
    "region": "{region}",
    "funding_total": "$50M Series A",
    "dark_horse_index": 4,
    "criteria_met": ["funding_signal", "category_innovation"],
    "why_matters": "Specific numbers + specific differentiation (in Chinese)",
    "latest_news": "2026-01: Event description",
    "source": "TechCrunch",
    "source_url": "https://techcrunch.com/article-url",  // Article URL from search results
    "confidence": 0.85
  }}
]
```

---

## Current Quota
- 🦄 Dark Horses (4-5): {quota_dark_horses} remaining
- ⭐ Rising Stars (2-3): {quota_rising_stars} remaining

**Quality over quantity. Return empty array if nothing qualifies.**"""


# ─────────────────────────────────────────────────────────────────────────────
# 中文版 Prompt (cn)
# ─────────────────────────────────────────────────────────────────────────────

ANALYSIS_PROMPT_CN = """你是 WeeklyAI 的 AI 产品发现分析师。

## 你的任务
从以下搜索结果中提取 AI 创业公司/产品信息，并进行评分。

## 搜索结果
{search_results}

---

## 严格排除名单（绝不收录）

### 1. 已经人尽皆知的产品
ChatGPT, Claude, Gemini, Copilot, DALL-E, Sora, Midjourney, Stable Diffusion,
Cursor, Perplexity, Kimi, 豆包, 通义千问, 文心一言, 智谱清言, 讯飞星火,
ElevenLabs, Synthesia, Runway, Pika, Bolt.new, v0.dev

### 2. 大厂产品
Google Gemini, Meta Llama, 百度文心, 阿里通义, 腾讯混元, 字节豆包

### 3. 不是产品（开发库/模型/论文）
LangChain, PyTorch, TensorFlow, HuggingFace 模型, 只有 GitHub 没有产品,
只有论文, 只有 Demo 没有官网

### 4. 工具目录/合集
"XX AI 工具合集", "最好的 AI 工具", "AI 工具盘点"

---

## 黑马评分标准 (4-5 分) - 必须满足 ≥2 条

| 维度 | 信号 | 示例 |
|------|------|------|
| 🚀 growth_anomaly | 融资速度快、ARR 年增长 >100% | Lovable: 8个月从0到独角兽 |
| 👤 founder_background | 大厂高管出走 (前 OpenAI/Google/Meta) | SSI: Ilya Sutskever |
| 💰 funding_signal | 种子轮 >$50M、估值增长 >3x | LMArena: 4个月估值 $1.7B |
| 🆕 category_innovation | 首创新品类 | World Labs: 首个商用世界模型 |
| 🔥 community_buzz | HN/Reddit 爆火但产品还小 | - |

**5 分**: 融资 >$100M 或 顶级创始人背景 或 品类开创者
**4 分**: 融资 >$30M 或 YC/a16z 背书 或 ARR >$10M

---

## 潜力股评分标准 (2-3 分) - 只需满足 1 条

**3 分**: 融资 $1M-$5M 或 ProductHunt Top 10 或 本地市场热度高
**2 分**: 刚发布、有明显创新但数据不足

---

## 关键：why_matters 质量要求

❌ **拒绝** 泛化描述：
- "这是一个很有潜力的 AI 产品"
- "值得关注"
- "团队背景不错"
- "融资情况良好"

✅ **必须** 有具体数字和差异化：
- "Sequoia 领投 $50M A轮，8个月 ARR 从0到 $10M，首个 AI 原生代码编辑器"
- "前 OpenAI 联创，专注安全 AGI，首轮融资即 $1B 估值"

---

## 关键：公司官网 URL 提取！

上面的搜索结果是新闻文章 URL，不是公司官网。
你必须从文章内容中提取公司的官方网站：

1. 在 snippet 文本中查找公司官网（如"访问 example.com"）
2. 对于常见模式：{{公司名}}.com, {{公司名}}.ai, {{公司名}}.io
3. 如果确定公司名称，可以推断 URL

示例：
- "月之暗面" → website: "https://moonshot.cn"
- "智谱AI" → website: "https://zhipuai.cn"
- "百川智能" → website: "https://baichuan-ai.com"

⚠️ 如果无法确定有效官网，仍然收录但设置：
   "website": "unknown" 和 "needs_verification": true

source_url 字段应填入搜索结果中的新闻文章 URL。

## 输出格式（仅返回 JSON）

返回 JSON 数组。如果没有符合条件的产品，返回 `[]`。

```json
[
  {{
    "name": "产品名称",
    "website": "https://公司官网.com",  // 必须从搜索结果中提取!
    "description": "一句话中文描述（>20字）",
    "category": "coding|image|video|voice|writing|hardware|finance|education|healthcare|agent|other",
    "region": "{region}",
    "funding_total": "$50M A轮",
    "dark_horse_index": 4,
    "criteria_met": ["funding_signal", "category_innovation"],
    "why_matters": "具体数字 + 具体差异化",
    "latest_news": "2026-01: 事件描述",
    "source": "36氪",
    "source_url": "https://36kr.com/文章链接",  // 文章 URL
    "confidence": 0.85
  }}
]
```

---

## 当前配额
- 🦄 黑马 (4-5分): 剩余 {quota_dark_horses} 个
- ⭐ 潜力股 (2-3分): 剩余 {quota_rising_stars} 个

**质量优先，宁缺毋滥。没有符合条件的产品就返回空数组。**"""


# ─────────────────────────────────────────────────────────────────────────────
# 单独评分 Prompt (用于 fallback 或二次评分)
# ─────────────────────────────────────────────────────────────────────────────

SCORING_PROMPT = """评估以下 AI 产品的"黑马指数"(1-5分)：

## 产品信息
{product}

## 评分标准

| 分数 | 标准 |
|------|------|
| **5分** | 融资 >$100M 或 顶级创始人 (前 OpenAI/Google 高管) 或 品类开创者 或 ARR >$50M |
| **4分** | 融资 >$30M 或 YC/a16z 投资 或 估值增长 >3x 或 ARR >$10M |
| **3分** | 融资 $5M-$30M 或 ProductHunt Top 5 或 本地市场热度高 |
| **2分** | 有创新点但数据不足 或 早期产品有潜力 |
| **1分** | 边缘产品 或 待验证 或 信息太少 |

## 返回格式（仅 JSON）

```json
{{
  "dark_horse_index": 4,
  "criteria_met": ["funding_signal", "founder_background"],
  "reason": "评分理由（具体说明依据）"
}}
```"""


# ─────────────────────────────────────────────────────────────────────────────
# 翻译/本地化 Prompt
# ─────────────────────────────────────────────────────────────────────────────

TRANSLATION_PROMPT = """将以下 AI 产品信息翻译成中文，保持专业术语：

{content}

要求：
1. 产品名保持英文
2. 融资金额保持美元格式 ($XXM)
3. description 和 why_matters 翻译成自然的中文
4. 只返回翻译后的 JSON，不要其他内容"""


# ═══════════════════════════════════════════════════════════════════════════════
# Prompt 选择器
# ═══════════════════════════════════════════════════════════════════════════════

def get_analysis_prompt(
    region_key: str,
    search_results: str,
    quota_dark_horses: int = 5,
    quota_rising_stars: int = 10,
    region_flag: Optional[str] = None
) -> str:
    """
    获取并填充分析 Prompt
    
    Args:
        region_key: 地区代码 (cn/us/eu/jp/kr/sea)
        search_results: 格式化的搜索结果文本
        quota_dark_horses: 黑马剩余配额
        quota_rising_stars: 潜力股剩余配额
        region_flag: 地区标识 emoji (可选)
        
    Returns:
        填充后的 prompt
    """
    # 选择语言版本
    if region_key == "cn":
        template = ANALYSIS_PROMPT_CN
    else:
        template = ANALYSIS_PROMPT_EN
    
    # 地区标识映射
    region_flags = {
        "us": "🇺🇸",
        "cn": "🇨🇳",
        "eu": "🇪🇺",
        "jp": "🇯🇵",
        "kr": "🇰🇷",
        "sea": "🇸🇬",
    }
    
    region = region_flag or region_flags.get(region_key, "🌍")
    
    # 填充模板
    return template.format(
        search_results=search_results[:15000],  # 限制长度
        region=region,
        quota_dark_horses=quota_dark_horses,
        quota_rising_stars=quota_rising_stars,
    )


def get_scoring_prompt(product: dict) -> str:
    """
    获取单独评分 Prompt
    
    Args:
        product: 产品信息字典
        
    Returns:
        填充后的 prompt
    """
    import json
    return SCORING_PROMPT.format(
        product=json.dumps(product, ensure_ascii=False, indent=2)
    )


def get_translation_prompt(content: str) -> str:
    """
    获取翻译 Prompt
    
    Args:
        content: 要翻译的内容
        
    Returns:
        填充后的 prompt
    """
    return TRANSLATION_PROMPT.format(content=content)


# ═══════════════════════════════════════════════════════════════════════════════
# 质量验证规则
# ═══════════════════════════════════════════════════════════════════════════════

# 已知名产品排除名单
WELL_KNOWN_PRODUCTS = {
    # 国际
    "chatgpt", "openai", "claude", "anthropic", "gemini", "bard",
    "copilot", "github copilot", "dall-e", "dall-e 3", "sora",
    "midjourney", "stable diffusion", "stability ai",
    "cursor", "perplexity", "elevenlabs", "eleven labs",
    "synthesia", "runway", "runway ml", "pika", "pika labs",
    "bolt.new", "bolt", "v0.dev", "v0", "replit", "together ai", "groq",
    "character.ai", "character ai", "jasper", "jasper ai",
    "notion ai", "grammarly", "copy.ai", "writesonic",
    "huggingface", "hugging face", "langchain", "llamaindex",
    # 中国
    "kimi", "月之暗面", "moonshot", "doubao", "豆包", "字节跳动",
    "tongyi", "通义千问", "通义", "qwen", "wenxin", "文心一言", "文心",
    "ernie", "百度", "baidu", "智谱", "zhipu", "chatglm", "glm",
    "讯飞星火", "星火", "spark", "minimax", "abab",
}

# 泛化 why_matters 黑名单
GENERIC_WHY_MATTERS = [
    "很有潜力", "值得关注", "有前景", "表现不错",
    "团队背景不错", "融资情况良好", "市场前景广阔",
    "技术实力强", "用户反馈良好", "增长迅速",
    "promising", "worth watching", "strong potential",
]


# ─────────────────────────────────────────────────────────────────────────────
# 导出
# ─────────────────────────────────────────────────────────────────────────────

__all__ = [
    "ANALYSIS_PROMPT_EN",
    "ANALYSIS_PROMPT_CN",
    "SCORING_PROMPT",
    "TRANSLATION_PROMPT",
    "get_analysis_prompt",
    "get_scoring_prompt",
    "get_translation_prompt",
    "WELL_KNOWN_PRODUCTS",
    "GENERIC_WHY_MATTERS",
]
