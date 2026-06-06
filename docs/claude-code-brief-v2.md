# Claude Code Brief — WeeklyAI v2（续）

> 把这份连同前一次的「subtraction 总纲」一起发给 Claude Code。
> 设计源真理是 `docs/hero-mockup.html`，按它来实现。

---

## 上下文（先读）

这是前一次「subtraction 总纲」的延续。如果上次的指令还在你的上下文里，跳过本节。否则先读项目根的 `CLAUDE.md` 和 `PRD-v2.md` 来跟上哲学：

- 产品定位：每日一个"想点进去看看"的 AI 产品 + 一条 AI 新闻流，面向所有对 AI 感兴趣的人。
- 不限来源：大厂或小作坊都行，要的是"oh shit"瞬间，不是融资规模。
- 数据模型：1-5 分 `dark_horse_index` 已弃用，改为 `screenshot_worthy: bool` + `hook: enum`。
- 抓取池：众筹 / Show HN / 大厂 release 为主，融资新闻 ~15% 副池。
- 发布机制：编辑器 CLI 审核（`crawler/tools/curate.py`），不自动发布。
- 首页三段：Hero + Recent picks 横滑条 + AI 新闻流，其他全部删（swipe deck / 黑马区块 / 更多推荐）。

**Hero 视觉源真理**：`docs/hero-mockup.html` —— 浏览器打开能看到四种状态（默认 / 长按预览 / 空状态 / 无图兜底）以及颜色 / 字体 / 排版规范。**严格对齐这个文件**。

---

## 工作流：Phase 1 → Phase 4 → Phase 3

**每个 Phase 之前先给我 5-bullet 的计划，等我确认后再写代码。** 不要一口气把三个 phase 都做完。

---

## Phase 1 — 整页 mockup

产出 `docs/homepage-mockup.html`：单文件、纯 HTML + CSS、移动端视口（~380px 宽，可纵向滚动），从上到下展示完整首页：

1. **Hero 卡片**（顶部）—— 直接使用 `hero-mockup.html` 的「默认（有图）」版式。用一个真实感的样例产品（例如 AI 盆栽）。
2. **Recent picks 横滑条**（紧接 Hero 下方）—— 7 张迷你卡横向滚动。每张 ~120px × 160px：小图 or hook 色块 + 产品名（一行截断）+ 日期小字。点击跳产品详情页。
3. **AI 新闻流**（再下方）—— 纵向列表。每条：source logo（16px）+ source 名 + 日期 · 标题（1-2 行）+ 一行摘要。气质要跟 Hero 的"杂志编辑"感配套：source 名用衬线，正文用 sans，垂直留白要慷慨。
4. **页脚**—— 极小字：`WeeklyAI · No.127 · 2026.5.30 · curated by ChenJunHsu`

约束：
- 与 `hero-mockup.html` 共用同一套 CSS 变量（hook 色、字体栈、文字色），新增的变量写在文件顶部
- 字体只用 400 / 500 两个字重；句首大写，禁 ALL CAPS / Title Case
- 不引外部框架，单文件，能在浏览器直接打开
- 完成后给我看，**我们要在这里迭代一轮再进下一个 phase**

---

## Phase 4 — Hook 分类规范

产出 `crawler/prompts/hook_classification.md`。对 6 个 hook 各写：

1. **定义**——一句话
2. **正例**——2-3 个具体真实的产品 + 为什么算这个 hook
3. **反例**——2-3 个看起来像但不是的产品 + 为什么不算
4. **撞类规则**——可能同时符合多个 hook 时的优先级
5. **视觉色**——从 `hero-mockup.html` 取的 hex

6 个 hook：

| Hook | 颜色 | 大致方向 |
|---|---|---|
| `weird_form` | `#5d8a4e` | 非传统物理形态 (AI 盆栽 / 相框 / 别针 / 玩偶) |
| `new_behavior` | `#d85a30` | AI 现在能做以前做不了的事 (Operator-2 跑 20 分钟无监督) |
| `unexpected_combo` | `#b94c87` | AI 接到意料之外的东西上 (AI 宠物项圈 / AI 浴室镜) |
| `quiet_real_problem` | `#5a6c7d` | 解决一个真实但不性感的问题 (法律脱敏 / 医疗记录) |
| `new_interaction` | `#b8a13a` | 新的与 AI 交互方式 (手势 / 传感器 / 环境感知) |
| `niche_depth` | `#6d4ea5` | 窄但深 (只做 X 但做到极致) |

然后更新 `crawler/prompts/analysis_prompts.py`：加一个 `_load_hook_classification()` 函数，运行时读这个 markdown 文件，把内容注入 analysis prompt。这样不同地区 / 不同 provider 的 hook 判定都共享同一份规范。

完成后给我看一遍 hook_classification.md，确认完再进 Phase 3。

---

## Phase 3 — 实施

把前一次 subtraction 总纲 + 新的 Hero / 首页设计落地到代码。`docs/hero-mockup.html` 和 `docs/homepage-mockup.html` 是设计源真理，严格对齐。

### A. Crawler 改造（来自原 brief）

