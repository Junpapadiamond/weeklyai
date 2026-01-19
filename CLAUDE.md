# WeeklyAI - Claude 项目入口

> 全球 AI 产品灵感库 + 黑马发现平台

## 第一原则

> **"帮 PM 发现全球正在崛起的 AI 产品，从潜力股到黑马一网打尽"**

这意味着：
- ✅ **全球视野** - 不只美国，覆盖中国/欧洲/日韩/东南亚
- ✅ **内容为王** - 产品数量和新鲜度是核心
- ✅ **分层收录** - 黑马(4-5分)重点推荐，潜力股(2-3分)作为灵感
- ✅ **每个产品都要有"为什么重要"**
- ❌ **不要过度设计** - 先有内容，再优化体验

---

## 数据结构

```
crawler/data/
├── dark_horses/          # 黑马产品 (4-5分)
│   └── week_2026_03.json
├── rising_stars/         # 潜力股 (2-3分)
│   └── global_2026_03.json
├── candidates/           # 待审核
├── products_featured.json # 精选产品
├── products_history.json  # 历史数据
└── industry_leaders.json  # 🏆 行业领军（已知名产品参考）
```

---

## 关键代码

| 文件 | 职责 |
|------|------|
| `crawler/tools/auto_discover.py` | Web Search + GLM/Perplexity 自动发现 |
| `crawler/tools/add_product.py` | 手动添加产品 |
| `crawler/tools/dark_horse_detector.py` | 黑马评分计算 |
| `crawler/prompts/search_prompts.py` | 🔍 搜索 Prompt 模块 |
| `crawler/prompts/analysis_prompts.py` | 📊 分析 Prompt 模块 |
| `crawler/utils/perplexity_client.py` | Perplexity SDK 封装 |
| `backend/app/routes/products.py` | 产品 API |
| `frontend/views/index.ejs` | 首页模板 |

---

## 常用命令

```bash
# 自动发现 (推荐)
cd crawler
python3 tools/auto_discover.py --region us     # 美国
python3 tools/auto_discover.py --region cn     # 中国
python3 tools/auto_discover.py --region all    # 全球

# 硬件/软件分离搜索 (新增)
python3 tools/auto_discover.py --region all --type hardware  # 只搜硬件
python3 tools/auto_discover.py --region all --type software  # 只搜软件
python3 tools/auto_discover.py --region all --type mixed     # 混合 (40%硬件+60%软件)
python3 tools/auto_discover.py --list-keywords --region us   # 查看关键词

# 手动添加
python3 tools/add_product.py --quick "Name" "URL" "Desc"

# 启动服务
cd frontend && npm start      # localhost:3000
cd backend && python run.py   # localhost:5000

# 定时任务管理
launchctl list | grep weeklyai              # 查看任务状态
./ops/scheduling/daily_update.sh            # 手动运行
tail -f crawler/logs/daily_update.log       # 查看日志
```

### 定时任务 (launchd)

| 文件 | 说明 |
|------|------|
| `ops/scheduling/daily_update.sh` | 每日更新脚本 |
| `ops/scheduling/com.weeklyai.crawler.plist` | launchd 配置 |

**运行时间**: 每天凌晨 3:00
**执行内容**: `auto_discover.py --region all` → `main.py --news-only`
**日志位置**: `crawler/logs/daily_update.log`

安装命令:
```bash
launchctl unload ~/Library/LaunchAgents/com.weeklyai.crawler.plist 2>/dev/null
cp ops/scheduling/com.weeklyai.crawler.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.weeklyai.crawler.plist
```

---

## 产品分层体系

| 层级 | 评分 | 定义 | 展示位置 |
|------|------|------|----------|
| **🦄 黑马** | 4-5 分 | 高潜力 + 低曝光 | 首页重点推荐 |
| **⭐ 潜力股** | 2-3 分 | 有潜力/潜伏期 | 灵感库/发现页 |
| **📦 观察** | 1 分 | 待验证 | 候选池 |
| **🏆 行业领军** | N/A | 已人尽皆知 | 参考列表 |

