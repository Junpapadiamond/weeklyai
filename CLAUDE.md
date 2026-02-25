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

## 技术栈

| 层 | 技术 |
|------|------|
| **前端 (主力)** | Next.js 16, React 19, TypeScript, Tailwind CSS, SWR, Zod |
| **前端 (遗留)** | Express.js + EJS (frontend/) |
| **后端** | Flask 3.0, PyMongo 4.6, MongoDB 7, Gunicorn |
| **爬虫** | Python 3.9+, Scrapy, BeautifulSoup4, Perplexity API, Zhipu GLM |
| **AI 模型** | Perplexity Sonar (全球), Zhipu GLM-4.7 (中国), Claude (分析) |
| **存储** | MongoDB (主要), JSON 文件 (回退) |
| **部署** | Docker Compose (本地), Vercel (前端+后端) |
| **定时调度** | macOS launchd (本地), cron (服务器) |
| **测试** | Pytest, Playwright, Vitest |

---

## 项目结构

```
WeeklyAI/
├── .env / .env.example          # 环境变量
├── .mcp.json                    # Claude MCP 配置 (智谱 web search)
├── docker-compose.yml           # 全栈: mongo + frontend + backend + crawler
├── CLAUDE.md                    # 项目文档 (source of truth)
├── AGENTS.md                    # Agent 专用精简文档
│
├── frontend-next/               # 🟢 主力前端 (Next.js 16 + React 19)
│   ├── src/app/                 # 页面 (home, product, blog, discover, search)
│   ├── src/components/          # 组件 (home, product, discover, common, layout)
│   ├── src/lib/                 # 工具库 (api-client, product-utils, schemas)
│   └── src/types/               # TypeScript 类型定义
│
├── frontend/                    # ⚪ 遗留前端 (Express + EJS)
│
├── backend/                     # Flask API
│   ├── app/routes/              # products.py, search.py
│   ├── app/services/            # product_repository, product_service, product_filters, product_sorting
│   └── vercel.json              # Vercel Serverless 部署
│
├── crawler/                     # AI 发现引擎
│   ├── main.py                  # 主协调器 (新闻聚合)
│   ├── tools/                   # 33 个 Python 工具脚本
│   ├── utils/                   # 12 个工具模块
│   ├── prompts/                 # 搜索 + 分析 Prompt
│   ├── spiders/                 # 17 个爬虫 (含 YouTube/X)
│   ├── database/                # MongoDB/JSON 抽象层
│   └── data/                    # 数据文件
│
├── ops/scheduling/              # 定时任务 (daily_update.sh, launchd)
├── tests/                       # 测试套件 (12 个 Python 测试文件)
└── history/                     # 历史版本
```

---

## 数据结构

```
crawler/data/
├── dark_horses/                 # 黑马产品 (4-5分)
│   └── week_2026_09.json
├── rising_stars/                # 潜力股 (2-3分)
│   └── global_2026_09.json
├── candidates/                  # 待审核
│   └── rss_to_products_cache.json
├── products_featured.json       # 精选产品 (前端数据源, 2-5分全量)
├── products_hot_search.json     # 热搜词数据源
├── products_history.json        # 历史数据
├── industry_leaders.json        # 🏆 行业领军（排除名单）
├── blogs_news.json              # 新闻/博客 (YouTube/X/RSS)
├── logo_cache.json              # Logo URL 缓存
├── source_watchlists.json       # 社交账号监控列表 (YouTube/X)
├── product_official_handles.json # 产品社交媒体账号
└── last_updated.json            # 更新时间戳
```

---

## 关键代码

