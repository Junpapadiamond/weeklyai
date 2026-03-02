#!/usr/bin/env python3
"""
分析 Prompt 模块

职责：从搜索结果中提取 AI 产品信息并评分

设计原则：
1. 结构化输出 (严格 JSON 格式)
2. 具体的评分标准 (黑马 4-5 分 / 潜力股 2-3 分)
3. 质量红线 (why_matters 必须有具体数字)
4. 明确的排除名单 (已知名产品、大厂产品、开发库)
5. 硬件产品专用评判体系 (Hardware Dark Horse Index)
"""

from typing import Optional
from urllib.parse import urlparse

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

## CRITICAL: Company Country Verification

- `region` is the search market flag injected by system, **not** the company nationality.
- Infer company headquarters/origin country from evidence in search results.
- Fill `company_country` with ISO code or country name (e.g. `US`, `United States`, `中国`).
- If evidence is insufficient, set `company_country` to `"unknown"` and confidence ≤ 0.5.

## Output Format (JSON ONLY)

Return a JSON array. If no qualifying products found, return `[]`.
Keep `description/why_matters/latest_news` compatible with existing fields, and always provide `*_en` English counterparts when possible.

```json
[
  {{
    "name": "Product Name",
    "website": "https://company-website.com",  // MUST be from search results!
    "description": "One-sentence description in source language or Chinese for compatibility (>20 chars, primary field)",
    "description_en": "One-sentence description in English (>20 chars)",
    "category": "coding|image|video|voice|writing|hardware|finance|education|healthcare|agent|other",
    "region": "{region}",
    "funding_total": "$50M Series A",
    "dark_horse_index": 4,
    "criteria_met": ["funding_signal", "category_innovation"],
    "why_matters": "Specific numbers + specific differentiation (source language / Chinese for compatibility)",
    "why_matters_en": "Specific numbers + specific differentiation (in English)",
    "latest_news": "2026-01: Event description (optional)",
    "latest_news_en": "2026-01: Event description (English, optional)",
    "source": "TechCrunch",
    "source_url": "https://techcrunch.com/article-url",  // Article URL from search results
    "company_country": "US",
    "company_country_confidence": 0.9,
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
- "百川智能" → website: "https://baichuan-ai.com"

⚠️ 如果无法确定有效官网，仍然收录但设置：
   "website": "unknown" 和 "needs_verification": true

source_url 字段应填入搜索结果中的新闻文章 URL。

## 关键：公司国籍校验

- `region` 是系统注入的“搜索市场”标识，**不是**公司国籍。
- 需要根据搜索结果证据判断公司总部/注册地国家，写入 `company_country`。
- `company_country` 支持 ISO 国家码或国家名称（如 `US` / `United States` / `中国`）。
- 若证据不足，必须填 `"company_country": "unknown"`，并将置信度设为 ≤ 0.5。

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
    "company_country": "CN",
    "company_country_confidence": 0.9,
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


TRANSLATION_TO_EN_PROMPT = """Translate the following AI product JSON fields into natural professional English.

{content}

Requirements:
1. Keep product/company/model names unchanged.
2. Preserve numbers, currencies, and dates exactly.
3. Translate description / why_matters / latest_news only.
4. Return JSON only, no markdown or extra text.
5. For missing source fields, do not invent content."""


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


def get_translation_to_en_prompt(content: str) -> str:
    """
    获取翻译到英文 Prompt

    Args:
        content: 要翻译的内容

    Returns:
        填充后的 prompt
    """
    return TRANSLATION_TO_EN_PROMPT.format(content=content)


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
    "ernie", "百度", "baidu",
    "讯飞星火", "星火", "spark", "minimax", "abab",
}

# 泛化 why_matters 黑名单
GENERIC_WHY_MATTERS = [
    "很有潜力", "值得关注", "有前景", "表现不错",
    "团队背景不错", "融资情况良好", "市场前景广阔",
    "技术实力强", "用户反馈良好", "增长迅速",
    "promising", "worth watching", "strong potential",
]


# ═══════════════════════════════════════════════════════════════════════════════
# 硬件产品评判体系 (Hardware Dark Horse Index)
# ═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# 硬件类别定义
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# 硬件类型：创新型 vs 传统型
# ─────────────────────────────────────────────────────────────────────────────

HARDWARE_TYPES = {
    "innovative": "创新形态硬件 (Innovative Form Factor)",  # 重点发掘
    "traditional": "传统硬件 (Traditional Hardware)",       # 芯片/机器人等
}

# ─────────────────────────────────────────────────────────────────────────────
# 创新特征标签 (Innovation Traits)
# ─────────────────────────────────────────────────────────────────────────────

INNOVATION_TRAITS = {
    # 形态创新 (最重要)
    "non_traditional_form": "非传统形态 (不是手机/平板/手表/耳机)",
    "new_form_factor": "新载体形态 (吊坠/别针/戒指/卡片/眼镜/玩偶等)",
    "wearable": "可穿戴",
    "portable": "便携随身",
    "ambient": "环境融入型",
    
    # 使用场景 (第二重要)
    "single_use_case": "专注单一场景",
    "companion": "情感陪伴",
    "productivity": "生产力 (会议/笔记)",
    "memory": "记忆辅助",
    "health": "健康监测",
    "lifestyle": "生活方式",
    
    # 交互创新
    "voice_first": "语音优先",
    "screenless": "无屏幕",
    "proactive_ai": "主动式 AI",
    "always_on": "Always-on listening",
    "gesture": "手势交互",
    "haptic": "触觉反馈",
    
    # 商业模式
    "affordable": "价格亲民 (<$300)",
    "no_subscription": "无订阅",
    "crowdfunding": "众筹产品",
    
    # 热度信号
    "social_buzz": "社交媒体热度",
    "media_coverage": "科技媒体报道",
    "viral": "现象级爆火",
}

# ─────────────────────────────────────────────────────────────────────────────
# 使用场景 (Use Cases)
# ─────────────────────────────────────────────────────────────────────────────

USE_CASES = {
    "emotional_companion": "情感陪伴 (Friend Pendant)",
    "meeting_notes": "会议录音/笔记 (Limitless, Plaud)",
    "memory_assistant": "记忆辅助 (Legend Memory)",
    "life_logging": "生活记录 (Looki)",
    "health_monitoring": "健康监测",
    "productivity": "生产力工具",
    "accessibility": "无障碍辅助",
    "entertainment": "娱乐/游戏",
    "education": "教育学习",
    "pet_care": "宠物照护",
    "child_safety": "儿童安全",
    "other": "其他场景",
}

# ─────────────────────────────────────────────────────────────────────────────
# 传统硬件类别 (保留用于芯片/机器人等)
# ─────────────────────────────────────────────────────────────────────────────

HARDWARE_CATEGORIES = {
    "ai_chip": "AI 芯片/加速器",
    "robotics": "机器人/人形机器人",
    "edge_ai": "边缘 AI 设备",
    "smart_glasses": "AI 眼镜/AR",
    "smart_home": "智能家居",
    "automotive": "智能汽车",
    "drone": "AI 无人机",
    "medical_device": "AI 医疗设备",
    "other": "其他硬件",
}

# ─────────────────────────────────────────────────────────────────────────────
# 硬件评分标准（宽松版 - 重创新轻融资）
# ─────────────────────────────────────────────────────────────────────────────

HARDWARE_SCORING_CRITERIA = """
## 🔧 创新硬件评分标准 - 形态创新 + 使用场景优先

> **核心理念**：
> 1. 「形态创新」最重要 - 是否是新的 AI 载体形态？
> 2. 「使用场景」第二重要 - 是否专注解决一个具体问题？
> 3. 其他因素：社交热度、价格、交互方式

---

### 评分维度权重

| 优先级 | 维度 | 权重 | 说明 |
|--------|------|------|------|
| 1️⃣ | **形态创新** | 40% | 是否是新的 AI 载体？非手机/平板/传统手表 |
| 2️⃣ | **使用场景** | 30% | 是否专注单一场景？场景是否有价值？ |
| 3️⃣ | **热度信号** | 15% | 社交媒体/众筹/媒体报道 |
| 4️⃣ | **商业可行** | 15% | 价格亲民/已发货/有融资 |

---

### 5分 - 现象级创新硬件

满足以下组合：
- ✅ 形态创新 (非传统形态) + 场景清晰 + 任意1条热度信号
- 或 ✅ 被大厂收购/战略合作
- 或 ✅ 融资 >$100M (传统硬件)

示例：Friend Pendant (新形态+陪伴场景+Twitter爆火), Limitless (被Meta收购)

### 4分 - 硬件黑马 ⭐ 重点发掘

满足以下任意组合：
- ✅ 形态创新 + 场景清晰
- ✅ 形态创新 + 已发货/预售
- ✅ 形态创新 + 众筹成功 (>300%)
- ✅ 场景清晰 + 社交热度/媒体报道

示例：Plaud NotePin (别针+会议), Vocci (戒指+会议), iBuddi (徽章+陪伴)

### 3分 - 硬件潜力

满足以下任意 1 条：
- 💡 有形态创新 (新载体形式)
- 🎯 有明确使用场景
- 🔧 有工作原型/demo
- 🌐 众筹进行中
- 🎨 设计/交互有亮点

### 2分 - 硬件观察

- 概念阶段但想法有趣
- 早期但方向清晰
- ProductHunt 新发布
- 社交媒体有讨论

---

### 创新特征标签 (innovation_traits)

输出时请标注产品具有的特征：

**形态创新类**：non_traditional_form, new_form_factor, wearable, portable, ambient
**场景类**：single_use_case, companion, productivity, memory, health, lifestyle
**交互类**：voice_first, screenless, proactive_ai, always_on, gesture, haptic
**商业类**：affordable, no_subscription, crowdfunding
**热度类**：social_buzz, media_coverage, viral
"""

# ─────────────────────────────────────────────────────────────────────────────
# 硬件产品分析 Prompt
# ─────────────────────────────────────────────────────────────────────────────

HARDWARE_ANALYSIS_PROMPT = """你是 WeeklyAI 的 AI 创新硬件分析师。

## 你的任务
从以下搜索结果中提取 **创新 AI 硬件产品**，重点发掘形态创新的产品。

## 搜索结果
{search_results}

---

## 硬件分类

### 创新形态硬件 (hardware_type: "innovative") ⭐ 重点发掘

不限制具体形态，只要是**非传统计算设备**的新 AI 载体都算：
- 可穿戴：吊坠、别针、戒指、眼镜、耳夹、手环、发卡、领带夹...
- 随身携带：卡片、钥匙扣、手机配件...
- 桌面/家居：AI 相框、台灯、镜子、玩偶、闹钟...
- 特定场景：宠物项圈、儿童手表、运动装备...
- 任何你觉得有趣的新形态！

### 传统硬件 (hardware_type: "traditional")

芯片、机器人、无人机、汽车等传统硬件品类。

---

{hardware_scoring}

---

## 严格排除

- 已知名：Nvidia GPU, Apple Vision Pro, Meta Quest, Tesla, DJI
- 大厂产品：Echo, AirPods, Pixel, 华为/小米智能设备
- 传统形态：普通智能手表、普通耳机、普通音箱
- 纯软件：App, SaaS, 云服务

---

## 输出格式（仅返回 JSON）

```json
[
  {{
    "name": "产品名称",
    "website": "https://官网",
    "description": "一句话描述",
    "category": "hardware",
    "hardware_type": "innovative",
    "form_factor": "pendant",
    "use_case": "emotional_companion",
    "innovation_traits": ["non_traditional_form", "voice_first", "affordable", "social_buzz"],
    "region": "{region}",
    "funding_total": "$10M",
    "price": "$99",
    "dark_horse_index": 4,
    "criteria_met": ["form_innovation", "use_case_clear", "social_buzz"],
    "why_matters": "AI 伴侣吊坠，Claude 驱动，$99 无订阅，Twitter 现象级爆火",
    "latest_news": "2026-01: 出货量达 10 万台",
    "source": "Wired",
    "source_url": "https://wired.com/article-url",
    "company_country": "US",
    "company_country_confidence": 0.9,
    "confidence": 0.85
  }}
]
```

## 关键：公司国籍校验

- `region` 是搜索市场标识，不是公司国籍。
- 需要根据搜索结果中的证据填 `company_country`（ISO 码或国家名）。
- 证据不足时，填 `"company_country": "unknown"` 且置信度 ≤ 0.5。

## 关键：公司官网 URL 提取！

上面的搜索结果是新闻/帖子 URL，不是公司官网。
你必须从结果中提取公司的官方网站：

1. 在 snippet 文本中查找公司官网（如"访问 example.com"）
2. 对于常见模式：{{公司名}}.com / .ai / .io
3. 如果不确定，设置：
   "website": "unknown", "needs_verification": true

⚠️ 禁止使用占位域名（example.com / test.com / placeholder），这些会被判为无效。

## 关键：source_url 必须可追溯

- `source_url` 字段**必须**精确复制自上方搜索结果中的 URL（新闻/帖子/众筹链接）。
- 不允许编造 `source_url`；如果找不到可对应的 URL，就不要输出该产品。

### 字段说明

| 字段 | 说明 | 示例值 |
|------|------|--------|
| hardware_type | 创新型/传统型 | "innovative" / "traditional" |
| form_factor | 自由描述形态 | "pendant", "pin", "ring", "card", "glasses", "plush_toy", "smart_frame"... |
| use_case | 使用场景 | "emotional_companion", "meeting_notes", "memory_assistant", "health_monitoring", "life_logging"... |
| innovation_traits | 创新特征标签数组 | ["non_traditional_form", "voice_first", "single_use_case", "affordable", "social_buzz"...] |
| price | 产品价格 | "$99", "$169", "unknown" |

---

## 当前配额
- 🔧 创新硬件黑马 (4-5分): {quota_dark_horses} 个
- ⭐ 硬件潜力股 (2-3分): {quota_rising_stars} 个

**评估重点：形态创新 (40%) > 使用场景 (30%) > 热度信号 (15%) > 商业可行 (15%)**"""


def get_hardware_analysis_prompt(
    search_results: str,
    region: str = "🌍",
    quota_dark_horses: int = 5,
    quota_rising_stars: int = 10,
) -> str:
    """
    获取硬件产品专用分析 Prompt
    
    Args:
        search_results: 搜索结果文本
        region: 地区标识
        quota_dark_horses: 黑马配额
        quota_rising_stars: 潜力股配额
        
    Returns:
        填充后的硬件分析 prompt
    """
    return HARDWARE_ANALYSIS_PROMPT.format(
        search_results=search_results[:15000],
        region=region,
        hardware_scoring=HARDWARE_SCORING_CRITERIA,
        quota_dark_horses=quota_dark_horses,
        quota_rising_stars=quota_rising_stars,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 硬件产品验证规则
# ─────────────────────────────────────────────────────────────────────────────

# 已知名硬件排除名单
WELL_KNOWN_HARDWARE = {
    # 芯片
    "nvidia", "nvidia gpu", "nvidia a100", "nvidia h100", "nvidia b200",
    "intel", "amd", "qualcomm", "apple m1", "apple m2", "apple m3",
    # AR/VR
    "apple vision pro", "meta quest", "meta quest 3", "pico",
    # 机器人
    "boston dynamics", "spot", "atlas",
    # 消费电子
    "iphone", "pixel", "galaxy", "echo", "alexa", "homepod", "nest",
    # 汽车
    "tesla", "tesla fsd", "waymo",
    # 无人机
    "dji", "dji mavic", "dji mini",
}

# 硬件官网占位域名（无效）
PLACEHOLDER_DOMAINS = {
    "example.com", "example.org", "example.net",
    "test.com", "localhost", "example.cn", "example.ai",
}

# 硬件评分 criteria (按权重排序)
HARDWARE_CRITERIA = {
    # ═══ 形态创新 (权重 40%) - 最重要 ═══
    "form_innovation": "非传统形态 (新的 AI 载体)",
    "non_traditional_form": "不是手机/平板/传统手表/耳机",
    "new_form_factor": "新载体形态 (吊坠/别针/戒指/卡片/玩偶/相框...)",
    
    # ═══ 使用场景 (权重 30%) - 第二重要 ═══
    "use_case_clear": "明确的使用场景",
    "single_use_case": "专注单一场景 (不追求万能)",
    "solves_real_problem": "解决真实问题",
    
    # ═══ 热度信号 (权重 15%) ═══
    "social_buzz": "社交媒体热度 (Twitter/TikTok)",
    "viral": "现象级爆火",
    "media_coverage": "科技媒体报道",
    "crowdfunding_success": "众筹成功 (>300%)",
    
    # ═══ 商业可行 (权重 15%) ═══
    "shipping": "已发货或预售中",
    "affordable": "价格亲民 (<$300)",
    "no_subscription": "无订阅费",
    "has_funding": "有融资",
    "acquired": "被大厂收购",
    
    # ═══ 传统硬件专用 ═══
    "mass_production": "规模量产",
    "hardware_funding": "硬件融资 >$100M",
    "strategic_partner": "大厂战略合作",
    "industry_award": "CES/MWC 大奖",
}


def validate_hardware_product(product: dict) -> tuple[bool, str]:
    """
    验证硬件产品质量（宽松版 - 重创新轻融资）
    
    Args:
        product: 产品信息字典
        
    Returns:
        (是否通过, 原因)
    """
    name_raw = product.get("name", "").strip()
    name = name_raw.lower()
    description = product.get("description", "").strip()
    why_matters = product.get("why_matters", "").strip()
    website = product.get("website", "").strip()

    # 基本必填字段
    if not name_raw:
        return False, "missing name"
    if not description:
        return False, "missing description"
    if not why_matters:
        return False, "missing why_matters"
    if not website:
        return False, "missing website"

    # ── 博客标题/通用概念名检查 ──
    blog_markers = ["：", "？", "！", "如何", "什么是", "为什么", "风口", "趋势"]
    if len(name_raw) > 10 and any(m in name_raw for m in blog_markers):
        return False, f"name looks like blog title: {name_raw}"

    generic_concepts = [
        "ai随身设备", "ai智能助手", "智能穿戴设备", "ai硬件",
        "ai眼镜", "ai助手", "智能硬件", "ai可穿戴",
    ]
    if name in generic_concepts or any(name.startswith(gc) for gc in generic_concepts):
        return False, f"name is generic concept: {name_raw}"

    # ── 不可信 source 检查 ──
    source_lower = product.get("source", "").strip().lower()
    untrusted = ["楽天市場", "rakuten", "眼鏡市場", "amazon", "youtube",
                 "bilibili", "tiktok", "淘宝", "京东", "twitter"]
    if any(u.lower() in source_lower for u in untrusted):
        return False, f"untrusted source: {source_lower}"

    # 过滤「新闻标题式」name（GLM 更容易把文章标题当成产品名）
    headline_patterns = [
        "融资", "宣布", "发布", "获得", "完成", "推出", "上线",
        "投资", "领投", "参投", "被投", "收购", "估值",
        "独家", "爆料", "报道", "曝光", "传出", "消息", "传闻",
    ]
    if any(p in name_raw for p in headline_patterns) and len(name_raw) >= 8:
        return False, "name looks like news headline"

    # 修复缺少协议的 URL
    if not website.startswith(("http://", "https://")) and "." in website:
        website = f"https://{website}"
        product["website"] = website

    if website.lower() == "unknown":
        # Allow unknown website for early hardware signals, but enforce manual verification downstream.
        product["needs_verification"] = True
    elif not website.startswith(("http://", "https://")):
        return False, "invalid website URL"
    else:
        domain = urlparse(website).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        if any(ph == domain or domain.endswith(f".{ph}") for ph in PLACEHOLDER_DOMAINS):
            return False, f"invalid website domain: {domain}"
    
    # 检查是否是已知名硬件
    for known in WELL_KNOWN_HARDWARE:
        if known in name or name in known:
            return False, f"well-known hardware: {known}"
    
    # 检查是否有硬件类别（宽松：只要标记为硬件即可）
    hw_category = product.get("hardware_category", "")
    is_hardware = product.get("is_hardware", False)
    category = product.get("category", "")
    
    if not hw_category and category != "hardware" and not is_hardware:
        return False, "not a hardware product"
    
    # 宽松版：硬件产品只需要满足基本要求即可
    # 不再强制要求 criteria 数量
    score = product.get("dark_horse_index", 0)
    try:
        score = int(float(score))
    except Exception:
        score = 0
    
    # 只有 5 分产品需要至少 1 条标准
    criteria = product.get("criteria_met", [])
    if score == 5 and len(criteria) < 1:
        return False, f"5-star hardware needs ≥1 criteria (has {len(criteria)})"
    
    # 检查描述长度（硬件也需基本描述）
    if len(description) < 20:
        return False, f"description too short ({len(description)} chars)"

    # 检查 why_matters 是否说明了创新点（宽松版）
    # 硬件产品只需要有基本描述即可，不强求具体硬件指标
    if score >= 4 and len(why_matters) < 20:
        return False, "hardware why_matters too short (need >20 chars)"
    
    return True, "passed"


# ─────────────────────────────────────────────────────────────────────────────
# 导出
# ─────────────────────────────────────────────────────────────────────────────

__all__ = [
    "ANALYSIS_PROMPT_EN",
    "ANALYSIS_PROMPT_CN",
    "SCORING_PROMPT",
    "TRANSLATION_PROMPT",
    "TRANSLATION_TO_EN_PROMPT",
    "get_analysis_prompt",
    "get_scoring_prompt",
    "get_translation_prompt",
    "get_translation_to_en_prompt",
    "WELL_KNOWN_PRODUCTS",
    "GENERIC_WHY_MATTERS",
    # 硬件相关
    "HARDWARE_CATEGORIES",
    "HARDWARE_SCORING_CRITERIA",
    "HARDWARE_ANALYSIS_PROMPT",
    "get_hardware_analysis_prompt",
    "WELL_KNOWN_HARDWARE",
    "HARDWARE_CRITERIA",
    "validate_hardware_product",
]