- 重写 `crawler/prompts/analysis_prompts.py`：删 1-5 评分，新增 `screenshot_worthy` + `hook`，注入 `hook_classification.md`，大厂版本号迭代 / 定价变化 / 本地化不算合格
- 重写 `crawler/prompts/search_prompts.py`：
  - **主池**（~65%）：众筹（Kickstarter / Indiegogo / Makuake / 摩点）/ Show HN / Product Hunt / 小米有品 / 36 氪硬件创新
  - **副池**（~20%）：大厂 release radar（OpenAI blog / Anthropic news / DeepMind / Meta AI / Apple newsroom / Xiaomi newsroom / 字节 / 腾讯 / 阿里）
  - **融资侧池**（~15%）：原有 TechCrunch / 36 氪融资查询，权重大幅下降
- 新增 `crawler/tools/curate.py`：CLI 工具，从 `crawler/data/candidates/` 取候选，逐个显示 name / website / why_matters / image / source URL，等键盘输入：
  - `y` → 写入 `products_featured.json`，标 `screenshot_worthy=true`
  - `n` → 移入 archive
  - `s` → 跳过留下次
  - `q` → 退出
- 把 `auto_publish.py` 调用从 daily 流水线移除，但保留脚本本身（打 deprecated 警告）

### B. Backend API（`backend/app/routes/products.py`）

- 新增 `GET /api/v1/products/hero` —— 返回今日 `screenshot_worthy=true` 最新一个；今日无则回退昨日且带 `is_yesterday: true` 标记
- 新增 `GET /api/v1/products/picks?limit=7` —— 最近 N 个 `screenshot_worthy=true` 产品，时间倒序
- 老端点 `dark-horses` / `rising-stars` 保留但 deprecated，过滤逻辑改为 `screenshot_worthy=true` 兼容

### C. Frontend（`frontend-next`）

**严格对齐 `docs/homepage-mockup.html`。**

- 重写 `src/app/page.tsx` + `src/components/home/home-client.tsx`
- 新增 `src/components/home/hero-card.tsx`：支持 4 状态
  - `default` — 有强图：满屏 hook 色背景 + 大标题压字
  - `active` — 长按时叠层小卡，露出补充信息
  - `empty` — 今日无 pick：昨日卡降饱和 + 顶部 pill
  - `fallback` — 无强图：白底 + 左侧 hook 色条 + 衬线引言（C 风格）
  - 状态选择：根据 `has_strong_image`、`screenshot_worthy`、`is_yesterday` 在渲染时决定
- 新增 `src/components/home/recent-picks-strip.tsx`：横滑 7 张迷你卡，调 `/picks`
- 新增 `src/components/home/news-stream.tsx`：复用现有 blog 数据，重排版匹配杂志气质
- 新增 `src/lib/hooks/use-hero.ts`、`use-picks.ts`
- 新增 `src/lib/hook-colors.ts`：6 个 hook → hex 映射，与 `hero-mockup.html` 的 CSS 变量保持一致
- **删除 / 不再使用**：`discovery-deck.tsx`（swipe card）、本周黑马区块组件、更多推荐区块组件。首页只保留 Hero + Recent picks + News 三段
- 详情页 `/product/[id]` 和 `/blog` **不动**

### D. 数据模型（增量、不破坏旧数据）

- TS：`frontend-next/src/types/product.ts` 加 `screenshot_worthy: boolean`、`hook: HookType`、`has_strong_image: boolean`
- Python：crawler / backend 的产品验证加这些字段
- Zod：`frontend-next/src/lib/schemas/` 更新
- 旧字段 `dark_horse_index` / `criteria_met` 保留并加 `@deprecated` 注释

### E. 每日流水线（`ops/scheduling/daily_update.sh`）

- 移除第 2 步 `auto_publish.py`，替换为打印 `"N 个新候选，跑 curate.py 审核"`
- 其余步骤不动（logo / dedup / news / mongo sync）

### 不要做（保持原 brief）

- 不动 product 详情页和 blog 详情页 UI
- 不删 / 不迁移旧数据文件（`crawler/data/dark_horses/*.json` 保留）
- 不做 👍/👎 反馈循环
- 不做 MongoDB schema migration
- 不"顺手"重构无关代码

### Definition of done

- `docs/homepage-mockup.html` 在浏览器渲染正常
- `crawler/prompts/hook_classification.md` 存在且被 `analysis_prompts.py` 运行时加载
- `python3 crawler/tools/auto_discover.py --region us` 跑出的候选明显不再是融资新闻为主（人工抽查 10 个，融资类 ≤ 2 个）
- `python3 crawler/tools/curate.py` 单键审核能跑通完整流程
- `cd frontend-next && npm run dev` 首页是 Hero + Recent picks + News 三段，对齐 `homepage-mockup.html`，看不到 swipe deck / 黑马区块 / 更多推荐
- Hero 卡片 4 种状态在 storybook / 测试 case 里都能正确渲染
- 既有 Python 和 Vitest 测试通过；新增 hook classification 注入的测试

---

**最后一句**：Phase 1 完成后等我确认再进 Phase 4，Phase 4 完成后等我确认再进 Phase 3。三段都不要急。
