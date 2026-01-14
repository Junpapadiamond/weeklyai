# WeeklyAI - Claude Code 执行指令

> **核心定位**：AI PM 的黑马产品灵感源，不是工具目录
>
> **一句话**：帮 PM 发现那些正在崛起但还没被大众注意到的 AI 产品

---

## 🚀 快速启动

```bash
cd WeeklyAI/frontend && npm start  # 前端 localhost:3000
cd WeeklyAI/backend && python run.py  # 后端 API
cd WeeklyAI/crawler && python main.py  # 爬虫更新
```

---

## ⚠️ 重要决策：数据源调整

### 🗑️ 必须移除
```
- [ ] 移除 HuggingFace 爬虫和数据
- [ ] 移除 GitHub 爬虫和数据
- [ ] 清理数据库中 source='huggingface' 或 source='github' 的记录
```

**原因**：这些是模型/开发库，不是终端产品，对 PM 无用，稀释内容质量。

### ✅ 保留的数据源
```
- ProductHunt API → 真实产品发布
- TechCrunch/Verge RSS → 行业新闻
- HackerNews API → 话题讨论
- 手动策展 JSON → 黑马产品 (crawler/data/dark_horses/)
```

---

## 📋 执行任务（按优先级）

### P0 - 今天做

1. **移除 HuggingFace/GitHub 数据源**
   - 删除或禁用 `crawler/sources/huggingface.py`
   - 删除或禁用 `crawler/sources/github.py`
   - 清理数据库/JSON 中相关数据

2. **添加"🦄 本周黑马"UI 板块**
   - 数据已在 `products_featured.json`，有 `dark_horse_index` 字段
   - 在首页热门推荐上方/下方添加黑马展示区
   - 显示：产品名、一句话亮点、融资额、成立时间

### P1 - 本周做

3. **修复 404 路由**
   - `/blog` → 博客动态页
   - `/search` → 搜索功能
   - `/product/:id` → 产品详情页

4. **产品卡片增强**
   - 添加字段显示：`why_matters`（为什么重要）
   - 添加字段显示：`funding_total`（融资额）
   - 添加"官网直达"按钮

### P2 - 之后做

5. **创建黑马数据目录结构**
   ```
   crawler/data/dark_horses/
   ├── week_2026_03.json  # 按周组织
   └── template.json      # 模板文件
   ```

---

## 🦄 黑马产品数据模板

```json
{
  "name": "Emergent",
  "slug": "emergent",
  "website": "https://emergent.sh",
  "logo": "https://...",
  "description": "Non-developers can build full-stack apps with AI agents",
  "category": "AI 建站",
  "region": "🇺🇸",
  "founded_date": "2025-01",
  "funding_total": "$23M Series A",
  "dark_horse_index": 5,
  "why_matters": "100万用户，$15M ARR，Lightspeed领投，8个月从0到独角兽",
  "latest_news": "2025-09 完成 Series A",
  "discovered_at": "2026-01-14",
  "source": "TechCrunch"
}
```

---

## 🎯 产品质量标准（严格执行）

一个产品必须满足：
- ✅ 有独立官网（不是 github.com 或 huggingface.co）
- ✅ 是终端用户可使用的产品（不是开发库/模型）
- ✅ 有品牌、logo
- ✅ 能回答"一个 PM 为什么要关注它"

**不收录**：
- ❌ HuggingFace Models（如 Llama-3.1-8B）
- ❌ GitHub 开发库（如 transformers, langchain）
- ❌ 没有官网的 demo/prototype
- ❌ 描述是"xxx相关的AI工具"这种废话

---

## 🔥 必须收录的黑马产品

### 闪电独角兽
| 产品 | 官网 | 亮点 |
|------|------|------|
| Thinking Machines Lab | thinkingmachines.ai | Mira Murati 创立，10个月融$2B |
| Safe Superintelligence | ssi.inc | Ilya Sutskever 创立，$32B估值 |
| Emergent | emergent.sh | 非开发者AI建站，$23M Series A |
| Lovable | lovable.dev | 8个月0到独角兽，欧洲最快 |

### CES 2026 硬件
| 产品 | 官网 | 亮点 |
|------|------|------|
| LG CLOiD | lg.com | 家用人形机器人，做饭洗衣叠衣服 |
| 1X NEO | 1x.tech | $20,000消费级人形机器人 |
| Rokid AI Glasses | rokid.com | 日常穿戴AI眼镜 |

### AI Coding 新势力（不是 Cursor/Copilot）
| 产品 | 官网 | 亮点 |
|------|------|------|
| Devin | cognition.ai | 全自主AI软件工程师 |
| Kiro | kiro.dev | AWS背景，规范驱动开发 |
| Goose | block.github.io/goose | Block开源，本地运行 |

---

## 📊 数据更新策略（学生预算版）

```
自动化（免费）:
├── ProductHunt API → 每12小时 cron
├── TechCrunch RSS → 每12小时 cron
└── HackerNews API → 每12小时 cron

手动（每周30分钟）:
├── 用 Claude 搜索 "AI startup funding this week"
├── 输出结构化 JSON
└── 审核后放入 dark_horses/ 目录
```

---

## ✅ 成功标准

> "一个 AI PM 每周一打开 WeeklyAI，10分钟内发现 3 个他从没听说过但立刻想深入了解的产品。"

**不追求**：产品数量最多、功能介绍最全
**追求**：发现价值最高、信息最新鲜、每个产品都有"为什么重要"

---

*版本: 7.0 | 更新: 2026-01-14*
*核心变更: 砍掉 HuggingFace/GitHub，专注黑马产品*
