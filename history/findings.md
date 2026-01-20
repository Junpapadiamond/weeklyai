# Findings: 全球化 AI 产品采集研究

> **任务**: 扩展 WeeklyAI 全球覆盖
> **更新时间**: 2026-01-16

---

## 📊 当前数据状态

```
黑马产品 (4-5分): 24 个
├── TechCrunch: 7
├── ProductHunt: 5
├── Y Combinator: 5
├── Crunchbase: 4
├── Bloomberg: 1
└── 其他: 2

地区分布:
├── 🇺🇸 美国: ~18 个 (75%)
├── 🇩🇪 德国: 1 个 (Parloa)
├── 🇧🇪 比利时: 1 个 (Alice)
├── 🇦🇪 中东: 1 个 (MilkStraw)
└── 其他: 3 个
```

**发现**: 当前数据严重偏向美国，缺乏亚洲和欧洲产品

---

## 🔍 全球 AI 产品渠道研究

### 中国渠道

| 渠道 | URL | API/RSS | 备注 |
|------|-----|---------|------|
| 36氪 | 36kr.com | 有 RSS | 融资信息最全 |
| 钛媒体 | tmtpost.com | 有 RSS | 深度分析 |
| IT桔子 | itjuzi.com | 需付费 API | 融资数据库 |
| 极客公园 | geekpark.net | 有 RSS | 产品评测 |
| 少数派 | sspai.com | 有 RSS | 效率工具 |
| 机器之心 | jiqizhixin.com | 有 RSS | AI 专业 |

### 日本渠道

| 渠道 | URL | 语言 | 备注 |
|------|-----|------|------|
| Bridge | thebridge.jp | 日/英 | 日本创业 |
| TechCrunch Japan | jp.techcrunch.com | 日文 | 本地化报道 |
| Coral Capital | coralcap.co | 英文 | VC 视角 |

### 韩国渠道

| 渠道 | URL | 语言 | 备注 |
|------|-----|------|------|
| Platum | platum.kr | 韩/英 | 韩国创业 |
| BeSUCCESS | besuccess.com | 英文 | 国际化报道 |

### 东南亚渠道

| 渠道 | URL | 覆盖 | 备注 |
|------|-----|------|------|
| e27 | e27.co | 东南亚 | 新加坡为主 |
| Tech in Asia | techinasia.com | 亚太 | 付费内容多 |
| KrASIA | kr-asia.com | 亚洲 | 36氪国际版 |
| DealStreetAsia | dealstreetasia.com | 东南亚 | 融资数据 |

### 欧洲渠道

| 渠道 | URL | 覆盖 | 备注 |
|------|-----|------|------|
| Sifted | sifted.eu | 欧洲 | FT 旗下 |
| EU-Startups | eu-startups.com | 泛欧 | 免费内容多 |
| Tech.eu | tech.eu | 泛欧 | 深度报道 |

---

## 💡 关键发现

### 1. 评分体系需要扩展
- 当前只有 1-5 分，但只关注 4-5 分
- 建议: 明确 2-3 分的"潜力股"定义和价值

### 2. 地区标签系统
- 当前用 emoji 标记地区 (🇺🇸, 🇨🇳)
- 需要标准化: ISO 国家代码 + emoji

### 3. 语言处理
- 中国/日本/韩国产品需要翻译
- 建议: 原文 + AI 翻译的 `description_en` 字段

### 4. 货币统一
- 中国: CNY/RMB
- 日本: JPY
- 韩国: KRW
- 建议: 添加 `funding_usd` 统一字段

---

## 🎯 潜力股 (2-3分) 定义

```
3分 - 值得关注:
  - 融资 $1M-$5M
  - 小众 ProductHunt 上榜
  - 本地市场有一定热度
  - 有独特创新点

2分 - 观察中:
  - 刚成立或刚发布
  - 有潜力但缺乏数据
  - 技术/产品有亮点
  - 等待更多验证
```

---

## 📁 建议的数据结构

```
crawler/data/
├── dark_horses/           # 4-5分黑马
│   ├── week_2026_03.json
│   └── ...
├── rising_stars/          # 2-3分潜力股 (新增)
│   ├── global_2026_03.json
│   └── ...
├── regions/               # 按地区分类 (可选)
│   ├── china.json
│   ├── japan.json
│   └── ...
└── products_featured.json # 综合展示
```

---

*下次更新: 添加具体产品发现*
