# WeeklyAI 技术交接分析报告（前后端 + 数据管道 + 部署全景）
> 生成时间：2026-03-13（Asia/Shanghai）  
> 统计口径：以 `crawler/data` 与 `backend/data` 当前仓库快照为准  
> 受众：工程交接团队（实现细节优先）

## 1. 项目总览与系统边界

### 1.1 系统目标与主链路
WeeklyAI 的核心链路是：

1. 爬虫发现候选产品（分地区、分 provider）。
2. 质量过滤与评分（黑马 4-5 分、潜力股 2-3 分）。
3. 写入策展数据（`products_featured.json`，并可同步 MongoDB）。
4. Flask API 提供查询能力。
5. Next.js 前端渲染首页/发现页/搜索页/详情页/博客页。
6. 调度系统（launchd/GitHub Actions）每天增量更新。

### 1.2 当前系统边界（重要）
- 主力前端是 Next.js（`frontend-next`），但 Docker Compose 与部分 CI 仍运行遗留 Express 前端（`frontend`）。
- 后端 API 是 Flask，数据层是“Mongo 优先 + JSON 回退”。
- 爬虫是独立 Python 工具集，负责发现、清洗、发布、同步。
- 存在两套数据快照：`crawler/data` 与 `backend/data`，并非始终一致。

---

## 2. 前端深度分析（Next.js 主前端 + 遗留前端）

### 2.1 现状、影响、建议
| 主题 | 现状 | 影响 | 建议 |
|---|---|---|---|
| 前端双轨 | Next.js 为主；遗留 Express 仍在 Docker/CI 使用 | 交接时容易误判“线上到底跑哪个前端” | 明确单一生产前端；遗留前端仅保留回滚策略并标注退役日期 |
| 路由结构 | Next App Router 路由完整：`/` `/discover` `/blog` `/search` `/product/[id]` | 功能完整但与 legacy 路由并存，测试目标分裂 | 统一 E2E 目标到 Next 路由 |
| 数据获取策略 | Server Component + `react cache` + `fetch revalidate`；客户端搜索用 SWR | 一致性较好，但首页 `weekly-top?limit=0` 会拉全量数据 | 对首页/发现页改分页或限制首屏数量 |
| API 基址回退 | Server 端优先 `API_BASE_URL_SERVER`，浏览器优先 `NEXT_PUBLIC_API_BASE_URL`；本地支持 `5000 -> 5001` 回退 | 健壮性好，但浏览器 fallback `/api/v1` 在 Next 无内置代理时会 404 | 在 Next 增加 rewrites/proxy，或强制配置环境变量 |
| 国际化 | `zh-CN` / `en-US`，cookie + localStorage 双写 | 体验稳定 | 保持；补充 i18n 覆盖率检查 |
| 聊天能力 | 前端支持 SSE 优先、JSON 回退、超时切换 | 用户体验好，但依赖后端与 Perplexity 可用性 | 增加聊天健康探针和降级文案监控 |

### 2.2 前端路由与数据映射
| 页面 | 组件入口 | 主要 API |
|---|---|---|
| 首页 `/` | `HomeDataSection` | `/products/dark-horses` `/products/weekly-top` `/products/last-updated` |
| 发现 `/discover` | `DiscoverDataSection` | `/products/weekly-top` |
| 博客 `/blog` | `BlogDataSection` | `/products/blogs` |
| 搜索 `/search` | `SearchClient` | `/search/` |
| 详情 `/product/[id]` | `ProductPage` | `/products/<id>` `/products/<id>/related` |
| 聊天 | `use-chat` | `/chat` `/chat/status` |

### 2.3 前端关键证据
- [frontend-next/package.json](/Users/jun/Desktop/Projects/WeeklyAI/frontend-next/package.json)
- [frontend-next/src/lib/api-client.ts](/Users/jun/Desktop/Projects/WeeklyAI/frontend-next/src/lib/api-client.ts)
- [frontend-next/src/lib/client-home-api.ts](/Users/jun/Desktop/Projects/WeeklyAI/frontend-next/src/lib/client-home-api.ts)
- [frontend-next/src/app/layout.tsx](/Users/jun/Desktop/Projects/WeeklyAI/frontend-next/src/app/layout.tsx)
- [frontend-next/src/components/chat/use-chat.ts](/Users/jun/Desktop/Projects/WeeklyAI/frontend-next/src/components/chat/use-chat.ts)
- [frontend/package.json](/Users/jun/Desktop/Projects/WeeklyAI/frontend/package.json)
- [frontend/app.js](/Users/jun/Desktop/Projects/WeeklyAI/frontend/app.js)

