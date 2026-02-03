# WeeklyAI

> 全球 AI 产品灵感库 + 黑马发现平台

帮 PM 发现全球正在崛起的 AI 产品，从潜力股到黑马一网打尽。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![Node](https://img.shields.io/badge/node-18+-green.svg)

## 特性

- **全球视野** - 覆盖美国/中国/欧洲/日韩/东南亚
- **智能发现** - 自动搜索 + AI 评分，每日更新
- **分层收录** - 黑马(4-5分) / 潜力股(2-3分) 分级推荐
- **创新硬件** - 重点发掘 AI 吊坠、别针、戒指等新形态硬件
- **为什么重要** - 每个产品都有清晰的价值说明

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- npm

### 安装

```bash
# 克隆项目
git clone https://github.com/your-username/WeeklyAI.git
cd WeeklyAI

# 后端依赖
cd backend
pip install -r requirements.txt

# 前端依赖
cd ../frontend
npm install

# 爬虫依赖
cd ../crawler
pip install -r requirements.txt
```

### 配置

```bash
# 创建环境变量文件
cp crawler/.env.example crawler/.env

# 编辑配置
# PERPLEXITY_API_KEY=your_perplexity_key
```

### 启动

```bash
# 启动后端 (localhost:5000)
cd backend && python run.py

# 启动前端 (localhost:3000)
cd frontend && npm start
```

## 核心功能

### 1. 自动发现

每日自动搜索全球 AI 产品，使用 Perplexity 进行智能评分。

```bash
cd crawler

# 搜索所有地区
python3 tools/auto_discover.py --region all

# 只搜索美国
python3 tools/auto_discover.py --region us

# 只搜索硬件产品
python3 tools/auto_discover.py --type hardware

# 预览模式（不保存）
python3 tools/auto_discover.py --dry-run
```

### 2. 产品评分体系

| 评分 | 层级 | 定义 | 示例 |
|------|------|------|------|
| 5分 | 现象级 | 融资>$100M / 社交爆火 / 品类开创 | Lovable, Friend Pendant |
| 4分 | 黑马 | 融资>$30M / 顶级VC背书 / 形态创新 | Plaud NotePin, Vocci |
| 3分 | 潜力股 | 融资$1M-$5M / ProductHunt上榜 | 早期有热度的产品 |
| 2分 | 观察 | 刚发布/有创新点但数据不足 | 新发布的创新产品 |

### 3. 创新硬件发掘

重点发掘非传统形态的 AI 硬件产品：

```
评分权重：形态创新 (40%) > 使用场景 (30%) > 热度信号 (15%) > 商业可行 (15%)
```

支持的创新形态：
- 可穿戴：吊坠、别针、戒指、眼镜、耳夹...
- 随身携带：卡片、钥匙扣、手机配件...
- 桌面/家居：AI 相框、台灯、镜子、玩偶...
- 特定场景：宠物项圈、儿童手表、运动装备...

### 4. 数据管理工具

```bash
cd crawler

# 清理重复数据
python3 tools/clean_duplicates.py --analyze-only  # 分析
python3 tools/clean_duplicates.py --backup        # 清理并备份

# 修复产品 Logo
python3 tools/fix_logos.py --dry-run  # 预览
python3 tools/fix_logos.py            # 执行

# 手动添加产品
python3 tools/add_product.py --quick "产品名" "URL" "描述"
```

## 项目结构

```
WeeklyAI/
├── frontend/           # 前端 (EJS + Express)
│   ├── views/         # 页面模板
│   └── public/        # 静态资源
├── backend/           # 后端 API (Python + Flask)
│   └── app/
│       └── routes/    # API 路由
├── crawler/           # 爬虫和数据处理
│   ├── tools/         # 工具脚本
│   ├── prompts/       # AI Prompt 模块
│   ├── utils/         # 工具函数
│   └── data/          # 数据文件
│       ├── products_featured.json  # 精选产品
│       └── industry_leaders.json   # 行业领军
└── ops/               # 运维
    └── scheduling/    # 定时任务
```

## API 端点

Base URL: `http://localhost:5000/api/v1`

| 端点 | 方法 | 说明 |
|------|------|------|
| `/products/weekly-top` | GET | 本周 Top 15 |
| `/products/dark-horses` | GET | 黑马产品 (4-5分) |
| `/products/rising-stars` | GET | 潜力股 (2-3分) |
| `/products/today` | GET | 今日精选 |
| `/products/<id>` | GET | 产品详情 |
| `/search?q=xxx` | GET | 搜索产品 |

## 定时任务

使用 macOS launchd 每日自动更新：

```bash
# 安装定时任务
launchctl unload ~/Library/LaunchAgents/com.weeklyai.crawler.plist 2>/dev/null
cp ops/scheduling/com.weeklyai.crawler.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.weeklyai.crawler.plist

# 查看状态
launchctl list | grep weeklyai

# 手动运行
./ops/scheduling/daily_update.sh

# 查看日志
tail -f crawler/logs/daily_update.log
```

**运行时间**: 每天凌晨 3:00

## 数据模板

### 创新硬件

```json
{
  "name": "Friend Pendant",
  "website": "https://friend.com",
  "description": "AI 伴侣项链，Claude 驱动的 always-on 情感陪伴设备",
  "category": "hardware",
  "hardware_type": "innovative",
  "form_factor": "pendant",
  "use_case": "emotional_companion",
  "innovation_traits": ["non_traditional_form", "voice_first", "affordable"],
  "price": "$99",
  "dark_horse_index": 5,
  "why_matters": "AI 伴侣吊坠，Claude 驱动，$99 无订阅，Twitter 现象级爆火"
}
```

### 软件产品

```json
{
  "name": "Lovable",
  "website": "https://lovable.dev",
  "description": "AI-first full-stack development platform",
  "category": "coding",
  "funding_total": "$100M",
  "dark_horse_index": 5,
  "why_matters": "8个月从0到独角兽，AI原生代码编辑器，Sequoia领投"
}
```

## 地区覆盖

| 地区 | 权重 | 搜索引擎 |
|------|------|----------|
| 美国 | 40% | Bing |
| 中国 | 25% | Sogou |
| 欧洲 | 15% | Bing |
| 日韩 | 10% | Bing |
| 东南亚 | 10% | Bing |

## 开发指南

### 添加新的搜索关键词

编辑 `crawler/tools/auto_discover.py` 中的 `KEYWORDS_SOFTWARE` 或 `KEYWORDS_HARDWARE`。

### 修改评分标准

编辑 `crawler/prompts/analysis_prompts.py` 中的评分 Prompt。

### 添加新的 API 端点

在 `backend/app/routes/products.py` 中添加新路由。

## 技术栈

- **前端**: Express.js, EJS, Tailwind CSS
- **后端**: Python, Flask
- **AI**: Perplexity Sonar
- **数据**: JSON 文件存储
- **定时任务**: macOS launchd

## License

MIT

---

Made with AI for AI enthusiasts.