---

## 🏆 行业领军（排除名单）

**文件**: `crawler/data/industry_leaders.json`

这些产品**不会**出现在黑马/潜力股列表中，因为它们已经广为人知。
但对于不熟悉 AI 领域的人，可以作为参考学习。

**分类概览**:

| 类别 | 代表产品 |
|------|----------|
| 通用大模型 | ChatGPT, Claude, Gemini, Copilot |
| 代码开发 | Cursor, GitHub Copilot, Replit, v0.dev, Bolt.new |
| 图像生成 | Midjourney, DALL-E, Stable Diffusion |
| 视频生成 | Sora, Runway, Pika, Synthesia |
| 语音合成 | ElevenLabs |
| 搜索引擎 | Perplexity |
| 中国大模型 | Kimi, 豆包, 通义千问, 文心一言, 智谱清言, 讯飞星火, MiniMax |
| 开发者工具 | LangChain, Hugging Face, Together AI, Groq |
| AI角色/伴侣 | Character.AI |
| 写作助手 | Jasper, Grammarly, Copy.ai, Notion AI |

> 💡 **注意**: 如果这些公司发布**全新的子产品**（不是主产品更新），仍可作为黑马收录

---

## 黑马判断标准 (4-5分)

### 什么是"黑马"？

**黑马 = 高潜力 + 低曝光 + PM 相关**

必须满足以下**至少 2 条**：

| 维度 | 黑马信号 | 示例 |
|------|----------|------|
| 🚀 **增长异常** | 融资速度快、ARR 增长快、用户暴涨 | Lovable: 8个月0到独角兽 |
| 👤 **创始人背景** | 大厂高管出走、知名投资人背书 | SSI: Ilya Sutskever (前 OpenAI) |
| 💰 **融资信号** | 种子轮 >$50M、估值增长 >3x | LMArena: 4个月估值 $1.7B |
| 🆕 **品类创新** | 开创新品类、解决新问题 | World Labs: 首个商用世界模型 |
| 🔥 **社区热度** | HN/Reddit/Twitter 突然爆火但产品还小 | - |

### 什么**不是**黑马？

- ❌ **已经人尽皆知**: ChatGPT, Midjourney, Cursor（除非有重大更新）
- ❌ **开发库/模型**: HuggingFace models, GitHub repos, LangChain
- ❌ **没有产品**: 只有论文、只有 demo、没有官网
- ❌ **大厂产品**: Google Gemini, Meta Llama（除非是独立子产品）
- ❌ **工具目录产品**: "xxx 相关的 AI 工具集合"

### 黑马评分详解

| 分数 | 标准 |
|------|------|
| **5分** | 必须收录: 融资 >$100M / 创始人顶级背景 / 品类开创者 |
| **4分** | 强烈推荐: 融资 >$30M / ARR >$10M / YC/顶级 VC 背书 |

---

## 潜力股标准 (2-3分)

### 什么是"潜力股"？

**潜力股 = 有创新 + 早期阶段 + 值得观察**

只要有以下**任意 1 条**即可收录：

| 维度 | 潜力股信号 | 示例 |
|------|------------|------|
| 💡 **创新点明确** | 解决真实问题、技术有特色 | 新型 AI 应用方式 |
| 🌱 **早期但有热度** | ProductHunt 上榜、社区讨论 | 小众但口碑好 |
| 🏠 **本地市场验证** | 在某个地区已有用户 | 中国/日本本土热门 |
| 🔧 **垂直领域深耕** | 专注细分赛道 | 医疗 AI、法律 AI |
| 🎨 **产品体验好** | 设计/交互有亮点 | 虽小但精致 |

### 潜力股评分详解

