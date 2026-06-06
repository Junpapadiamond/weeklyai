#!/usr/bin/env python3
"""
WeeklyAI v2 analysis prompts.

The v2 target is not "well-funded AI startup." It is one product per day
that someone interested in AI would stop scrolling to inspect.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

HOOK_TYPES = {
    "weird_form",
    "new_behavior",
    "unexpected_combo",
    "quiet_real_problem",
    "new_interaction",
    "niche_depth",
}

HOOK_CLASSIFICATION_FILE = Path(__file__).with_name("hook_classification.md")


@lru_cache(maxsize=1)
def _load_hook_classification() -> str:
    """Load the shared hook taxonomy used by every provider/region prompt."""
    try:
        return HOOK_CLASSIFICATION_FILE.read_text(encoding="utf-8")
    except OSError:
        return "Hook taxonomy unavailable. Use the six allowed hook enum values only."


QUALITY_GATE_EN = """
## Selection Philosophy

WeeklyAI v2 picks one screenshot-worthy AI product per day. Funding is context,
not a gate. Source does not matter: big lab, famous product, unknown indie,
crowdfunding oddity, or niche maker project can all qualify.

The single test: would someone scrolling AI Twitter stop and want to check this
out? If yes, include it. If no, skip it.

Qualifying surprise can be:
- new physical form
- new behavior
- unexpected combination
- new interaction
- quietly solved real problem
- narrow but deep niche execution

The core rubric question: Does this product violate expectations in a productive
way?
"""

QUALITY_GATE_CN = """
## 选择哲学

WeeklyAI v2 每天只挑一个值得截图、值得点进去看的 AI 产品。融资只是背景，不是门槛。
来源不限：大厂、知名产品、独立开发者、众筹怪东西、垂直小工具都可以。

唯一测试：一个刷 AI Twitter / 即刻的人，会不会停下来想点开？会就收，不会就跳过。

合格的惊喜可以来自：
- 新物理形态
- 新行为能力
- 意外组合
- 新交互方式
- 安静解决真实问题
- 很窄但做得很深

核心问题：这个产品有没有用一种有效方式违反预期？
"""

COMMON_EXCLUSIONS_EN = """
## Exclusions and Higher-Bar Rules

Keep excluding:
1. Dev libraries, SDKs, model repos, raw GitHub projects, papers-only demos.
   Examples: LangChain, PyTorch, TensorFlow, HuggingFace model pages, LlamaIndex.
2. Tool directories and listicles.
   Examples: "best AI tools", "top 10 AI tools", "AI tool collection".
3. Pure model/version/pricing/localization/UI-change announcements.

Do NOT blanket-exclude big tech or well-known products. ChatGPT, Claude, Gemini,
Cursor, OpenAI, Anthropic, Google, Xiaomi, ByteDance, Meta, Apple, Tencent, and
Alibaba can qualify only when THIS launch is genuinely surprising: a new
capability, new behavior, new form, new interaction, or real workflow leap.

Treat industry_leaders.json as a "needs higher bar" list, not a hard exclusion.

For a famous brand, explicitly answer inside why_matters:
"What specifically makes THIS launch surprising vs. normal product evolution?"
"""

COMMON_EXCLUSIONS_CN = """
## 排除与更高门槛

继续排除：
1. 开发库、SDK、模型仓库、只有 GitHub 的项目、只有论文或 demo。
   例如 LangChain、PyTorch、TensorFlow、HuggingFace 模型页、LlamaIndex。
2. 工具目录/合集/盘点。
   例如“最佳 AI 工具”“Top 10 AI tools”“AI 工具合集”。
3. 纯模型版本号、价格、本地化、UI 小改公告。

不要再硬排除大厂或知名产品。ChatGPT、Claude、Gemini、Cursor、OpenAI、
Anthropic、Google、小米、字节、Meta、Apple、腾讯、阿里都可以入选，但只有当
“这次发布”本身代表真正的新能力、新行为、新形态、新交互或真实工作流跃迁时才算。

industry_leaders.json 是“需要更高门槛”的列表，不是硬排除名单。

如果来自知名品牌，必须在 why_matters 里回答：
“这次发布到底哪里令人意外，而不是正常产品演进？”
"""

HOOK_BLOCK = """
## Hook Taxonomy

{hook_classification}
"""

OUTPUT_CONTRACT_EN = """
## Output Rules

Return JSON only. Return `[]` if nothing is screenshot-worthy.

