# Claude Code 改进任务 Prompt

> 复制以下内容，直接给 Claude Code 用

---

## 背景

我是 WeeklyAI 的开发者。这是一个面向 AI 产品经理的"全球 AI 产品发现平台"，帮用户发现正在崛起的 AI 黑马产品。

经过资深 PM 评审，我需要实施以下改进。请先阅读 `CLAUDE.md` 了解项目全貌，然后按优先级执行。

## 当前技术栈
- **Frontend**: Next.js 16 + React 19 + SWR + TailwindCSS (`frontend-next/`)
- **Backend**: Flask + MongoDB/JSON (`backend/`)
- **Crawler**: Python + Perplexity/GLM API (`crawler/`)
- **部署**: Vercel (frontend + backend serverless)

---

## 🔴 Phase 1: 首页信息架构重构（最高优先级）

### 任务 1.1: 本周黑马改为纵向大卡片

**文件**: `frontend-next/src/components/home/home-client.tsx`

当前本周黑马区域是横向滚动小卡片，信息密度太低，用户必须点进去才能判断产品是否值得关注。

**改为**:
- 纵向排列的大卡片（类似 Product Hunt 首页风格）
- 每张卡片直接展示：产品名 + Logo + 一句话描述 + **why_matters（完整显示）** + 融资金额 + 地区标签 + 评分
- 保留"全部/硬件/软件"的 tab 切换
- 最多展示 10 个，超出折叠
- 移动端一列，桌面端两列网格
- 每张卡片高度统一，why_matters 超过 3 行用 "展开" 按钮

**设计要求**:
- 卡片左侧放 Logo（64x64），右侧放内容
- 融资金额用绿色 badge，评分用现有的红色 badge
- 地区 emoji flag 放在卡片右上角
- hover 效果：轻微 shadow 提升 + border 变色

### 任务 1.2: Hero 区文案优化

**文件**: `frontend-next/src/components/home/home-client.tsx` 或 `home-data-section.tsx`

当前数据面板（样本池/黑马候选/硬件占比/覆盖地区）对普通用户是噪音。

**改为**:
- 主标题保持："发现全球最新AI产品"
- 副标题改为："每周 5 分钟，看完全球 AI 领域最值得关注的新产品"
- 数据面板改为更有意义的指标：
  - "本周新增 X 款" (统计 discovered_at 在本周的产品数)
  - "X 款获得融资" (统计有 funding_total 的产品数)
  - "覆盖 X 个地区"（保留）
  - "累计收录 X 款"（总产品数）
- 保留"本周偏热"标签

### 任务 1.3: Swipe 卡片区域降级

**文件**: `frontend-next/src/components/home/discovery-deck.tsx`, `home-client.tsx`

Swipe 卡片交互门槛高，新用户不理解。

**改动**:
- 将"快速发现"区域从首页第二区块移到第三区块（在"更多推荐"之后）
- 或者改为一个独立的 `/discover` 页面，首页只放一个入口链接："🎲 随机发现产品 →"
- 如果保留在首页，增加一个更明显的操作引导动画（首次访问时显示）

---

## 🟡 Phase 2: 产品详情页增强

### 任务 2.1: 结构化信息展示

**文件**: `frontend-next/src/app/product/[id]/page.tsx`

当前详情页信息太扁平。改为结构化布局：

```
┌──────────────────────────────────────────┐
│ [Logo 128px]  产品名          [评分badge] │
│               分类 · 地区                 │
│               一句话描述                  │
├──────────────────────────────────────────┤
│ 📊 关键指标                              │
│ ┌─────────┬─────────┬──────────────────┐ │
│ │ 💰 融资  │ 🏷️ 估值 │ 📅 发现日期      │ │
│ │ $142.5M │ -       │ 2026-02-10      │ │
│ └─────────┴─────────┴──────────────────┘ │
├──────────────────────────────────────────┤
│ 💡 为什么重要                             │
│ (完整展示 why_matters 内容)               │
├──────────────────────────────────────────┤
│ 📰 最新动态                              │
│ (展示 latest_news 字段)                  │
├──────────────────────────────────────────┤
│ [访问官网]  [返回首页]                    │
├──────────────────────────────────────────┤
│ 🔗 相关产品 (横向滚动卡片)               │
└──────────────────────────────────────────┘
```