| 分数 | 标准 |
|------|------|
| **3分** | 值得关注: 融资 $1M-$5M / ProductHunt 上榜 / 本地热度高 |
| **2分** | 观察中: 刚发布/数据不足 但有明显创新点 |
| **1分** | 边缘: 勉强符合，待更多验证 |

---

## 地区权重

| 地区 | 权重 | 搜索引擎 |
|------|------|----------|
| 🇺🇸 美国 | 40% | Bing |
| 🇨🇳 中国 | 25% | Sogou |
| 🇪🇺 欧洲 | 15% | Bing |
| 🇯🇵🇰🇷 日韩 | 10% | Bing |
| 🇸🇬 东南亚 | 10% | Bing |

---

## 自动发现配置

### 每日配额

| 类别 | 目标数量 | 说明 |
|------|----------|------|
| 🦄 **黑马** | 5 个/天 | 4-5 分产品 |
| ⭐ **潜力股** | 10 个/天 | 2-3 分产品 |

### 地区配额（防止单一地区主导）

| 地区 | 最大数量 |
|------|----------|
| 🇺🇸 美国 | 6 |
| 🇨🇳 中国 | 4 |
| 🇪🇺 欧洲 | 3 |
| 🇯🇵 日本 | 2 |
| 🇰🇷 韩国 | 2 |
| 🇸🇬 东南亚 | 2 |

### 硬件/软件关键词系统

| 类型 | 关键词示例 | 配额占比 |
|------|------------|----------|
| 🔧 **硬件** | AI芯片、人形机器人、具身智能、边缘AI | **40%** |
| 💻 **软件** | AI融资、AI Agent、AIGC、大模型 | **60%** |

**硬件关键词** (`KEYWORDS_HARDWARE`):
- `AI chip startup funding 2026`
- `humanoid robot company funding`
- `AI semiconductor startup investment`
- `AI芯片 创业公司 融资`
- `人形机器人 创业公司`
- `具身智能 创业公司`

### 关键词轮换策略

根据星期几自动切换关键词池：

| 日期 | 关键词类型 | 说明 |
|------|------------|------|
| 周一/周四/周日 | 通用关键词 | `AI startup funding 2026`, `AI融资 2026` |
| 周二/周五 | 站点定向搜索 | `site:techcrunch.com`, `site:36kr.com` |
| 周三/周六 | 原生语言深度搜索 | 日语、韩语、德语关键词 |

### Provider 配置

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `ZHIPU_API_KEY` | 智谱 API Key | (required for cn) |
| `PERPLEXITY_API_KEY` | Perplexity API Key | (optional) |
| `PERPLEXITY_MODEL` | Perplexity 模型 | `sonar` |
| `USE_PERPLEXITY` | 启用 Perplexity | `false` |
| `API_RATE_LIMIT_DELAY` | API 调用间隔(秒) | `2` |

**Provider 路由:**
- `cn` → 始终使用 GLM（中文覆盖更稳）
- `us/eu/jp/kr/sea` → 根据 `USE_PERPLEXITY` 选择

**启用 Perplexity (推荐):**
```bash
# 1. 安装 SDK
pip install perplexityai

# 2. 设置环境变量
export PERPLEXITY_API_KEY=pplx_xxx
export USE_PERPLEXITY=true

# 3. 测试连接
python3 tools/auto_discover.py --test-perplexity

# 4. 运行发现
python3 tools/auto_discover.py --region us --dry-run
```

**Perplexity Search API 特性:**
- 实时 Web 搜索（排名结果 + 内容提取）
- 支持地区/语言/域名过滤
- 多查询批量搜索（最多 5 个）
- 官方 SDK 支持

**成本估算 (Perplexity):**
- Search API: $5 / 1K requests
- Sonar: $3 / 1M input, $15 / 1M output
- 预计月成本: $20-$35

**相关文件:**
- `crawler/utils/perplexity_client.py` - Perplexity SDK 封装
- `crawler/tools/auto_discover.py` - 自动发现（集成 Perplexity）