Primary display fields are zh-CN:
- `description`, `why_matters`, `latest_news` must be natural Chinese.
- Also provide English fields when possible: `description_en`, `why_matters_en`, `latest_news_en`.

`why_matters` must be concrete and click-provoking. It should contain the
specific surprise, behavior, form, number, price, source, or observed traction.

Good why_matters examples:
- Small indie: "AI 盆栽 reminds you to water via voice — 5k units on Makuake at ¥8,000. Weird form, real behavior."
- Big lab: "OpenAI quietly shipped Operator-2: ChatGPT can now run your terminal unsupervised for 20-min coding tasks. New behavior, not a version bump."

Bad examples:
- "This is a promising AI product"
- "Worth watching"
- "Strong team background"
- "The company raised funding"

Website rules:
- Prefer official company/product website.
- If an interesting product has no verified official website, keep it with
  `"website": "unknown"` and `"needs_verification": true`.
- `source_url` must be the article, product page, crowdfunding page, or post URL
  from the search results. Do not invent it.

Company country:
- `region` is the search market flag, not company nationality.
- Fill `company_country` from evidence when possible.
- If unsure, use `"company_country": "unknown"` and confidence <= 0.5.

```json
[
  {{
    "name": "Product Name",
    "website": "https://company-website.com",
    "description": "一句话中文描述，说明产品到底是什么",
    "description_en": "One-sentence English description",
    "category": "coding|image|video|voice|writing|hardware|finance|education|healthcare|agent|other",
    "region": "{region}",
    "funding_total": "optional context, not a score",
    "screenshot_worthy": true,
    "hook": "weird_form|new_behavior|unexpected_combo|quiet_real_problem|new_interaction|niche_depth",
    "why_matters": "具体说明为什么这次会让人停下来点开",
    "why_matters_en": "Concrete reason this is surprising/clickable",
    "latest_news": "optional event summary",
    "latest_news_en": "optional English event summary",
    "source": "Source name",
    "source_url": "https://source-url-from-search-results",
    "company_country": "US|CN|unknown",
    "company_country_confidence": 0.9,
    "confidence": 0.85
  }}
]
```
"""

OUTPUT_CONTRACT_CN = """
## 输出规则

只返回 JSON。如果没有 screenshot-worthy 产品，返回 `[]`。

主展示字段是中文：
- `description`、`why_matters`、`latest_news` 必须是自然中文。
- 尽量提供英文对应字段：`description_en`、`why_matters_en`、`latest_news_en`。

`why_matters` 必须具体、有点击欲。它应该包含具体惊喜、行为、形态、数字、价格、
来源或可观察热度。

好的 why_matters 示例：
- 小 indie："AI 盆栽 reminds you to water via voice — 5k units on Makuake at ¥8,000. Weird form, real behavior."
- 大厂："OpenAI quietly shipped Operator-2: ChatGPT can now run your terminal unsupervised for 20-min coding tasks. New behavior, not a version bump."

差的例子：
- “这是一个很有潜力的 AI 产品”
- “值得关注”
- “团队背景不错”
- “融资情况良好”

官网规则：
- 优先填写官方产品/公司网站。
- 如果产品很有意思但官网无法确认，保留它，设置 `"website": "unknown"` 和 `"needs_verification": true`。
- `source_url` 必须来自搜索结果里的文章、产品页、众筹页或帖子 URL，不要编造。

公司国籍：
- `region` 是搜索市场，不是公司国籍。
- 有证据时填写 `company_country`。
- 不确定时填 `"company_country": "unknown"`，置信度 <= 0.5。

```json
[
  {{
    "name": "产品名称",
    "website": "https://公司官网.com",
    "description": "一句话中文描述，说明产品到底是什么",
    "description_en": "One-sentence English description",
    "category": "coding|image|video|voice|writing|hardware|finance|education|healthcare|agent|other",
    "region": "{region}",
    "funding_total": "可选背景，不是评分依据",
    "screenshot_worthy": true,
    "hook": "weird_form|new_behavior|unexpected_combo|quiet_real_problem|new_interaction|niche_depth",
    "why_matters": "具体说明为什么这次会让人停下来点开",
    "why_matters_en": "Concrete reason this is surprising/clickable",
    "latest_news": "可选事件摘要",
    "latest_news_en": "optional English event summary",
    "source": "来源名称",
    "source_url": "https://搜索结果中的来源链接",
    "company_country": "US|CN|unknown",
    "company_country_confidence": 0.9,
    "confidence": 0.85
  }}
]
```
"""

ANALYSIS_PROMPT_EN = f"""You are WeeklyAI's AI Product Discovery Analyst.