---

## 3. 后端深度分析（Flask API）

### 3.1 现状、影响、建议
| 主题 | 现状 | 影响 | 建议 |
|---|---|---|---|
| 应用装配 | `create_app` 注册 `products/search/chat` 蓝图 | 结构清晰 | 保持分层，补全 API 文档自动生成 |
| 全局限流 | `/api/*` 每 IP 100 req/min（内存） | 单实例有效，多实例不共享状态 | 上线 Redis 限流（或网关限流） |
| CORS | 配置了 allowlist；未配置时回退 `*` | 开发方便，生产存在放大暴露面 | 生产环境强制非空 allowlist |
| 端口策略 | `run.py` 支持 `5000` 占用时自动降到 `5001` | 本地可用性高 | 文档显式写明 fallback 行为 |
| 数据仓库 | `MONGO_URI` 显式配置才启用 Mongo；否则 JSON | 容灾好，但环境认知门槛高 | 在启动日志里打印“当前数据源模式” |

### 3.2 API 清单（公开接口）
Base: `/api/v1`

| 模块 | 路径 | 说明 |
|---|---|---|
| products | `/products/trending` | 热门推荐 |
| products | `/products/weekly-top` | 周榜，支持 `sort_by` |
| products | `/products/<product_id>` | 产品详情 |
| products | `/products/categories` | 分类 |
| products | `/products/blogs` | 博客/新闻 |
| products | `/products/dark-horses` | 黑马 |
| products | `/products/rising-stars` | 潜力股 |
| products | `/products/today` | 最近窗口精选 |
| products | `/products/last-updated` | 数据更新时间 |
| products | `/products/<product_id>/related` | 相关推荐 |
| products | `/products/analytics/summary` | 摘要分析 |
| products | `/products/feed/rss` | RSS feed |
| products | `/products/industry-leaders` | 行业领军 |
| search | `/search/` | 搜索（q/categories/type/sort/page/limit） |
| chat | `/chat/status` | 聊天状态 |
| chat | `/chat` | 聊天（JSON/SSE） |

### 3.3 服务层关键逻辑
- 排序：`weekly-top` 默认综合分（`heat 0.65 + freshness 0.30 + funding 0.05`，新鲜度半衰期 21 天）。
- 黑马刷新：`DARK_HORSE_FRESH_DAYS` 默认 5 天，Top1 可 sticky 到 10 天。
- 搜索：支持关键词相关性 + 基础排序复合。
- Repository 缓存：产品缓存 300 秒；博客缓存由 `BLOG_CACHE_SECONDS`（默认 60 秒）控制。
- Mongo 失败后冷却：`MONGO_FAILURE_COOLDOWN_SECONDS` 默认 60 秒。
- Chat：每 IP 10 req/min，消息长度上限 2000，支持流式 SSE。

### 3.4 后端关键证据
- [backend/app/__init__.py](/Users/jun/Desktop/Projects/WeeklyAI/backend/app/__init__.py)
- [backend/app/routes/products.py](/Users/jun/Desktop/Projects/WeeklyAI/backend/app/routes/products.py)
- [backend/app/routes/search.py](/Users/jun/Desktop/Projects/WeeklyAI/backend/app/routes/search.py)
- [backend/app/routes/chat.py](/Users/jun/Desktop/Projects/WeeklyAI/backend/app/routes/chat.py)
- [backend/app/services/product_service.py](/Users/jun/Desktop/Projects/WeeklyAI/backend/app/services/product_service.py)
- [backend/app/services/product_repository.py](/Users/jun/Desktop/Projects/WeeklyAI/backend/app/services/product_repository.py)
- [backend/app/services/product_sorting.py](/Users/jun/Desktop/Projects/WeeklyAI/backend/app/services/product_sorting.py)
- [backend/config.py](/Users/jun/Desktop/Projects/WeeklyAI/backend/config.py)
- [backend/run.py](/Users/jun/Desktop/Projects/WeeklyAI/backend/run.py)

---

## 4. 爬虫与数据工程分析