### 质量过滤规则

产品必须通过以下验证才会被保存：

1. **必填字段**：`name`, `website`, `description`, `why_matters`
2. **URL 验证**：必须是有效的 `http://` 或 `https://` URL
3. **描述长度**：`description` 必须 >20 字符
4. **why_matters 质量**：
   - ✅ 必须包含具体数字（融资金额/ARR/用户数）
   - ✅ 必须包含具体差异化（首创/背景/技术）
   - ❌ 禁止泛化描述："很有潜力"、"值得关注"、"融资情况良好"

### why_matters 示例

```
✅ GOOD:
- "Sequoia领投$50M，8个月ARR从0到$10M，首个AI原生代码编辑器"
- "前OpenAI联创，专注安全AGI，首轮融资即$1B估值"
- "日本本土AI独角兽，ARR $30M，主打日语企业市场"

❌ BAD:
- "这是一个很有潜力的AI产品"
- "融资情况良好，团队背景不错"
- "值得关注的新兴公司"
```

### 运行报告示例

```
═══════════════════════════════════════════════════════════════════════
Daily Discovery Report - 2026-01-19
═══════════════════════════════════════════════════════════════════════
Quotas:     Dark Horses: 4/5 ⚠️  Rising Stars: 10/10 ✅
Attempts:   3 rounds
Duration:   245.3 seconds
Regions:    us: 4, cn: 3, eu: 2, jp: 1
Providers:  glm: 3, perplexity: 7
Unique domains found: 15
Duplicates skipped: 3
Quality rejections: 2

Quality rejection reasons:
  - why_matters lacks specific details: 2
═══════════════════════════════════════════════════════════════════════
```

---

## API 端点

Base URL: `http://localhost:5000/api/v1`

| 端点 | 方法 | 说明 |
|------|------|------|
| `/products/trending` | GET | 热门 Top 5 |
| `/products/weekly-top` | GET | 本周 Top 15 |
| `/products/dark-horses` | GET | 黑马产品 (`limit`, `min_index`) |
| `/products/rising-stars` | GET | **潜力股产品 (2-3分)** (`limit`) |
| `/products/today` | GET | 今日精选 (`limit`, `hours`) |
| `/products/<id>` | GET | 产品详情 |
| `/products/categories` | GET | 分类列表 |
| `/products/blogs` | GET | 博客/新闻 (`limit`, `source`) |
| `/search?q=xxx` | GET | 搜索 (`categories`, `type`, `sort`, `page`) |

### 排序规则

所有产品列表按以下优先级排序：

| 优先级 | 条件 | 说明 |
|--------|------|------|
| 1️⃣ | **评分** | 5分 > 4分 > 3分 > 2分 |
| 2️⃣ | **融资金额** | 同分时，$500M > $100M |
| 3️⃣ | **估值/用户数** | 融资相同时，估值 > 用户数 |

---

## 数据模板

```json
{
  "name": "Etched AI",
  "slug": "etched-ai",
  "website": "https://etched.com",
  "logo": "https://...",
  "description": "AI chip startup building Sohu processor for transformers",
  "category": "hardware",
  "region": "🇺🇸",
  "founded_date": "2022",
  "funding_total": "$500M",
  "dark_horse_index": 5,
  "why_matters": "Peter Thiel 领投，估值 $5B，Sohu 芯片挑战 Nvidia 垄断",
  "latest_news": "2026-01: Stripes 领投新一轮融资",
  "discovered_at": "2026-01-16",
  "source": "TechCrunch"
}
```

**必填字段**: `name`, `website`, `description`, `why_matters`, `dark_horse_index`
**重要字段**: `funding_total`, `latest_news`, `category`
**有效分类**: coding, image, video, voice, writing, hardware, finance, education, healthcare, other

---

*更新: 2026-01-19 (硬件配额+前端布局+排序优化)*
