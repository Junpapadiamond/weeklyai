# WeeklyAI - Agent 快速参考

> 本文档是 AI Agent 工作时的精简参考。完整文档见 `CLAUDE.md`。

## 项目定位

全球 AI 产品发现平台，帮 PM 发现崛起中的 AI 产品。

- **黑马** (4-5分): 高潜力 + 低曝光，首页重点推荐
- **潜力股** (2-3分): 有创新 + 早期阶段，灵感库
- **行业领军**: 已知名产品 (排除名单: `crawler/data/industry_leaders.json`)

---

## 技术栈

| 层 | 技术 |
|------|------|
| **前端 (主力)** | Next.js 16, React 19, TypeScript, Tailwind CSS, SWR — `frontend-next/` |
| **前端 (遗留)** | Express.js + EJS — `frontend/` (不再主动开发) |
| **后端** | Flask 3.0, PyMongo 4.6, MongoDB 7 — `backend/` |
| **爬虫** | Python 3.9+, Perplexity API, Zhipu GLM — `crawler/` |
| **存储** | MongoDB (主要, `MONGO_URI`), JSON 文件 (回退) |
| **测试** | Pytest, Vitest, Playwright |

---

## 项目结构速查

```
WeeklyAI/
├── frontend-next/               # 主力前端 (Next.js 16)
│   ├── src/app/                 # 页面: home, product/[id], blog, discover, search
│   ├── src/components/          # 组件: home/, product/, discover/, common/, layout/
│   ├── src/lib/                 # api-client, product-utils, schemas, favorites
│   └── src/types/               # TypeScript 类型
├── backend/                     # Flask API
│   ├── app/routes/              # products.py, search.py
│   └── app/services/            # product_repository, product_service, product_filters, product_sorting
├── crawler/                     # AI 发现引擎
│   ├── tools/                   # 33 工具脚本 (auto_discover, rss_to_products, sync_to_mongodb...)
│   ├── utils/                   # perplexity_client, glm_client, dedup, social_sources...
│   ├── prompts/                 # search_prompts, analysis_prompts
│   ├── spiders/                 # 17 爬虫 (含 youtube_spider, x_spider)
│   └── data/                    # products_featured.json, blogs_news.json, dark_horses/...
├── ops/scheduling/              # daily_update.sh (10步流水线), launchd
└── tests/                       # 12 个 Python 测试文件 (+ frontend-next Vitest)
```

---

## 关键文件

### 爬虫核心
| 文件 | 用途 |
|------|------|
| `crawler/tools/auto_discover.py` | 主发现引擎 (cn→GLM, 其他→Perplexity) |
| `crawler/tools/auto_publish.py` | 候选 → featured 发布 |
| `crawler/tools/rss_to_products.py` | 社交信号 enrich featured |
| `crawler/tools/sync_to_mongodb.py` | JSON → MongoDB 同步 |
| `crawler/tools/fix_logos.py` | Logo 自动修复 |
| `crawler/tools/cleanup_unknowns_and_duplicates.py` | 去重 + 清理 |
| `crawler/utils/perplexity_client.py` | Perplexity SDK |
| `crawler/utils/glm_client.py` | 智谱 GLM SDK |
| `crawler/prompts/analysis_prompts.py` | 产品评判 Prompt (含硬件体系) |

### 后端核心
| 文件 | 用途 |
|------|------|
| `backend/app/services/product_repository.py` | 数据层 (MongoDB→JSON 回退) |
| `backend/app/services/product_service.py` | 业务逻辑 |
| `backend/app/services/product_filters.py` | 过滤/搜索匹配/数据清洗 |
| `backend/app/services/product_sorting.py` | 排序/多样化策略 |
| `backend/app/routes/products.py` | API 端点 |

### 前端核心
| 文件 | 用途 |
|------|------|
| `frontend-next/src/app/page.tsx` | 首页 |
| `frontend-next/src/components/home/home-client.tsx` | 首页客户端编排 |
| `frontend-next/src/components/home/discovery-deck.tsx` | Swipe Card |
| `frontend-next/src/lib/api-client.ts` | API 调用层 |

---

## 数据文件