| 文件 | 职责 |
|------|------|
| `crawler/tools/auto_discover.py` | 自动发现 (Provider 路由: cn→GLM, 其他→Perplexity) |
| `crawler/tools/auto_publish.py` | 自动发布候选 → featured |
| `crawler/tools/rss_to_products.py` | 社交信号→产品 + enrich featured |
| `crawler/tools/sync_to_mongodb.py` | JSON → MongoDB 同步 |
| `crawler/tools/dark_horse_detector.py` | 黑马评分计算 |
| `crawler/tools/fix_logos.py` | Logo 自动修复 (favicon/HTML icon 解析) |
| `crawler/tools/resolve_websites.py` | 自动解析缺失官网 URL |
| `crawler/tools/validate_websites.py` | 验证自动解析的域名 |
| `crawler/tools/cleanup_unknowns_and_duplicates.py` | 去重 + 清理未知域名 |
| `crawler/tools/backfill_source_urls.py` | 回填 source_url |
| `crawler/tools/add_product.py` | 手动添加产品 |
| `crawler/tools/data_classifier.py` | 自动分类 (YouTube/X → blog) |
| `crawler/prompts/search_prompts.py` | 🔍 搜索 Prompt 模块 |
| `crawler/prompts/analysis_prompts.py` | 📊 分析 Prompt 模块 (含硬件评判体系) |
| `crawler/utils/perplexity_client.py` | Perplexity SDK 封装 (美国/欧洲/日韩) |
| `crawler/utils/glm_client.py` | 智谱 GLM SDK 封装 (中国区) |
| `crawler/utils/social_sources.py` | 社交来源配置 (YouTube/X 账号列表) |
| `crawler/utils/dedup.py` | 去重 (按 normalized domain) |
| `crawler/spiders/youtube_spider.py` | YouTube RSS 信号爬虫 |
| `crawler/spiders/x_spider.py` | X/Twitter 信号爬虫 (Perplexity + fallback) |
| `backend/app/routes/products.py` | 产品 API |
| `backend/app/services/product_repository.py` | 数据层 (MongoDB 优先, JSON 回退) |
| `backend/app/services/product_service.py` | 业务逻辑 (排序/过滤/enrichment) |
| `frontend-next/src/app/page.tsx` | 首页 (Next.js) |
| `frontend-next/src/components/home/home-client.tsx` | 首页客户端组件 |
| `frontend-next/src/components/home/discovery-deck.tsx` | Swipe Card 组件 |

---

## 🔧 硬件站点搜索源 (3个优质来源)

| 站点 | 说明 | 搜索模式 |
|------|------|----------|
| **Product Hunt** | 全球硬件首发地，发现最早期创新产品 | `site:producthunt.com AI hardware` |
| **Kickstarter** | 众筹平台，最前沿硬件创意 | `site:kickstarter.com AI robot` |
| **36氪** | 中国最权威 AI/硬件媒体 | `site:36kr.com AI硬件` |

使用硬件搜索：
```bash
python3 tools/auto_discover.py --region all --type hardware
```

---

## 常用命令

```bash
# 自动发现 (推荐)
cd crawler
python3 tools/auto_discover.py --region us     # 美国
python3 tools/auto_discover.py --region cn     # 中国
python3 tools/auto_discover.py --region all    # 全球

# 硬件/软件分离搜索
python3 tools/auto_discover.py --region all --type hardware  # 只搜硬件
python3 tools/auto_discover.py --region all --type software  # 只搜软件
python3 tools/auto_discover.py --region all --type mixed     # 混合 (40%硬件+60%软件)
python3 tools/auto_discover.py --list-keywords --region us   # 查看关键词

# 手动添加
python3 tools/add_product.py --quick "Name" "URL" "Desc"

# 启动服务
cd frontend-next && npm run dev   # localhost:3001 (主力前端)
cd frontend && npm start          # localhost:3000 (遗留前端)
cd backend && python run.py       # localhost:5000

# 社交信号
python3 tools/rss_to_products.py --sources youtube,x --enrich-featured --dry-run

# MongoDB 同步
python3 tools/sync_to_mongodb.py --all --dry-run

# 定时任务管理
launchctl list | grep weeklyai              # 查看任务状态
./ops/scheduling/daily_update.sh            # 手动运行
tail -f crawler/logs/daily_update.log       # 查看日志

# 测试
cd frontend-next && npm test                # Vitest 前端测试
PYTHONPATH=backend:crawler python -m pytest tests/ -v   # Python 测试
```

### 定时任务 (launchd)

| 文件 | 说明 |
|------|------|
| `ops/scheduling/daily_update.sh` | 每日更新脚本 (10 步流水线) |
| `ops/scheduling/com.weeklyai.crawler.plist` | launchd 配置 |
| `ops/scheduling/com.weeklyai.news.plist` | 新闻更新任务 |

**运行时间**: 每天凌晨 3:00
**日志位置**: `crawler/logs/daily_update.log`

**每日流水线 (10 步)**:
```
1. auto_discover.py --region all        → 全球 AI 产品发现
2. auto_publish.py                      → 候选产品发布到 featured
3. backfill_source_urls.py              → 回填 source_url
4. resolve_websites.py --aggressive     → 自动解析缺失官网
5. validate_websites.py                 → 验证自动解析的域名
6. cleanup_unknowns_and_duplicates.py   → 去重 + 清理未知域名
7. fix_logos.py                         → Logo 自动修复
8. main.py --news-only                  → 新闻/博客更新
9. rss_to_products.py --enrich-featured → 社交信号 enrich
10. sync_to_mongodb.py --all            → 同步到 MongoDB (如有配置)
```

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

## 数据入库与首页展示规则

### 自动入库

- auto_discover 产出 **2-5 分** 产品，完成评判体系评分 + 去重（按 website）后，全部写入后端数据源（当前为 `products_featured.json`）。
- **2-5 分全量库**即前端"更多推荐"的完整数据源。