### 4.1 现状、影响、建议
| 主题 | 现状 | 影响 | 建议 |
|---|---|---|---|
| Provider 路由 | CN 默认走 GLM（受 `USE_GLM_FOR_CN` 控制），其他区域走 Perplexity | 成本和区域召回可控 | 持续记录 provider 命中率与质量差异 |
| 每日配额 | 目标 `5` 黑马 + `10` 潜力股，最多 3 轮 | 节奏稳定，但产出受关键词和质量门限波动 | 把“配额达成率”纳入日报告警 |
| 质量门控 | URL/描述/why_matters/去重/来源可信/幻觉校验（GLM 场景） | 数据质量总体可控 | 对被拒原因做周度统计闭环 |
| 数据发布 | `save_product` 写周文件并同步 `products_featured.json` | 发布路径直接、见效快 | 增加事务式写入与回滚机制 |
| 社交 enrich | `rss_to_products` 可 enrich featured + 产出 pending candidates | 能提升鲜度 | 增加对 false positive 的人工抽检比例 |
| Mongo 同步 | `_sync_key` upsert + 索引保障 + candidates/blogs 同步 | 数据库查询性能好 | 将 sync 结果接入告警（插入/更新异常波动） |

### 4.2 关键规则（代码实值）
- 每日目标：黑马 5、潜力股 10。
- 区域上限：US 6、CN 4、EU 3、JP 2、KR 2、SEA 2。
- 关键词预算模式：`adaptive`（默认）/`legacy`。
- Analyze Gate 默认开启，关键词回放机制开启。
- GLM 关键词间隔默认 3 秒。
- CN 默认关键词上限 4（可配）。

### 4.3 关键证据
- [crawler/tools/auto_discover.py](/Users/jun/Desktop/Projects/WeeklyAI/crawler/tools/auto_discover.py)
- [crawler/prompts/analysis_prompts.py](/Users/jun/Desktop/Projects/WeeklyAI/crawler/prompts/analysis_prompts.py)
- [crawler/prompts/search_prompts.py](/Users/jun/Desktop/Projects/WeeklyAI/crawler/prompts/search_prompts.py)
- [crawler/tools/auto_publish.py](/Users/jun/Desktop/Projects/WeeklyAI/crawler/tools/auto_publish.py)
- [crawler/tools/rss_to_products.py](/Users/jun/Desktop/Projects/WeeklyAI/crawler/tools/rss_to_products.py)
- [crawler/tools/sync_to_mongodb.py](/Users/jun/Desktop/Projects/WeeklyAI/crawler/tools/sync_to_mongodb.py)
- [crawler/utils/perplexity_client.py](/Users/jun/Desktop/Projects/WeeklyAI/crawler/utils/perplexity_client.py)
- [crawler/utils/glm_client.py](/Users/jun/Desktop/Projects/WeeklyAI/crawler/utils/glm_client.py)
- [crawler/main.py](/Users/jun/Desktop/Projects/WeeklyAI/crawler/main.py)

---

## 5. 部署与运维分析

### 5.1 当前部署形态
| 形态 | 现状 | 风险 | 建议 |
|---|---|---|---|
| Vercel | 前后端拆分部署（文档已定义） | 需要严格环境变量治理 | 建立环境变量模板与发布前校验 |
| Docker Compose | `mongo + backend + crawler + legacy frontend` | 与 Next 主前端不一致 | 增加 `frontend-next` 服务并定义默认入口 |
| 本地调度 | launchd 每天 03:00 执行 `daily_update.sh`；新闻任务 3h 间隔 | 多套调度脚本路径有历史残留 | 统一调度脚本路径与唯一入口 |
| GitHub Actions | 有 daily update / CN update / data verification / CI/CD / legacy E2E | 流水线目标不完全一致（legacy 仍占主） | 合并为“Next 主链路 + 数据链路”双主线 |

### 5.2 调度与流水线现状
- `daily_update.sh` 已实现 10+ 步流水线（含发布、回填、解析、校验、去重、修 Logo、news、enrich、Mongo sync）。
- GitHub `daily_update.yml` UTC `19:00`（即上海次日 `03:00`）自动运行，并回写 `crawler/data` 与 `backend/data`。
- `cn_zhipu_update.yml` 支持手动触发中国区专用链路。
- `ci.yml` 的 E2E 仍对遗留前端 `frontend/app.js` 做验证，不是 Next 主前端。