| 文件 | 用途 |
|------|------|
| `crawler/data/products_featured.json` | 2-5分全量产品 (前端数据源) |
| `crawler/data/dark_horses/week_*.json` | 每周黑马 (4-5分) |
| `crawler/data/rising_stars/global_*.json` | 每周潜力股 (2-3分) |
| `crawler/data/blogs_news.json` | 新闻/博客 (YouTube/X/RSS) |
| `crawler/data/products_hot_search.json` | 热搜词数据源 |
| `crawler/data/industry_leaders.json` | 排除名单 |
| `crawler/data/source_watchlists.json` | 社交监控账号 |
| `crawler/data/logo_cache.json` | Logo URL 缓存 |

---

## 每日流水线 (10 步)

```
1. auto_discover.py --region all        → 产品发现
2. auto_publish.py                      → 发布到 featured
3. backfill_source_urls.py              → 回填 source_url
4. resolve_websites.py --aggressive     → 解析缺失官网
5. validate_websites.py                 → 验证域名
6. cleanup_unknowns_and_duplicates.py   → 去重 + 清理
7. fix_logos.py                         → Logo 修复
8. main.py --news-only                  → 新闻更新
9. rss_to_products.py --enrich-featured → 社交信号 enrich
10. sync_to_mongodb.py --all            → MongoDB 同步
```

**调度**: launchd, 每天 3:00 AM
**日志**: `crawler/logs/daily_update.log`

---

## 常用命令

```bash
# 发现
cd crawler && python3 tools/auto_discover.py --region all

# 社交信号 enrich
python3 tools/rss_to_products.py --sources youtube,x --enrich-featured --dry-run

# 同步 MongoDB
python3 tools/sync_to_mongodb.py --all

# 前端开发
cd frontend-next && npm run dev    # :3001

# 后端开发
cd backend && python run.py        # :5000

# 测试
cd frontend-next && npm test
PYTHONPATH=backend:crawler python -m pytest tests/ -v
```

---

## API 端点

Base: `http://localhost:5000/api/v1`

| 端点 | 说明 |
|------|------|
| `GET /products/dark-horses` | 黑马 (4-5分) |
| `GET /products/rising-stars` | 潜力股 (2-3分) |
| `GET /products/weekly-top` | 本周 Top 15 |
| `GET /products/trending` | 热门 Top 5 |
| `GET /products/today` | 今日精选 |
| `GET /products/<id>` | 产品详情 |
| `GET /products/<id>/related` | 相关产品推荐 |
| `GET /products/blogs` | 新闻/博客 |
| `GET /products/categories` | 分类列表 |
| `GET /products/last-updated` | 数据更新时间 |
| `GET /products/analytics/summary` | 分析摘要 |
| `GET /products/feed/rss` | RSS 订阅源 |
| `GET /products/industry-leaders` | 行业领军参考列表 |
| `GET /search?q=xxx` | 搜索 |

---

## Provider 路由

```
cn → GLM (glm-4.7, search_pro/search_pro_quark/search_std)
us/eu/jp(含日韩)/sea → Perplexity (sonar)
```

回退: `USE_GLM_FOR_CN=false` → 中国区回退到 Perplexity

---

## 质量规则

- **必填**: name, website, description, why_matters, dark_horse_index
- **URL**: 有效 http/https，禁止 placeholder
- **description**: >20 字符
- **why_matters**: >30 字符 + 具体数字/差异化，禁止泛化
- **去重**: normalized domain (`_sync_key`)
- **排除**: industry_leaders.json 中的产品

---

## 关键环境变量

| 变量 | 说明 |
|------|------|
| `MONGO_URI` | MongoDB (未设置=JSON 回退) |
| `PERPLEXITY_API_KEY` | Perplexity API |
| `PERPLEXITY_MODEL` | Perplexity 模型 (默认 `sonar`) |
| `ZHIPU_API_KEY` | 智谱 GLM API |
| `GLM_MODEL` | GLM 模型 (默认 `glm-4.7`) |
| `GLM_SEARCH_ENGINE` | `search_pro` / `search_pro_quark` / `search_std` |
| `USE_GLM_FOR_CN` | 中国区 GLM 开关 |
| `CONTENT_YEAR` | 年份过滤 (默认 2026) |
| `SOCIAL_HOURS` | 社交信号回溯 (默认 96h) |
| `DARK_HORSE_FRESH_DAYS` | 黑马新鲜期 (默认 5) |
| `DARK_HORSE_STICKY_DAYS` | TOP1 保留期 (默认 10) |

---

*更新: 2026-02-25 | 完整文档: CLAUDE.md*