### 首页三段展示

- **本周黑马**（首页第一区块）：
  - 上限 10 个，优先 **4-5 分**（软件 + 硬件）。
  - **刷新规则** (保持新鲜度):
    - 大部分产品：严格 **5 天后移出** → 更多推荐
    - TOP 1 产品 (最高评分+融资)：可保留 **10 天**
    - 如果 `news_updated_at` 更新，重置计时器
    - 空状态回退：按评分显示 top 10
  - 配置: `DARK_HORSE_FRESH_DAYS=5`, `DARK_HORSE_STICKY_DAYS=10`
- **硬件补位**：
  - 若当周硬件 **无 4-5 分**，可补入 **2-3 分硬件**。
  - 补位数量 **≤ 当周 4-5 分软件数量**。
  - 补位硬件不受时间限制；如有 4-5 分硬件则直接放入本周黑马。
- **Swipe card**（首页第二区块）：
  - 使用 **2-5 分全量库**，用户可以一直刷到全部刷完。
  - 卡片尽量展示更多信息（如 `why_matters` / `funding_total` / `latest_news`）。
- **更多推荐**（首页第三区块）：
  - 展示全部 2-5 分产品（包含从本周黑马移出的旧产品）。

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

## 软件黑马标准 (4-5分)

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

### 软件评分详解

| 分数 | 标准 |
|------|------|
| **5分** | 必须收录: 融资 >$100M / 创始人顶级背景 / 品类开创者 |
| **4分** | 强烈推荐: 融资 >$30M / ARR >$10M / YC/顶级 VC 背书 |

---

## 潜力股标准 (2-3分)

**潜力股 = 有创新 + 早期阶段 + 值得观察**

只要有以下**任意 1 条**即可收录：

| 维度 | 潜力股信号 | 示例 |
|------|------------|------|
| 💡 **创新点明确** | 解决真实问题、技术有特色 | 新型 AI 应用方式 |
| 🌱 **早期但有热度** | ProductHunt 上榜、社区讨论 | 小众但口碑好 |
| 🏠 **本地市场验证** | 在某个地区已有用户 | 中国/日本本土热门 |
| 🔧 **垂直领域深耕** | 专注细分赛道 | 医疗 AI、法律 AI |
| 🎨 **产品体验好** | 设计/交互有亮点 | 虽小但精致 |

| 分数 | 标准 |
|------|------|
| **3分** | 值得关注: 融资 $1M-$5M / ProductHunt 上榜 / 本地热度高 |
| **2分** | 观察中: 刚发布/数据不足 但有明显创新点 |
| **1分** | 边缘: 勉强符合，待更多验证 |

---

## 🔧 硬件产品评判体系 (宽松版)

> **核心理念：硬件产品重在「创新性」和「灵感启发」，而非严格的融资门槛**

硬件创业门槛高、周期长，很多创新产品来自小团队。我们收录硬件产品的目的是：
- ✅ 发现有趣的 AI 硬件形态
- ✅ 获得产品灵感和趋势洞察
- ✅ 关注技术创新而非商业规模
- ❌ 不强求融资金额或量产数据

### 硬件分类

#### 硬件类型 (hardware_type)

| 类型 | 说明 | 优先级 |
|------|------|--------|
| `innovative` | **创新形态硬件** - 非传统计算设备的新 AI 载体 | ⭐ 重点发掘 |
| `traditional` | 传统硬件 - 芯片/机器人/无人机等 | 正常评估 |

#### 形态不限制 (form_factor)

创新形态硬件**不限制具体形态**，用 `form_factor` 字段自由描述：

| 形态类别 | 示例 |
|----------|------|
| 可穿戴 | pendant, pin, ring, glasses, earclip, bracelet, hairpin... |
| 随身携带 | card, keychain, phone_case... |
| 桌面/家居 | smart_frame, lamp, mirror, plush_toy, alarm... |
| 特定场景 | pet_collar, kids_watch, sports_gear... |

#### 创新特征标签 (innovation_traits)

| 标签 | 说明 |
|------|------|
| **形态创新类** | `non_traditional_form`, `new_form_factor`, `wearable`, `portable`, `ambient` |
| **场景类** | `single_use_case`, `companion`, `productivity`, `memory`, `health`, `lifestyle` |
| **交互类** | `voice_first`, `screenless`, `proactive_ai`, `always_on`, `gesture`, `haptic` |
| **商业类** | `affordable`, `no_subscription`, `crowdfunding` |
| **热度类** | `social_buzz`, `media_coverage`, `viral` |

#### 使用场景 (use_case)

