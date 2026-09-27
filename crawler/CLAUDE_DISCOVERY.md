# 使用 Claude 中转发现黑马

2026-09-26 排查：每日任务的 Perplexity 返回 401、GLM 返回 429，预检失败导致后续发布、同步与 demo 预生成均跳过。现在每日任务默认使用 Claude，密钥需配置到 GitHub Actions secrets；Vercel 只负责提供 API、读取 MongoDB/部署快照，不运行长时间爬虫。

### 来源与可选 Exa

`DISCOVERY_SEARCH_PROVIDER=rss` 是当前部署默认。`auto` 在配置 `EXA_API_KEY` 时合并 Exa 与 RSS，Exa 故障会降级到 RSS 并在报告记录；`exa` 要求 Exa 成功（仍保留 RSS 补充），失败会明确退出。Exa 密钥只放 GitHub Actions secret / 本地忽略的环境文件。Exa 仅提供有发布日期的候选文章，最终仍读取原文、核验引用和官网链接，再交给 Claude 分析，不能凭搜索摘要直接入库。每轮最多一次 Exa 搜索、10 个结果。

量子位地址更新为 `/feed`，增加 Tech.eu、Sifted、BetaKit；保留原来源的健康记录。2026-09-26 实测 36kr 无 RSS 条目、VentureBeat 不可读、TechCrunch Funding 超出 14 天窗口，不能把 HTTP 200 当作来源可用。

`python crawler/tools/audit_discovery_sources.py --output artifacts/source-health.json` 不调用模型；检查 RSS 条目、最新发布日期、窗口内可用数和原文可读性。正常发现任务也记录这些指标，GitHub 的报告 artifact 在任务失败时仍上传。`auto_discover.py --provider claude --dry-run` 再验证模型提取与证据规则，但不发布数据。最终要检查任务发布步骤、MongoDB 同步结果，以及 Vercel 的 `/api/v1/products/last-updated` 和实际新产品，而非只看模型请求成功。

现有 `auto_discover.py` 支持 `DISCOVERY_PROVIDER=claude`：读取有发布日期的公开 RSS 和文章正文，再调用 Anthropic Messages 兼容接口提取产品。无需 Perplexity 密钥。`auto` 保留原有 Perplexity / GLM 路由。

在未提交的 `crawler/.env` 中配置（不要把密钥放进代码或前端变量）：

```dotenv
DISCOVERY_PROVIDER=claude
CLAUDE_API_BASE_URL=https://api.intenext.ai/v1
CLAUDE_MODEL=claude-sonnet-5
CLAUDE_API_KEY=<your-secret>
CLAUDE_DISCOVERY_DAYS=14
CLAUDE_DISCOVERY_MAX_CALLS=6
CLAUDE_DISCOVERY_MAX_ARTICLES=12
```

从仓库根目录运行：

```sh
python crawler/tools/check_providers.py --live
python crawler/tools/auto_discover.py --region all --dry-run
python crawler/tools/auto_discover.py --region all
```

每轮默认最多 6 次模型请求、12 篇文章，每批 2 篇，不自动重试模型请求。`--dry-run` 会产生模型费用，但不修改产品数据。报告保存在 `crawler/logs/discovery/`，包含来源、发布日期、原文证据、排除原因及实际 token 用量。扫描完成但只有已收录产品时允许零新增；新闻全部不可用或模型失败会非零退出。

产品名须出现在引用文章中；官网域名须来自文章的真实链接且主页能核验产品名称；评分 4–5 必须有两项不同且有原文引用的信号。行业领军与已有名称/域名排除。文章中没有官网的产品暂不入库。RSS 覆盖范围不同于全网搜索，不保证各地区每天都有新产品。

正式运行会备份当周分类文件和 featured，再沿用现有发布流程写入 `crawler/data`。本地后端默认从这些文件读取；已有进程需要重启或等待缓存刷新。Vercel 使用 MongoDB 或 `backend/data` 快照，需要另行同步/部署。

已有 GitHub 每日任务也支持这个配置：设置仓库变量 `DISCOVERY_PROVIDER=claude`、`CLAUDE_API_BASE_URL`、`CLAUDE_MODEL`，以及仓库 secret `CLAUDE_API_KEY`。本地 `.env` 不会自动上传为 GitHub/Vercel 配置。新闻/社交的其他 Perplexity 功能仍使用原有各自配置。
