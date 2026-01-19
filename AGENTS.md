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
└── products_history.json  # 历史数据
```

---

## 关键代码

| 文件 | 职责 |
|------|------|
| `crawler/tools/auto_discover.py` | Web Search + GLM 自动发现 |
| `crawler/tools/add_product.py` | 手动添加产品 |
| `crawler/tools/dark_horse_detector.py` | 黑马评分计算 |
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

## API 端点

Base URL: `http://localhost:5000/api/v1`

| 端点 | 方法 | 说明 |
|------|------|------|
| `/products/trending` | GET | 热门 Top 5 |
| `/products/weekly-top` | GET | 本周 Top 15 |
| `/products/dark-horses` | GET | 黑马产品 (`limit`, `min_index`) |
| `/products/today` | GET | 今日精选 (`limit`, `hours`) |
| `/products/<id>` | GET | 产品详情 |
| `/products/categories` | GET | 分类列表 |
| `/products/blogs` | GET | 博客/新闻 (`limit`, `source`) |
| `/search?q=xxx` | GET | 搜索 (`categories`, `type`, `sort`, `page`) |

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

*更新: 2026-01-19*