| 场景 | 说明 | 示例产品 |
|------|------|----------|
| `emotional_companion` | 情感陪伴 | Friend Pendant |
| `meeting_notes` | 会议录音/笔记 | Limitless, Plaud |
| `memory_assistant` | 记忆辅助 | Legend Memory |
| `life_logging` | 生活记录 | Looki |
| `health_monitoring` | 健康监测 | - |
| `productivity` | 生产力工具 | - |
| `accessibility` | 无障碍辅助 | - |

### 创新硬件评分标准

> **核心理念**：形态创新 (40%) > 使用场景 (30%) > 热度信号 (15%) > 商业可行 (15%)

#### 评分维度权重

| 优先级 | 维度 | 权重 | 关键问题 |
|--------|------|------|----------|
| 1️⃣ | **形态创新** | 40% | 是否是新的 AI 载体？非手机/平板/传统手表？ |
| 2️⃣ | **使用场景** | 30% | 是否专注单一场景？场景是否有真实价值？ |
| 3️⃣ | **热度信号** | 15% | 社交媒体/众筹/媒体报道？ |
| 4️⃣ | **商业可行** | 15% | 价格亲民/已发货/有融资？ |

#### 5分 - 现象级创新硬件

满足组合：**形态创新 + 场景清晰 + 热度信号**
- 或被大厂收购/战略合作
- 或融资 >$100M (传统硬件)

示例：Friend Pendant, Limitless (被Meta收购)

#### 4分 - 硬件黑马 ⭐ 重点发掘

满足以下**任意组合**：
- ✅ 形态创新 + 场景清晰
- ✅ 形态创新 + 已发货/预售
- ✅ 形态创新 + 众筹成功 (>300%)
- ✅ 场景清晰 + 社交热度/媒体报道

示例：Plaud NotePin, Vocci, iBuddi

#### 3分 - 硬件潜力

满足以下**任意 1 条**：
- 💡 有形态创新 (任何新载体形式)
- 🎯 有明确使用场景
- 🔧 有工作原型/demo
- 🌐 众筹进行中
- 🎨 设计/交互有亮点

#### 2分 - 硬件观察

- 概念阶段但想法有趣
- ProductHunt 新发布
- 社交媒体有讨论
- 早期但方向清晰

### 硬件 why_matters 要求（宽松版）

```
✅ GOOD (说清楚创新点即可):
- "首款开源 AI 眼镜，支持多种 LLM 集成，开发者友好"
- "掌上 AI 助手，用 LAM 模型直接操作 App，交互方式新颖"
- "AI 录音吊坠，自动生成会议摘要，$99 极致性价比"
- "人形机器人，步态控制创新，成本是竞品 1/3"

❌ BAD (太泛化):
- "创新的 AI 硬件"
- "下一代智能设备"
```

### 已知名硬件排除名单

不收录以下已广为人知的硬件（但其**新产品线**可以收录）：
- **芯片**: Nvidia GPU, Intel, AMD, Qualcomm
- **AR/VR**: Apple Vision Pro, Meta Quest
- **机器人**: Boston Dynamics Spot/Atlas
- **消费电子**: iPhone, Echo, HomePod
- **汽车**: Tesla FSD, Waymo
- **无人机**: DJI

---

## 地区权重

| 地区 | 权重 | 搜索引擎 |
|------|------|----------|
| 🇺🇸 美国 | 40% | Bing |
| 🇨🇳 中国 | 25% | Sogou/Quark |
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

**区域路由架构:**
```
auto_discover.py
       │
       ▼
┌──────────────────┐
│ get_provider()   │
│  cn → GLM        │
│  us/eu/jp → Pplx │
└──────────────────┘
       │
   ┌───┴───┐
   ▼       ▼
┌─────┐  ┌─────────┐
│ GLM │  │Perplexity│
└─────┘  └─────────┘
```

#### Perplexity (美国/欧洲/日韩/东南亚)

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `PERPLEXITY_API_KEY` | Perplexity API Key | (required) |
| `PERPLEXITY_MODEL` | Perplexity 模型 | `sonar` |

**启用 Perplexity:**
```bash
# 1. 安装 SDK
pip install perplexityai

# 2. 设置环境变量
export PERPLEXITY_API_KEY=pplx_xxx

# 3. 测试连接
python3 tools/auto_discover.py --test-perplexity

# 4. 运行发现
python3 tools/auto_discover.py --region us --dry-run
```

**Perplexity 特性:**
- 实时 Web 搜索（排名结果 + 内容提取）
- 支持地区/语言/域名过滤
- 官方 SDK 支持

**成本估算:** $20-$35/月

#### GLM 智谱 (中国区)

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `ZHIPU_API_KEY` | 智谱 API Key | (required for cn) |
| `GLM_MODEL` | GLM 模型 | `glm-4.7` |
| `GLM_SEARCH_ENGINE` | 搜索引擎 | `search_pro` (可选: `search_pro_sogou`, `search_pro_quark`, `search_std`) |
| `USE_GLM_FOR_CN` | 中国区启用 GLM | `true` |
| `GLM_THINKING_TYPE` | 深度思考模式 | `disabled` |
| `GLM_CLEAR_THINKING` | 清除思考内容 | `true` |