## Search Results
{{search_results}}

{QUALITY_GATE_EN}
{COMMON_EXCLUSIONS_EN}
{HOOK_BLOCK}
{OUTPUT_CONTRACT_EN}

Current target: find screenshot-worthy candidates, not fill a quota.
Quality over quantity. Return [] when nothing would make someone click.
"""

ANALYSIS_PROMPT_CN = f"""你是 WeeklyAI 的 AI 产品发现分析师。

## 搜索结果
{{search_results}}

{QUALITY_GATE_CN}
{COMMON_EXCLUSIONS_CN}
{HOOK_BLOCK}
{OUTPUT_CONTRACT_CN}

当前目标：找到值得截图/点开的候选，不是填满配额。
质量优先，宁缺毋滥。没有让人想点开的产品就返回 []。
"""

HARDWARE_ANALYSIS_PROMPT = f"""你是 WeeklyAI 的 AI 创新硬件分析师。

## 搜索结果
{{search_results}}

{QUALITY_GATE_CN}

## 硬件重点

硬件 prompt 的权重不变：
- 形态创新 40%
- 使用场景 30%
- 热度信号 15%
- 商业可行 15%

优先发掘非传统 AI 载体：盆栽、相框、吊坠、镜子、台灯、贴纸、玩偶、宠物项圈、
戒指、眼镜、门铃、徽章、NAS、家居物件等。传统芯片/机器人也可以，但必须有
真正新行为或新交互，不能只是融资新闻。

{COMMON_EXCLUSIONS_CN}
{HOOK_BLOCK}
{OUTPUT_CONTRACT_CN}

硬件字段可额外输出：
- `hardware_type`: "innovative" or "traditional"
- `form_factor`: "plant" / "frame" / "pendant" / "mirror" / "lamp" / ...
- `use_case`: one concise use case
- `innovation_traits`: string array
- `price`: optional
"""

SCORING_PROMPT = """Evaluate whether this AI product is screenshot-worthy.

## Product
{product}

Return JSON only:
```json
{{
  "screenshot_worthy": true,
  "hook": "weird_form|new_behavior|unexpected_combo|quiet_real_problem|new_interaction|niche_depth",
  "reason": "Concrete reason it would make an AI-interested reader click."
}}
```

Reject routine version bumps, pricing changes, localization, minor UI changes,
generic funding news, dev libraries, model repos, and tool directories.
"""

TRANSLATION_PROMPT = """将以下 AI 产品信息翻译成中文，保持专业术语：

{content}

要求：
1. 产品名保持英文
2. description 和 why_matters 翻译成自然中文
3. 不要把 funding 写成入选理由，除非它只是背景
4. 只返回翻译后的 JSON，不要其他内容"""

TRANSLATION_TO_EN_PROMPT = """Translate the following AI product JSON fields into natural professional English.

{content}