### 5.3 关键证据
- [docker-compose.yml](/Users/jun/Desktop/Projects/WeeklyAI/docker-compose.yml)
- [DEPLOY.md](/Users/jun/Desktop/Projects/WeeklyAI/DEPLOY.md)
- [ops/scheduling/daily_update.sh](/Users/jun/Desktop/Projects/WeeklyAI/ops/scheduling/daily_update.sh)
- [ops/scheduling/com.weeklyai.crawler.plist](/Users/jun/Desktop/Projects/WeeklyAI/ops/scheduling/com.weeklyai.crawler.plist)
- [ops/scheduling/com.weeklyai.news.plist](/Users/jun/Desktop/Projects/WeeklyAI/ops/scheduling/com.weeklyai.news.plist)
- [ops/scheduling/run_crawler.sh](/Users/jun/Desktop/Projects/WeeklyAI/ops/scheduling/run_crawler.sh)
- [.github/workflows/daily_update.yml](/Users/jun/Desktop/Projects/WeeklyAI/.github/workflows/daily_update.yml)
- [.github/workflows/cn_zhipu_update.yml](/Users/jun/Desktop/Projects/WeeklyAI/.github/workflows/cn_zhipu_update.yml)
- [.github/workflows/ci.yml](/Users/jun/Desktop/Projects/WeeklyAI/.github/workflows/ci.yml)
- [.github/workflows/ci-cd.yml](/Users/jun/Desktop/Projects/WeeklyAI/.github/workflows/ci-cd.yml)

---

## 6. 数据现状快照（仓库当前状态）

### 6.1 核心指标（`crawler/data`）
- `products_featured.json`：`588`
- `blogs_news.json`：`0`
- 黑马周文件：`9` 个；最新 `week_2026_11.json`（`5` 条）
- 潜力股周文件：`6` 个；最新 `global_2026_11.json`（`6` 条）
- `last_updated`：`2026-03-13T03:04:05Z`
- 行业领军：`10` 类、`34` 产品

### 6.2 结构分布（`products_featured.json`）
- 评分分布：`1分=6`，`2分=66`，`3分=208`，`4分=217`，`5分=91`
- 硬件数量：`194`，占比约 `33%`
- Top 来源：`TechCrunch(63)`、`curated(35)`、`Product Hunt(29)`、`36kr(10)` 等
- 网站占位值数量：`1`
- `why_matters` 长度 `<30` 的条目：`75`（质量风险点）

### 6.3 数据快照差异（`crawler/data` vs `backend/data`）
- `backend/data/blogs_news.json` 为 `152` 条，但 `crawler/data/blogs_news.json` 当前为 `0`。
- `backend/data/rising_stars` 文件数少于 `crawler/data/rising_stars`。
- 说明当前存在“多快照不同步窗口”，会影响线上结果一致性与排障效率。

---

## 7. Public APIs / Interfaces（盘点与调用关系）

### 7.1 前端调用后端的关键约束
| 接口 | 主要调用方 | 关键约束 |
|---|---|---|
| `/products/weekly-top` | 首页、发现页 | `sort_by` 支持别名；`limit=0` 返回全量，注意性能 |
| `/products/dark-horses` | 首页 | 前端会过滤无效 website |
| `/products/blogs` | 博客页 | `source` + `market` 组合筛选 |
| `/search/` | 搜索页 | 分页上限、类型筛选、排序 |
| `/products/<id>` | 详情页 | 支持按 ID 或 name |
| `/products/<id>/related` | 详情页 | 相似推荐（分类/类型） |
| `/chat` | 聊天栏 | SSE/JSON 双模式，失败回退 |
| `/chat/status` | 聊天栏状态 | 仅返回配置可用性，不代表模型质量 |

### 7.2 接口治理结论（现状-影响-建议）
| 现状 | 影响 | 建议 |
|---|---|---|
| 接口契约主要靠代码与 Zod schema，对外缺统一 API 文档 | 新同学上手慢，变更影响难评估 | 增加 OpenAPI/Swagger 导出，联动前端 schema 测试 |
| 返回结构中中文 message 字段较多 | 对多语言客户端扩展不友好 | 保留 message 但引入稳定 machine-readable `error_code` |

---

## 8. 关键风险与技术债诊断（重点结论）

### 8.1 结论一：主力前端与 Docker/CI 仍有并行切换风险
- 现状：Next 是主力；但 Compose/CI E2E 仍偏 legacy。
- 影响：测试通过不代表 Next 生产链路通过；部署认知混乱。
- 建议：把 Next 作为唯一默认运行链路，legacy 改为显式 fallback 模式。