**搜索引擎选项:**

| 引擎 | 价格 | 说明 |
|------|------|------|
| `search_pro` | ¥0.03/次 | 智谱自研高阶版 (推荐) |
| `search_pro_sogou` | ¥0.05/次 | 腾讯生态+知乎 |
| `search_pro_quark` | ¥0.05/次 | 夸克搜索增强，中文召回更强 |
| `search_std` | ¥0.01/次 | 基础搜索 |

**启用 GLM (中国区):**
```bash
# 1. 安装 SDK
pip install zhipuai

# 2. 设置环境变量 (在 crawler/.env)
ZHIPU_API_KEY=your-api-key
GLM_MODEL=glm-4.7
GLM_SEARCH_ENGINE=search_pro
USE_GLM_FOR_CN=true

# 3. 测试连接
python3 tools/auto_discover.py --test-glm

# 4. 测试路由
python3 tools/auto_discover.py --test-routing

# 5. 运行中国区发现
python3 tools/auto_discover.py --region cn --dry-run
```

**GLM-4.7 特性:**
- 智谱自研联网搜索（优化中文内容）
- 最大上下文 200K，最大输出 128K
- 支持深度思考 (thinking)
- 支持多搜索引擎切换
- 官方 SDK 支持

**成本估算:** ¥30-50/月

**⚠️ 限流处理:**
- GLM API 有并发限制，429 错误表示 "并发数过高"
- 自动重试机制：遇到 429 会等待后重试（退避策略）
- 单实例锁 + 关键词数限制 + cooldown 节流
- 如果频繁限流，可联系智谱客服增加限额
- 或者设置 `USE_GLM_FOR_CN=false` 临时回退到 Perplexity

**中国权威 AI 媒体源:**

| 媒体 | 域名 | 优先级 |
|------|------|--------|
| 36氪 | 36kr.com | Tier 1 |
| 机器之心 | jiqizhixin.com | Tier 1 |
| IT桔子 | itjuzi.com | Tier 1 |
| 钛媒体 | tmtpost.com | Tier 1 |
| 量子位 | qbitai.com | Tier 2 |
| 雷锋网 | leiphone.com | Tier 2 |

#### 回滚方案

如果 GLM 集成出现问题：
1. 设置 `USE_GLM_FOR_CN=false`
2. 中国区自动回退到 Perplexity
3. 无需代码修改

**相关文件:**
- `crawler/utils/perplexity_client.py` - Perplexity SDK 封装
- `crawler/utils/glm_client.py` - GLM SDK 封装
- `crawler/tools/auto_discover.py` - 自动发现（Provider 路由）

### 质量过滤规则

产品必须通过以下验证才会被保存：

1. **必填字段**：`name`, `website`, `description`, `why_matters`
2. **URL 验证**：必须是有效的 `http://` 或 `https://` URL，禁止 placeholder 域名
3. **描述长度**：`description` 必须 >20 字符
4. **why_matters 质量**：
   - ✅ 必须包含具体数字（融资金额/ARR/用户数）
   - ✅ 必须包含具体差异化（首创/背景/技术）
   - ❌ 禁止泛化描述："很有潜力"、"值得关注"、"融资情况良好"
   - ❌ 长度 < 30 字符则拒绝
5. **域名过滤**：unknown 域名不阻止入库但标记 `needs_verification: true`
6. **行业领军排除**：`industry_leaders.json` 中的产品不收录

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
Providers:  perplexity: 10
Unique domains found: 15
Duplicates skipped: 3
Quality rejections: 2

Quality rejection reasons:
  - why_matters lacks specific details: 2
═══════════════════════════════════════════════════════════════════════
```

---

## 社交信号引擎 (YouTube + X)

### 架构

```
YouTube RSS / X (Perplexity Search)
       │
       ▼
 youtube_spider.py / x_spider.py
       │
       ▼
 blogs_news.json (source: youtube/x)
       │
       ▼
 rss_to_products.py --enrich-featured
       │
  ┌────┴────┐
  ▼         ▼
