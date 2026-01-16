# WeeklyAI - Claude 项目入口

> 全球 AI 产品灵感库 + 黑马发现平台

## 快速了解项目（按顺序阅读）

### 1. 核心文档
| 优先级 | 文件 | 内容 |
|--------|------|------|
| ⭐⭐⭐ | `INSTRUCTIONS.md` | 项目定位、评分标准、工具速查 |
| ⭐⭐ | `crawler/tools/auto_discover.py` | 自动发现脚本 (Web Search MCP) |
| ⭐ | `session-*.md` | 最近的会话记录，了解进度 |

### 2. 数据结构
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

### 3. 关键代码
| 文件 | 职责 |
|------|------|
| `crawler/tools/auto_discover.py` | Web Search + GLM 自动发现 |
| `crawler/tools/add_product.py` | 手动添加产品 |
| `crawler/tools/dark_horse_detector.py` | 黑马评分计算 |
| `backend/app/routes/products.py` | 产品 API |
| `frontend/views/index.ejs` | 首页模板 |

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

## 定时任务 (launchd)

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

## 黑马评分标准 (1-5分)

| 分数 | 标准 |
|------|------|
| 5 | 融资>$100M / 顶级创始人 / 品类开创者 |
| 4 | 融资>$30M / YC/a16z 投资 / 高增长 |
| 3 | 融资$5M-$30M / ProductHunt Top 5 |
| 2 | 有创新点 / 数据不足 |
| 1 | 边缘 / 待验证 |

## 地区权重

| 地区 | 权重 | 搜索引擎 |
|------|------|----------|
| 🇺🇸 美国 | 40% | Bing |
| 🇨🇳 中国 | 25% | Sogou |
| 🇪🇺 欧洲 | 15% | Bing |
| 🇯🇵🇰🇷 日韩 | 10% | Bing |
| 🇸🇬 东南亚 | 10% | Bing |

## 最近更新

- 2026-01-16: 设置每日自动数据更新 (launchd)
  - 创建 `ops/scheduling/daily_update.sh` 统一更新脚本
  - 修正 plist 路径 (`Projects/WeeklyAI`)，改为每天 3:00 运行
- 2026-01-16: 集成 Zhipu Web Search MCP，支持实时全球搜索
- 详见 `session-web-search-mcp-integration-2026-01-16.md`