### 8.2 结论二：数据存在多目录快照差异，缺“单一真源”
- 现状：`crawler/data` 与 `backend/data` 的 blogs/rising_stars 存在差异。
- 影响：前后端观察值不一致，导致线上问题定位困难。
- 建议：定义 SoT（建议 `crawler/data`），`backend/data` 仅镜像产物并加一致性校验。

### 8.3 结论三：部署文档与实际入口存在偏差
- 现状：文档强调 Next 主前端，但 Docker/部分 CI 默认 legacy；部分脚本路径仍含旧目录。
- 影响：新环境按文档部署可能“可运行但不一致”。
- 建议：合并部署文档，给出唯一推荐路径与兼容路径矩阵。

### 8.4 其他高优先风险
| 级别 | 风险 | 现状 | 建议 |
|---|---|---|---|
| P0 | 前端 API fallback `/api/v1` 无内建代理 | Next 中无 `app/api` 代理路由 | 增加 Next rewrites 或强制注入 API env |
| P0 | 调度路径历史残留 | `run_crawler.sh` 与 `cron.txt` 使用旧目录 | 清理并统一为 `Projects/WeeklyAI` |
| P1 | CORS 默认 `*` | 未配置 allowlist 时全开 | 生产环境强制 allowlist 非空 |
| P1 | 限流为进程内存级 | 多实例不共享 | 上 Redis 或网关限流 |
| P1 | 首页全量拉取周榜 | 数据规模增大后首屏压力升高 | 首页限制首屏数量并分页 |
| P2 | 测试覆盖偏工具层 | Next UI/SSR 与后端契约联测不足 | 增加契约测试与 Next E2E |

---

## 9. 30/60/90 天改造路线图（P0/P1/P2）

### 9.1 Day 0-30（P0：先消除认知与运行分叉）
| 任务 | 收益 | 依赖 | DoD |
|---|---|---|---|
| 统一生产前端为 `frontend-next` | 消除“主/遗留混跑”风险 | 调整 Compose 与 CI | Compose 默认起 Next；CI 主流水线验证 Next 路由 |
| 建立数据单一真源策略 | 消除数据不一致排障成本 | 定义 SoT 与同步脚本 | 每次日更后自动执行 `crawler/data` vs `backend/data` 一致性检查并报警 |
| 收敛部署文档与入口 | 降低部署失败率 | 文档与脚本清理 | 只保留一份主部署 runbook，路径/端口/变量全可执行 |
| 修复 API 代理缺口 | 防止生产 fallback 404 | Next 配置 | 无环境变量时前端仍可访问后端 API |

### 9.2 Day 31-60（P1：提升稳定性与可观测性）
| 任务 | 收益 | 依赖 | DoD |
|---|---|---|---|
| CORS 与限流生产化 | 提升安全与抗压 | Redis 或网关组件 | CORS 无 `*`；限流跨实例一致 |
| 接口契约化（OpenAPI + schema 测试） | 降低前后端联调成本 | 路由/类型梳理 | 每次 CI 校验接口契约兼容性 |
| 数据质量门禁升级 | 减少低质量条目进入 featured | verifier 与规则阈值 | `why_matters` 等关键字段低质量率持续下降并纳入 CI 报告 |

### 9.3 Day 61-90（P2：扩展与性能阶段）
| 任务 | 收益 | 依赖 | DoD |
|---|---|---|---|
| 爬虫任务编排分层（发现/验证/发布） | 便于并行扩展与容错 | 任务拆分 | 任一子任务失败不影响全链路；可重放 |
| 首页与搜索性能优化 | 降低首屏/查询压力 | API 分页策略 | 首页首屏请求量受控；P95 响应下降 |
| 可观测性体系（日志+指标+告警） | 缩短故障定位时间 | 监控平台接入 | 关键链路有统一 dashboard 与告警阈值 |

---

## 10. 事实校验与交付说明

### 10.1 本次校验已覆盖
1. 事实一致性：端口、路径、变量名、调度时间、关键脚本入口已对齐代码。
2. 数据一致性：数量型结论均来自当前仓库快照脚本统计。
3. 架构闭环：前端、后端、爬虫、调度、CI/CD 均包含输入/处理/输出/回退。
4. 可执行性：路线图每项均给出收益、依赖、DoD。

### 10.2 本次未做
1. 未修改任何代码与配置文件。
2. 未执行全量自动化测试（报告基于静态代码与数据快照审计）。

---

如果你要下一步落地，建议从 P0 第一项开始：先把 Compose 与 CI 的默认前端统一到 `frontend-next`，再收敛数据单一真源。