新产品 →    已存在产品 →
candidates  刷新 latest_news / news_updated_at
```

### 关键特性

- **来源配置优先级**：`env > crawler/data/source_watchlists.json > 内置默认`（由 `social_sources.py` 读取）
- **X 回退链路**：Perplexity 产出为 0 时启用 account fallback（`r.jina.ai` timeline + `cdn.syndication.twimg.com`）
- **enrich 逻辑**：先 enrich 已存在产品，再判重；确保已有产品也能刷新 `latest_news` / `news_updated_at` 并写入 `extra.signals`
- **年份硬闸门**：`CONTENT_YEAR` (默认当前年) 统一过滤非指定年份内容
- **YouTube 精度**：信号词需命中标题/描述前窗口；`github.com` 仅在有 "open source/开源" 文案时才算信号
- **X URL 支持**：多种形态 (`/status/`, `/i/web/status/`, `mobile.twitter.com`)
- **分类规则**：`data_classifier.py` 对 `youtube/x` 来源强制归类为 `blog`

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CONTENT_YEAR` | 仅保留该年份内容 | `2026` |
| `SOCIAL_HOURS` | 信号回溯窗口 (小时) | `96` |
| `YOUTUBE_CHANNEL_IDS` | 监控的 YouTube 频道 | (env 或 watchlists) |
| `X_ACCOUNTS` | 监控的 X 账号 | (env 或 watchlists) |
| `X_SOURCE_MODE` | X 来源模式 | `hybrid` |
| `SOCIAL_X_MAX_RESULTS` | X 搜索最大结果数 | `20` |

### 验证

```bash
# 验证社交信号质量 (不写入 repo)
python3 crawler/tools/verify_social_signals.py --hours 96 --limit 30

# Dry-run enrich
python3 crawler/tools/rss_to_products.py --sources youtube,x --enrich-featured --dry-run
```

---

## 前端 (frontend-next)

### 技术栈
Next.js 16 + React 19 + TypeScript + Tailwind CSS + SWR + Zod

### 页面

| 路径 | 文件 | 说明 |
|------|------|------|
| `/` | `src/app/page.tsx` | 首页 (黑马 + Swipe Card + 更多推荐) |
| `/product/[id]` | `src/app/product/[id]/page.tsx` | 产品详情 |
| `/discover` | `src/app/discover/page.tsx` | Swipe 发现模式 |
| `/blog` | `src/app/blog/page.tsx` | 新闻/博客 |
| `/search` | `src/app/search/page.tsx` | 搜索结果 |

### 核心组件

| 组件 | 文件 | 说明 |
|------|------|------|
| HomeClient | `components/home/home-client.tsx` | 首页客户端编排 |
| DiscoveryDeck | `components/home/discovery-deck.tsx` | Swipe Card 交互 |
| HeroCanvas | `components/home/hero-canvas.tsx` | Hero 背景动画 (p5.js) |
| ProductCard | `components/product/product-card.tsx` | 产品卡片 |
| SmartLogo | `components/common/smart-logo.tsx` | 智能 Logo 加载 (CDN + fallback) |
| FavoriteButton | `components/favorites/favorite-button.tsx` | 收藏按钮 |
| ThemeToggle | `components/layout/theme-toggle.tsx` | 深色/浅色切换 |

### 启动

```bash
cd frontend-next
npm install
npm run dev    # localhost:3001
```

---

## API 端点

Base URL: `http://localhost:5000/api/v1`

| 端点 | 方法 | 说明 |
|------|------|------|
| `/products/trending` | GET | 热门 Top 5 |
| `/products/weekly-top` | GET | 本周 Top 15 (`limit`, `sort_by`) |
| `/products/dark-horses` | GET | 黑马产品 (`limit`, `min_index`) |
| `/products/rising-stars` | GET | **潜力股产品 (2-3分)** (`limit`) |
| `/products/today` | GET | 今日精选 (`limit`, `hours`) |
| `/products/<id>` | GET | 产品详情 |
| `/products/<id>/related` | GET | 相关产品推荐 (`limit`) |
| `/products/categories` | GET | 分类列表 |
| `/products/blogs` | GET | 博客/新闻 (`limit`, `source`, `market`) |
| `/products/last-updated` | GET | 最近更新时间 |
| `/products/analytics/summary` | GET | 数据分析摘要 |
| `/products/feed/rss` | GET | RSS 订阅源 |
| `/products/industry-leaders` | GET | 行业领军参考列表 |
| `/search?q=xxx` | GET | 搜索 (`categories`, `type`, `sort`, `page`, `limit`) |

### 排序规则

所有产品列表按以下优先级排序：

| 优先级 | 条件 | 说明 |
|--------|------|------|
| 1️⃣ | **评分** | 5分 > 4分 > 3分 > 2分 |
| 2️⃣ | **融资金额** | 同分时，$500M > $100M |
| 3️⃣ | **估值/用户数** | 融资相同时，估值 > 用户数 |

---

## 数据模板

### 创新硬件数据模板

