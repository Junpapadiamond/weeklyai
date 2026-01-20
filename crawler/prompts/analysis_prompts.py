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


# ═══════════════════════════════════════════════════════════════════════════════
# 硬件产品评判体系 (Hardware Dark Horse Index)
# ═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# 硬件类别定义
# ─────────────────────────────────────────────────────────────────────────────

HARDWARE_CATEGORIES = {
    "ai_chip": "AI 芯片/加速器 (AI Chip/Accelerator)",
    "robotics": "机器人/人形机器人 (Robotics/Humanoid)",
    "edge_ai": "边缘 AI 设备 (Edge AI Device)",
    "smart_glasses": "AI 眼镜/AR 设备 (AI Glasses/AR)",
    "wearables": "AI 可穿戴设备 (AI Wearables)",
    "smart_home": "智能家居 AI (Smart Home AI)",
    "automotive": "智能汽车/自动驾驶 (Automotive AI)",
    "drone": "AI 无人机 (AI Drone)",
    "medical_device": "AI 医疗设备 (AI Medical Device)",
    "other_hardware": "其他 AI 硬件 (Other AI Hardware)",
}

# ─────────────────────────────────────────────────────────────────────────────
# 硬件评分标准（宽松版 - 重创新轻融资）
# ─────────────────────────────────────────────────────────────────────────────

HARDWARE_SCORING_CRITERIA = """
## 🔧 硬件产品评分标准 (Hardware Index) - 宽松版

> 核心理念：硬件产品重在「创新性」和「灵感启发」，而非严格的融资门槛
> 硬件创业门槛高、周期长，很多创新产品来自小团队，同样值得关注

### 5分 - 硬件明星 (满足任意 1 条即可)

| 维度 | 信号 | 示例 |
|------|------|------|
| 💰 hardware_funding | 融资 >$100M | Etched: $500M, Figure: $675M |
| 🏆 industry_award | CES/MWC 等行业大奖 | Rabbit R1: CES Best of Innovation |
| 🏭 mass_production | 规模量产 (>1000台) | Unitree: 已交付 1000+ 台 |
| 🤝 strategic_partner | 大厂战略合作 | Figure: BMW 工厂部署 |

### 4分 - 硬件黑马 (满足任意 1 条即可)

| 维度 | 信号 | 示例 |
|------|------|------|
| 🚀 prototype_demo | 有实际工作产品演示 | 不只是概念图 |
| 📺 ces_showcase | CES/MWC/ProductHunt 曝光 | - |
| 💵 any_funding | 获得任何机构融资 | 硬件能融到钱就不容易 |
| 👤 hardware_founder | 创始人有硬件背景 | 前 Apple/Tesla/Nvidia |

### 3分 - 硬件潜力 (满足任意 1 条即可)

- 💡 产品形态有创新（新的 AI 交互方式）
- 🎯 解决明确用户痛点
- 🔧 有工作原型或 demo 视频
- 🌐 众筹平台表现不错（Kickstarter/Indiegogo）

### 2分 - 硬件观察

- 概念阶段但想法有趣
- 早期团队但方向清晰
- 技术有亮点但产品未成型
- 值得持续关注
"""

# ─────────────────────────────────────────────────────────────────────────────
# 硬件产品分析 Prompt
# ─────────────────────────────────────────────────────────────────────────────