Requirements:
1. Keep product/company/model names unchanged.
2. Preserve numbers, currencies, and dates exactly.
3. Translate description / why_matters / latest_news only.
4. Return JSON only, no markdown or extra text.
5. For missing source fields, do not invent content."""

WELL_KNOWN_PRODUCTS = {
    "chatgpt", "openai", "claude", "anthropic", "gemini", "bard",
    "copilot", "github copilot", "dall-e", "sora", "midjourney",
    "stable diffusion", "cursor", "perplexity", "elevenlabs",
    "runway", "pika", "bolt.new", "v0.dev", "replit", "notion ai",
    "grammarly", "kimi", "moonshot", "豆包", "doubao", "通义",
    "qwen", "文心", "百度", "baidu", "讯飞星火",
}

NEEDS_HIGHER_BAR_PRODUCTS = WELL_KNOWN_PRODUCTS

GENERIC_WHY_MATTERS = [
    "很有潜力", "值得关注", "有前景", "表现不错", "团队背景不错",
    "融资情况良好", "市场前景广阔", "技术实力强", "用户反馈良好",
    "promising", "worth watching", "strong potential", "strong team",
]

DEV_LIBRARY_TERMS = {
    "langchain", "llamaindex", "llama index", "pytorch", "tensorflow",
    "huggingface model", "hugging face model", "github repo", "sdk",
}

TOOL_DIRECTORY_TERMS = {
    "best ai tools", "top 10 ai tools", "ai tool collection", "ai tools directory",
    "工具合集", "工具盘点", "最佳 ai 工具",
}

WELL_KNOWN_HARDWARE = {
    "nvidia", "nvidia gpu", "intel", "amd", "qualcomm", "apple vision pro",
    "meta quest", "tesla", "waymo", "dji", "echo", "airpods", "homepod",
}

PLACEHOLDER_DOMAINS = {
    "example.com", "example.org", "example.net", "test.com", "localhost",
    "example.cn", "example.ai",
}

HARDWARE_TYPES = {
    "innovative": "创新形态硬件",
    "traditional": "传统硬件",
}

HARDWARE_CATEGORIES = {
    "ai_chip": "AI 芯片/加速器",
    "robotics": "机器人/人形机器人",
    "edge_ai": "边缘 AI 设备",
    "smart_glasses": "AI 眼镜/AR",
    "smart_home": "智能家居",
    "medical_device": "AI 医疗设备",
    "other": "其他硬件",
}

HARDWARE_CRITERIA = {
    "form_innovation": "非传统形态",
    "new_form_factor": "新载体形态",
    "use_case_clear": "明确使用场景",
    "single_use_case": "专注单一场景",
    "solves_real_problem": "解决真实问题",
    "social_buzz": "社交媒体热度",
    "crowdfunding_success": "众筹成功",
    "shipping": "已发货或预售",
}

HARDWARE_SCORING_CRITERIA = """
形态创新 40% / 使用场景 30% / 热度信号 15% / 商业可行 15%。
输出 screenshot_worthy + hook，不再输出 1-5 分作为核心判断。
"""


def _is_truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _has_bad_term(text: str, terms: set[str]) -> Optional[str]:
    lowered = text.lower()
    for term in terms:
        if term in lowered:
            return term
    return None


def _normalize_website(product: dict, *, allow_unknown: bool) -> tuple[bool, str]:
    website = str(product.get("website") or "").strip()
    if not website or website.lower() == "unknown":
        if allow_unknown:
            product["website"] = "unknown"
            product["needs_verification"] = True
            return True, "website needs verification"
        return False, "missing website"

    if not website.startswith(("http://", "https://")) and "." in website:
        website = f"https://{website}"
        product["website"] = website

    if not website.startswith(("http://", "https://")):
        return False, "invalid website URL"

    domain = urlparse(website).netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    if any(ph == domain or domain.endswith(f".{ph}") for ph in PLACEHOLDER_DOMAINS):
        return False, f"invalid website domain: {domain}"
    return True, "website ok"


def _validate_common_product(product: dict, *, hardware: bool = False) -> tuple[bool, str]:
    name = str(product.get("name") or "").strip()
    description = str(product.get("description") or "").strip()
    why_matters = str(product.get("why_matters") or "").strip()
    source_url = str(product.get("source_url") or "").strip()
    text = " ".join([name, description, why_matters, str(product.get("source") or "")])

    if not name:
        return False, "missing name"
    if not description:
        return False, "missing description"
    if not why_matters:
        return False, "missing why_matters"

    headline_patterns = [
        "融资", "宣布", "发布", "获得", "完成", "推出", "上线", "投资",
        "领投", "参投", "收购", "估值", "独家", "爆料", "报道", "曝光",
        "传出", "消息", "传闻",
    ]
    if len(name) >= 8 and any(pattern in name for pattern in headline_patterns):
        return False, "name looks like news headline"

    if _has_bad_term(text, DEV_LIBRARY_TERMS):
        return False, "dev library/model repo is excluded"
    if _has_bad_term(text, TOOL_DIRECTORY_TERMS):
        return False, "tool directory/listicle is excluded"

    if len(description) < 20:
        return False, f"description too short ({len(description)} chars)"
    if len(why_matters) < (20 if hardware else 30):
        return False, f"why_matters too short ({len(why_matters)} chars)"

    why_lower = why_matters.lower()
    for generic in GENERIC_WHY_MATTERS:
        if generic in why_lower:
            return False, f"generic why_matters: contains '{generic}'"

    hook = str(product.get("hook") or "").strip()
    if hook not in HOOK_TYPES:
        return False, f"invalid hook: {hook or 'missing'}"

    if not _is_truthy(product.get("screenshot_worthy")):
        return False, "not screenshot_worthy"
    product["screenshot_worthy"] = True

    website_ok, website_reason = _normalize_website(product, allow_unknown=True)
    if not website_ok:
        return False, website_reason

    if not source_url:
        product["needs_source_verification"] = True

    confidence = product.get("confidence", 1.0)
    try:
        confidence_float = float(confidence)
    except (TypeError, ValueError):
        confidence_float = 1.0
    if confidence_float < 0.5:
        return False, f"low confidence ({confidence_float:.2f})"

    if not product.get("categories"):
        category = product.get("category") or ("hardware" if hardware else "other")
        product["categories"] = [category]

    # Compatibility fields for legacy sorting and old endpoints.
    product.setdefault("dark_horse_index", 4 if product["screenshot_worthy"] else 2)
    product.setdefault("criteria_met", [hook])
    return True, "passed"


def get_analysis_prompt(
    region_key: str,
    search_results: str,
    quota_dark_horses: int = 5,
    quota_rising_stars: int = 10,
    region_flag: Optional[str] = None,
) -> str:
    template = ANALYSIS_PROMPT_CN if region_key == "cn" else ANALYSIS_PROMPT_EN
    region_flags = {
        "us": "🇺🇸",
        "cn": "🇨🇳",
        "eu": "🇪🇺",
        "jp": "🇯🇵",
        "kr": "🇰🇷",
        "sea": "🇸🇬",
    }
    return template.format(
        search_results=search_results[:15000],
        region=region_flag or region_flags.get(region_key, "🌍"),
        hook_classification=_load_hook_classification(),
        quota_dark_horses=quota_dark_horses,
        quota_rising_stars=quota_rising_stars,
    )


def get_hardware_analysis_prompt(
    search_results: str,
    region: str = "🌍",
    quota_dark_horses: int = 5,
    quota_rising_stars: int = 10,
) -> str:
    return HARDWARE_ANALYSIS_PROMPT.format(
        search_results=search_results[:15000],
        region=region,
        hook_classification=_load_hook_classification(),
        quota_dark_horses=quota_dark_horses,
        quota_rising_stars=quota_rising_stars,
    )


def get_scoring_prompt(product: dict) -> str:
    import json

    return SCORING_PROMPT.format(product=json.dumps(product, ensure_ascii=False, indent=2))


def get_translation_prompt(content: str) -> str:
    return TRANSLATION_PROMPT.format(content=content)


def get_translation_to_en_prompt(content: str) -> str:
    return TRANSLATION_TO_EN_PROMPT.format(content=content)


def validate_product(product: dict) -> tuple[bool, str]:
    return _validate_common_product(product, hardware=False)


def validate_hardware_product(product: dict) -> tuple[bool, str]:
    product.setdefault("category", "hardware")
    product.setdefault("is_hardware", True)

    # Preserve existing test behavior: headline rejection should fire before
    # website verification for hallucinated CN headlines.
    name_raw = str(product.get("name") or "").strip()
    headline_patterns = [
        "融资", "宣布", "发布", "获得", "完成", "推出", "上线", "投资",
        "领投", "参投", "被投", "收购", "估值", "独家", "爆料", "报道",
        "曝光", "传出", "消息", "传闻",
    ]
    if len(name_raw) >= 8 and any(pattern in name_raw for pattern in headline_patterns):
        return False, "name looks like news headline"

    # Compatibility: older hardware candidates may not yet contain v2 fields.
    if "hook" not in product:
        product["hook"] = "weird_form"
    if "screenshot_worthy" not in product:
        product["screenshot_worthy"] = True

    return _validate_common_product(product, hardware=True)


__all__ = [
    "ANALYSIS_PROMPT_EN",
    "ANALYSIS_PROMPT_CN",
    "SCORING_PROMPT",
    "TRANSLATION_PROMPT",
    "TRANSLATION_TO_EN_PROMPT",
    "HOOK_TYPES",
    "get_analysis_prompt",
    "get_scoring_prompt",
    "get_translation_prompt",
    "get_translation_to_en_prompt",
    "_load_hook_classification",
    "validate_product",
    "WELL_KNOWN_PRODUCTS",
    "NEEDS_HIGHER_BAR_PRODUCTS",
    "GENERIC_WHY_MATTERS",
    "HARDWARE_TYPES",
    "HARDWARE_CATEGORIES",
    "HARDWARE_SCORING_CRITERIA",
    "HARDWARE_ANALYSIS_PROMPT",
    "get_hardware_analysis_prompt",
    "WELL_KNOWN_HARDWARE",
    "HARDWARE_CRITERIA",
    "validate_hardware_product",
]