```json
{
  "name": "Friend Pendant",
  "slug": "friend-pendant",
  "website": "https://friend.com",
  "description": "AI 伴侣项链，Claude 驱动的 always-on 情感陪伴设备",
  "category": "hardware",
  "hardware_type": "innovative",
  "form_factor": "pendant",
  "use_case": "emotional_companion",
  "innovation_traits": ["non_traditional_form", "voice_first", "affordable", "no_subscription", "social_buzz"],
  "region": "🇺🇸",
  "price": "$99",
  "funding_total": "$10M",
  "dark_horse_index": 5,
  "criteria_met": ["form_innovation", "use_case_clear", "viral"],
  "why_matters": "AI 伴侣吊坠，Claude 驱动，$99 无订阅，Twitter 现象级爆火",
  "latest_news": "2026-01: 出货量达 10 万台",
  "discovered_at": "2026-01-20",
  "source": "Wired",
  "is_hardware": true
}
```

### 传统硬件数据模板

```json
{
  "name": "Etched AI",
  "slug": "etched-ai",
  "website": "https://etched.ai",
  "description": "AI chip startup building Sohu processor for transformers",
  "category": "hardware",
  "hardware_type": "traditional",
  "hardware_category": "ai_chip",
  "region": "🇺🇸",
  "funding_total": "$500M",
  "dark_horse_index": 5,
  "criteria_met": ["hardware_funding", "mass_production"],
  "why_matters": "获$500M融资，估值$5B，Stripes领投，AI芯片挑战Nvidia垄断",
  "latest_news": "2026-01: Stripes 领投新一轮融资",
  "discovered_at": "2026-01-16",
  "source": "TechCrunch",
  "is_hardware": true
}
```

**必填字段**: `name`, `website`, `description`, `why_matters`, `dark_horse_index`
**创新硬件字段**: `hardware_type`, `form_factor`, `use_case`, `innovation_traits`, `price`
**有效分类**: coding, image, video, voice, writing, hardware, finance, education, healthcare, agent, other

---

## MongoDB Migration (JSON → Mongo)

### Architecture

```
JSON files (source of truth)
    ↓  sync_to_mongodb.py --all
MongoDB (runtime store for Vercel)
    ↓  MONGO_URI env var
Backend (prefers MongoDB, falls back to JSON)
```

### How It Works

- **Sync tool** (`crawler/tools/sync_to_mongodb.py`):
  - Loads `products_featured.json` + all `dark_horses/*.json` (skips `template.json`)
  - Merges and deduplicates by normalized domain key (same logic as backend)
  - Upserts into MongoDB `products` collection via `_sync_key`
  - Also syncs `blogs`, `candidates` with `--blogs`, `--candidates`, or `--all`
  - Creates indexes with `--ensure-indexes` (also runs automatically after sync)

- **Backend** (`product_repository.py`):
  - `_mongo_uri_configured()`: returns True only when `MONGO_URI` env var is set and non-empty
  - `load_products()`: tries MongoDB first when configured, falls back to JSON file loading
  - `load_blogs()`: same pattern — MongoDB first, JSON fallback
  - MongoClient is cached at module scope for serverless connection reuse

- **Docker Compose**: includes `mongo:7` service; backend and crawler get `MONGO_URI` automatically

### Environment Variables

| Variable | Where | Example |
|---|---|---|
| `MONGO_URI` | Vercel backend | `mongodb+srv://user:pass@cluster/weeklyai?retryWrites=true&w=majority` |
| `MONGO_URI` | Local dev | `mongodb://localhost:27017/weeklyai` (set by docker-compose) |

When `MONGO_URI` is **not set**, the backend uses JSON files only (zero MongoDB dependency).

### One-Time Migration Runbook

```bash
# 1. Set MONGO_URI to your target MongoDB
export MONGO_URI="mongodb+srv://..."

# 2. Dry run to verify
cd crawler
python tools/sync_to_mongodb.py --all --dry-run

# 3. Real sync (clears non-curated items first)
python tools/sync_to_mongodb.py --all --clear-old

# 4. Verify counts
python -c "
from pymongo import MongoClient
import os
db = MongoClient(os.environ['MONGO_URI']).get_database()
print(f'products: {db.products.count_documents({})}')
print(f'blogs: {db.blogs.count_documents({})}')
"
```

### Ongoing Sync

After daily crawler runs, sync to MongoDB (step 10 in daily pipeline):

```bash
python tools/sync_to_mongodb.py --all
```

### Collections & Indexes

**products**: `_sync_key` (unique), `website`, `dark_horse_index` desc, `final_score` desc, `discovered_at` desc, `categories`, text index on `name`/`description`/`why_matters`

**blogs**: `_sync_key` (unique), `published_at` desc, `created_at` desc

---

## 数据质量保障

### 流水线质量修复