HARDWARE_ANALYSIS_PROMPT = """你是 WeeklyAI 的 AI 硬件产品分析师。

## 你的任务
从以下搜索结果中提取 **AI 硬件产品**信息，并使用硬件专用评分标准进行评分。

## 搜索结果
{search_results}

---

## 硬件类别

| 代码 | 类别 |
|------|------|
| ai_chip | AI 芯片/加速器 (NPU, TPU, 推理芯片) |
| robotics | 机器人/人形机器人 (工业机器人, 服务机器人) |
| edge_ai | 边缘 AI 设备 (AI 盒子, 开发板) |
| smart_glasses | AI 眼镜/AR 设备 |
| wearables | AI 可穿戴设备 (智能戒指, AI 徽章) |
| smart_home | 智能家居 AI (AI 音箱, AI 摄像头) |
| automotive | 智能汽车/自动驾驶芯片 |
| drone | AI 无人机 |
| medical_device | AI 医疗设备 |
| other_hardware | 其他 AI 硬件 |

---

{hardware_scoring}

---

## 严格排除

### 1. 已知名硬件
Nvidia GPU, Apple Vision Pro, Meta Quest, Tesla FSD, DJI 无人机

### 2. 大厂产品
Google Pixel, Amazon Echo, Apple AirPods, 华为/小米智能设备

### 3. 纯软件产品
App, SaaS, 云服务 (本 prompt 专门用于硬件)

---

## 关键：硬件 why_matters 要求

❌ **拒绝** 泛化描述：
- "创新的 AI 硬件"
- "下一代智能设备"

✅ **必须** 有具体硬件指标：
- "CES 2026 创新奖，已与富士康签约量产，预售 5 万台"
- "自研 AI 芯片，推理性能是 Nvidia A100 的 20 倍，能耗降低 80%"
- "人形机器人，已在 BMW 工厂部署 100 台，单台售价 $16,000"

---

## 输出格式（仅返回 JSON）

```json
[
  {{
    "name": "产品名称",
    "website": "https://公司官网",
    "description": "一句话描述（含核心硬件参数）",
    "category": "hardware",
    "hardware_category": "robotics|ai_chip|edge_ai|smart_glasses|wearables|...",
    "region": "{region}",
    "funding_total": "$200M Series B",
    "dark_horse_index": 5,
    "criteria_met": ["mass_production", "strategic_partner"],
    "hardware_specs": {{
      "form_factor": "人形机器人",
      "key_tech": "双足行走+灵巧手",
      "manufacturing_partner": "BMW",
      "unit_price": "$16,000",
      "units_deployed": 100
    }},
    "why_matters": "CES 2026 最佳创新奖，BMW 独家合作，单台成本降至 $16K",
    "latest_news": "2026-01: CES 2026 发布量产版",
    "source": "The Verge",
    "confidence": 0.9
  }}
]
```

---

## 当前配额
- 🔧 硬件黑马 (4-5分): {quota_dark_horses} 个
- ⭐ 硬件潜力股 (2-3分): {quota_rising_stars} 个

**硬件评估重点：量产能力 > 技术炫酷 > 融资金额**"""


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

# 硬件特有的 criteria 验证
HARDWARE_CRITERIA = {
    "mass_production": "已量产或即将量产",
    "hardware_funding": "硬件融资 >$200M",
    "strategic_partner": "大厂战略合作",
    "industry_award": "CES/行业大奖",
    "pre_order": "预售火爆",
    "prototype_demo": "工作原型演示",
    "hardware_seed": "种子轮 >$50M",
    "manufacturing": "明确制造合作",
    "ces_showcase": "CES/MWC 展示",
    "hardware_founder": "硬件大厂创始人",
}


def validate_hardware_product(product: dict) -> tuple[bool, str]:
    """
    验证硬件产品质量（宽松版 - 重创新轻融资）
    
    Args:
        product: 产品信息字典
        
    Returns:
        (是否通过, 原因)
    """
    name = product.get("name", "").lower()
    
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
    
    # 只有 5 分产品需要至少 1 条标准
    criteria = product.get("criteria_met", [])
    if score == 5 and len(criteria) < 1:
        return False, f"5-star hardware needs ≥1 criteria (has {len(criteria)})"
    
    # 检查 why_matters 是否说明了创新点（宽松版）
    why_matters = product.get("why_matters", "")
    
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
    "get_analysis_prompt",
    "get_scoring_prompt",
    "get_translation_prompt",
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