### 任务 2.2: 产品截图自动获取（可选，后续做）

在产品卡片和详情页添加产品官网截图。可以用以下方案之一：
- 方案 A: 使用 `https://image.thum.io/get/{url}` 免费截图 API
- 方案 B: 使用 `https://api.microlink.io/?url={url}&screenshot=true`
- 在前端用 `<img>` 加载，加 fallback 占位图（如果截图加载失败显示产品 Logo）

---

## 🟡 Phase 3: Newsletter 邮件订阅

### 任务 3.1: 前端订阅入口

**位置**: 首页底部（更多推荐之后），新建组件 `frontend-next/src/components/home/newsletter-signup.tsx`

**UI**:
```
┌──────────────────────────────────────────┐
│  📬 每周 AI 产品速递                      │
│  每周一封邮件，5 分钟看完本周最值得关注的  │
│  AI 产品                                 │
│                                          │
│  [________邮箱地址________] [订阅]        │
│                                          │
│  已有 XXX 位产品经理订阅                  │
└──────────────────────────────────────────┘
```

### 任务 3.2: 后端订阅 API

**方案选择**: 推荐使用 **Resend** (resend.com) 或 **Buttondown** API，轻量且免费额度够用。

**新增文件**: `backend/app/routes/newsletter.py`

```python
# POST /api/v1/newsletter/subscribe
# Body: {"email": "xxx@example.com"}
# 存储到 MongoDB 的 subscribers collection
# 返回: {"success": true, "message": "订阅成功"}

# GET /api/v1/newsletter/count
# 返回当前订阅人数（用于前端展示）
```

### 任务 3.3: 每周自动生成邮件内容

**新增文件**: `crawler/tools/generate_newsletter.py`

逻辑：
1. 从 `products_featured.json` 读取本周新增的 4-5 分产品
2. 按评分排序取 Top 5
3. 生成 HTML 邮件模板（每个产品：名称 + why_matters + 官网链接）
4. 通过 Resend API 发送给所有订阅者
5. 加到 `daily_update.sh` 的周日执行任务中

---

## 🟡 Phase 4: 产品描述语言统一

### 任务 4.1: 描述中文化

**文件**: `crawler/tools/auto_discover.py`, `crawler/prompts/analysis_prompts.py`

当前问题：产品描述和 why_matters 中英文混杂。

**改动**:
- 在 `analysis_prompts.py` 的评判 prompt 中明确要求：
  - `description` 字段必须用中文
  - `why_matters` 字段必须用中文
  - 产品名称保持英文原名
  - 数字和专有名词（如 YC, Sequoia, ARR）保持英文
- 增加一个后处理函数 `ensure_chinese_description()` 在 `auto_discover.py` 中调用，检测 description 是否为中文，如果是英文则调用 LLM 翻译

### 任务 4.2: 历史数据修复

**新增脚本**: `crawler/tools/translate_descriptions.py`

批量翻译现有英文 description 和 why_matters 为中文：
1. 读取 `products_featured.json`
2. 检测每个产品的 description/why_matters 语言
3. 如果是英文，调用 Perplexity/GLM 翻译为中文
4. 保持产品名、融资金额、专有名词为英文
5. Dry-run 模式 + 备份

---

## 注意事项

1. **每个 Phase 完成后都要跑测试**: `cd frontend-next && npm run build` 确保没有 build error
2. **不要动 crawler 的核心评分逻辑**（`dark_horse_detector.py`）
3. **保持后端 JSON fallback 兼容性**：所有 MongoDB 操作都要有 JSON 降级
4. **CSS 用 TailwindCSS**，不要引入新的 CSS 框架
5. **组件命名遵循现有风格**: kebab-case 文件名，PascalCase 组件名

---

## 执行顺序

```
Phase 1.1 (大卡片) → Phase 1.2 (Hero文案) → Phase 1.3 (Swipe降级)
→ Phase 2.1 (详情页结构化) → Phase 3.1-3.2 (Newsletter前后端)
→ Phase 4.1 (prompt中文化) → Phase 4.2 (历史数据翻译)
```

一次做一个任务，做完给我看效果再继续下一个。