| 问题 | 文件 | 修复 |
|---|---|---|
| JSON 解析失败返回原始文本 | `perplexity_client.py`, `glm_client.py` | 返回 `[]` + 日志警告 |
| `why_matters` 验证 AND→OR bug | `auto_discover.py` | 含泛化短语 **或** 长度 < 30 则拒绝 |
| 缺失 categories | `auto_discover.py` | `validate_product()` 默认 `["other"]` |
| 无效 region | `auto_discover.py` | `validate_product()` 默认 🌐 |
| upsert key 冲突 | `db_handler.py` | 统一为 `_sync_key` (normalized domain) |
| Unknown 域名处理 | `cleanup_unknowns_and_duplicates.py` | 硬过滤未知域名 + 不可信平台 |
| source_url 域名校验 | `auto_discover.py` (cn) | 校验 source_url 不含不可信平台域名 |
| Logo 域名锁定 | `fix_logos.py` | Logo 仅从产品官方域名获取 |

### 修复工具

```bash
# 一次性数据修复
python crawler/tools/repair_data.py --dry-run   # 预览
python crawler/tools/repair_data.py              # 执行 (自动创建 .bak 备份)
```

修复内容：空 `criteria_met` 回填、缺失 categories、无效 region、知名产品清除、融资金额标准化 (`funding_total_usd`)。

---

## 测试

| 测试文件 | 覆盖范围 |
|----------|----------|
| `tests/test_blog_market_distribution.py` | 博客市场分布与聚合逻辑 |
| `tests/test_blog_market_filters.py` | 博客市场过滤参数 |
| `tests/test_cn_news_only_merge.py` | 中国区新闻合并去重 |
| `tests/test_darkhorse_freshness.py` | 黑马新鲜度/轮换逻辑 |
| `tests/test_data_verifier.py` | 产品 schema 验证 |
| `tests/test_demand_signals.py` | 需求信号检测 (融资/增长/热度) |
| `tests/test_frontend.py` | E2E 前端测试 (Playwright) |
| `tests/test_glm_tool_parsing.py` | GLM JSON 解析鲁棒性 |
| `tests/test_mongo_migration.py` | MongoDB 同步/去重/回退 (30 tests) |
| `tests/test_search_accuracy.py` | 搜索相关性与排序准确性 |
| `tests/test_social_signals.py` | X/YouTube URL 解析 + enrich 逻辑 |
| `tests/test_weekly_top_sorting.py` | Weekly Top 排序策略 |
| `frontend-next/src/lib/__tests__/schemas.test.ts` | 前端 schema 验证 |
| `frontend-next/src/lib/__tests__/product-utils.test.ts` | 前端工具函数测试 |

```bash
# Python 测试
PYTHONPATH=backend:crawler python -m pytest tests/ -v

# 前端测试
cd frontend-next && npm test
```

---

## 全部环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MONGO_URI` | MongoDB 连接 URI | (未设置则用 JSON) |
| `API_BASE_URL_SERVER` | Next.js 服务端 API 基地址 | `http://localhost:5000/api/v1` |
| `NEXT_PUBLIC_API_BASE_URL` | 前端浏览器侧 API 基地址 | `http://localhost:5000/api/v1` |
| `PERPLEXITY_API_KEY` | Perplexity API Key | (required) |
| `PERPLEXITY_MODEL` | Perplexity 模型 | `sonar` |
| `ZHIPU_API_KEY` | 智谱 API Key | (required for cn) |
| `GLM_MODEL` | GLM 模型 | `glm-4.7` |
| `GLM_SEARCH_ENGINE` | GLM 搜索引擎 | `search_pro` |
| `USE_GLM_FOR_CN` | 中国区启用 GLM | `true` |
| `GLM_THINKING_TYPE` | GLM 深度思考 | `disabled` |
| `CONTENT_YEAR` | 内容年份过滤 | `2026` |
| `SOCIAL_HOURS` | 社交信号回溯窗口 | `96` |
| `YOUTUBE_CHANNEL_IDS` | YouTube 频道列表 | (watchlists) |
| `X_ACCOUNTS` | X 账号列表 | (watchlists) |
| `X_SOURCE_MODE` | X 来源模式 | `hybrid` |
| `SOCIAL_X_MAX_RESULTS` | X 最大结果数 | `20` |
| `FLASK_ENV` | Flask 环境 | `development` |
| `CORS_ALLOWED_ORIGINS` | 后端 CORS 白名单 (逗号分隔) | 空 |
| `PORT` | 后端端口 | `5000` |
| `PORT_FALLBACK` | 备用后端端口 | `5001` |
| `NODE_ENV` | Node 环境 | `production` |
| `DARK_HORSE_FRESH_DAYS` | 黑马新鲜期 (天) | `5` |
| `DARK_HORSE_STICKY_DAYS` | TOP1 保留期 (天) | `10` |

---

*更新: 2026-02-25*
