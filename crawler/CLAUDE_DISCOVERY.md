# 使用 Claude 中转发现黑马

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
