import type { Product } from "@/types/api";
import { DEFAULT_LOCALE, pickLocaleText, type SiteLocale } from "@/lib/locale";
import logoManifest from "@/lib/generated/logo-manifest.json";

const INVALID_WEBSITE_VALUES = new Set(["unknown", "n/a", "na", "none", "null", "undefined", ""]);
const PLACEHOLDER_VALUES = new Set(["unknown", "n/a", "na", "none", "tbd", "暂无", "未公开", "待定", "unknown.", "n/a."]);
const COMPOSITE_HEAT_WEIGHT = 0.65;
const COMPOSITE_FRESHNESS_WEIGHT = 0.3;
const COMPOSITE_FUNDING_WEIGHT = 0.05;
const FRESHNESS_HALF_LIFE_DAYS = 21;
type ProductTextField = "description" | "why_matters" | "latest_news";
type ProductTextOverride = Partial<Record<ProductTextField, string>>;
const DIRECTION_IGNORED = new Set([
  "hardware",
  "software",
  "other",
  "tool",
  "tools",
  "ai",
  "ai tool",
  "ai_tool",
  "ai tools",
  "ai_tools",
  "ai hardware",
  "ai_hardware",
  "ai 工具",
  "ai_工具",
  "ai 硬件",
  "ai_硬件",
  "innovative",
  "non traditional form",
  "non_traditional_form",
  "single use case",
  "single_use_case",
  "media coverage",
  "media_coverage",
  "social buzz",
  "social_buzz",
  "affordable",
  "always on",
  "always_on",
  "portable",
  "lifestyle",
  "traditional",
  "new form factor",
  "new_form_factor",
]);

const DIRECTION_LABELS_ZH: Record<string, string> = {
  hardware: "硬件",
  software: "软件",
  other: "其他",
  agent: "智能体",
  coding: "编程开发",
  image: "图像",
  video: "视频",
  vision: "计算机视觉",
  voice: "语音",
  writing: "写作",
  finance: "金融",
  education: "教育",
  healthcare: "医疗健康",
  enterprise: "企业服务",
  productivity: "办公效率",
  ai_chip: "AI 芯片",
  robotics: "机器人",
  driving: "自动驾驶",
  wearables: "可穿戴设备",
  smart_glasses: "智能眼镜",
  smart_home: "智能家居",
  edge_ai: "边缘 AI",
  drone: "无人机",
  simulation: "仿真",
  security: "AI 安全",
  infrastructure: "基础设施",
  legal: "法律",
  brain_computer_interface: "脑机接口",
  world_model: "世界模型",
  developer_tools: "开发工具",
  automation: "自动化",
  consumer_ai: "消费级 AI",
  ai_code: "AI 编程",
  ai_qa: "AI 质量测试",
  ai_search: "AI 搜索",
  app_builder: "应用搭建",
  collaboration: "团队协作",
  edtech: "教育科技",
  emotional_companion: "情感陪伴",
  engineering: "工程",
  hosting: "应用托管",
  local_ai: "本地 AI",
  mcp: "MCP",
  open_source: "开源工具",
  pendant: "智能挂坠",
  privacy: "隐私保护",
  screenless: "无屏设备",
  sdk: "SDK",
  testing: "软件测试",
  web_automation: "网页自动化",
};

const DIRECTION_LABELS_EN: Record<string, string> = {
  hardware: "Hardware",
  software: "Software",
  other: "Other",
  agent: "Agent",
  coding: "Coding",
  image: "Image",
  video: "Video",
  vision: "Vision",
  voice: "Voice",
  writing: "Writing",
  finance: "Finance",
  education: "Education",
  healthcare: "Healthcare",
  enterprise: "Enterprise",
  productivity: "Productivity",
  ai_chip: "AI Chips",
  robotics: "Robotics",
  driving: "Autonomous Driving",
  wearables: "Wearables",
  smart_glasses: "Smart Glasses",
  smart_home: "Smart Home",
  edge_ai: "Edge AI",
  drone: "Drones",
  simulation: "Simulation",
  security: "AI Security",
  infrastructure: "Infrastructure",
  legal: "Legal",
  brain_computer_interface: "Brain-Computer Interface",
  world_model: "World Model",
};

const UNKNOWN_COUNTRY_CODE = "UNKNOWN";
const UNKNOWN_COUNTRY_NAME = "Unknown";
const REGION_FLAG_RE = /[\u{1F1E6}-\u{1F1FF}]{2}/u;
const LOW_CONFIDENCE_LOGO_MARKERS = [
  "favicon.bing.com",
  "google.com/s2/favicons",
  "icons.duckduckgo.com",
  "icon.horse",
  "favicon.yandex.net",
  "api.faviconkit.com",
] as const;
const GENERIC_PLACEHOLDER_LOGO_MARKERS = [
  "/logos/custom/default-ai.svg",
  "/static/pwa-app/logo-default.png",
] as const;
const LOGO_MANIFEST = logoManifest as Record<string, string>;

const COUNTRY_CODE_TO_NAME: Record<string, string> = {
  US: "United States",
  CN: "China",
  SG: "Singapore",
  JP: "Japan",
  KR: "South Korea",
  GB: "United Kingdom",
  DE: "Germany",
  FR: "France",
  SE: "Sweden",
  CA: "Canada",
  IL: "Israel",
  BE: "Belgium",
  AE: "United Arab Emirates",
  NL: "Netherlands",
  CH: "Switzerland",
  IN: "India",
};

const COUNTRY_CODE_TO_NAME_ZH: Record<string, string> = {
  US: "美国",
  CN: "中国",
  SG: "新加坡",
  JP: "日本",
  KR: "韩国",
  GB: "英国",
  DE: "德国",
  FR: "法国",
  SE: "瑞典",
  CA: "加拿大",
  IL: "以色列",
  BE: "比利时",
  AE: "阿联酋",
  NL: "荷兰",
  CH: "瑞士",
  IN: "印度",
};

const COUNTRY_CODE_TO_FLAG: Record<string, string> = {
  US: "🇺🇸",
  CN: "🇨🇳",
  SG: "🇸🇬",
  JP: "🇯🇵",
  KR: "🇰🇷",
  GB: "🇬🇧",
  DE: "🇩🇪",
  FR: "🇫🇷",
  SE: "🇸🇪",
  CA: "🇨🇦",
  IL: "🇮🇱",
  BE: "🇧🇪",
  AE: "🇦🇪",
  NL: "🇳🇱",
  CH: "🇨🇭",
  IN: "🇮🇳",
};

const COUNTRY_NAME_ALIASES: Record<string, string> = {
  us: "US",
  usa: "US",
  "united states": "US",
  "u.s.": "US",
  america: "US",
  美国: "US",
  cn: "CN",
  china: "CN",
  prc: "CN",
  中国: "CN",
  sg: "SG",
  singapore: "SG",
  新加坡: "SG",
  jp: "JP",
  japan: "JP",
  日本: "JP",
  kr: "KR",
  korea: "KR",
  "south korea": "KR",
  韩国: "KR",
  gb: "GB",
  uk: "GB",
  "united kingdom": "GB",
  britain: "GB",
  england: "GB",
  英国: "GB",
  de: "DE",
  germany: "DE",
  德国: "DE",
  fr: "FR",
  france: "FR",
  法国: "FR",
  se: "SE",
  sweden: "SE",
  瑞典: "SE",
  ca: "CA",
  canada: "CA",
  加拿大: "CA",
  il: "IL",
  israel: "IL",
  以色列: "IL",
  be: "BE",
  belgium: "BE",
  比利时: "BE",
  ae: "AE",
  uae: "AE",
  "united arab emirates": "AE",
  阿联酋: "AE",
  nl: "NL",
  netherlands: "NL",
  荷兰: "NL",
  ch: "CH",
  switzerland: "CH",
  瑞士: "CH",
  in: "IN",
  india: "IN",
  印度: "IN",
};

const FLAG_TO_COUNTRY_CODE: Record<string, string> = Object.entries(COUNTRY_CODE_TO_FLAG).reduce((acc, [code, flag]) => {
  acc[flag] = code;
  return acc;
}, {} as Record<string, string>);

const DISCOVERY_REGION_FLAGS = new Set(["🇺🇸", "🇨🇳", "🇪🇺", "🇯🇵🇰🇷", "🇸🇬", "🌍"]);
const REGION_DERIVED_COUNTRY_SOURCES = new Set(["region:search_fallback", "region:fallback"]);
const COUNTRY_BY_CC_TLD: Record<string, string> = {
  cn: "CN",
  jp: "JP",
  kr: "KR",
  de: "DE",
  fr: "FR",
  se: "SE",
  ca: "CA",
  uk: "GB",
  sg: "SG",
  il: "IL",
  be: "BE",
  ae: "AE",
  nl: "NL",
  ch: "CH",
  in: "IN",
};

const ZH_PRODUCT_TEXT_OVERRIDES: Record<string, ProductTextOverride> = {
  "exa": {
    description: "面向 AI 智能体的搜索引擎，提供网页搜索和实时信息检索服务。",
  },
  "axya": {
    "description": "面向制造企业的 AI 采购平台，连接现有 ERP 系统，处理采购订单、询价和供应商沟通。",
    "why_matters": "供应商网络超过 8 万家，客户包括 GE 航空航天和 MDA Space。年度经常性收入同比翻倍，净收入留存率为 140%；产品支持风险识别和采购流程自动化。"
  },
  "feather robotics": {
    "description": "模块化人形机器人平台，开发者可以按用途调整手臂长度等硬件配置，并运行 Nvidia、Skild 或 Physical Intelligence 等公司的机器人模型。",
    "why_matters": "售价 3 万美元，约为 Unitree H2 Edu 的一半。已实现超过 100 万美元收入，并在餐厅和实验室部署，主要面向需要定制机器人硬件的开发者。"
  },
  "kontext": {
    "description": "为 AI 智能体提供运行时安全控制，监测其行为，并在执行前拦截未经授权的操作。",
    "why_matters": "通过实时评估智能体行为和执行安全策略，帮助企业管理智能体的访问权限。投资方包括 a16z CSX。"
  },
  "duqu": {
    "description": "为企业尚未收款的 B2B 发票提供短期垫款，使用 AI 自动完成约 95% 的信用评估，24 小时内转账。",
    "why_matters": "面向荷兰企业的回款需求，原始资料指出当地 46% 的 B2B 发票逾期支付。其承保系统也可供银行和贷款机构以自有品牌接入。"
  },
  "outerlimit": {
    "description": "为 AI 智能体提供去中心化的安全和授权服务。",
    "why_matters": "完成 1600 万美元种子前轮融资后首次公开亮相，投资方包括 AlbionVC 和 Evolution Equity Partners。专注智能体的权限管理和安全授权。"
  },
  "reply next": {
    "description": "帮助连锁品牌统一管理各地门店的线上信息，自动回复客户、发现经营问题并跟踪竞争对手。",
    "why_matters": "面向拥有数百至数千个门店的品牌。原始资料指出，90% 的企业不清楚 Google Maps 带来的收入，70% 未在公开渠道回复用户，不到 10% 出现在 AI 搜索结果中。"
  },
  "sakana ai": {
    "description": "日本基础模型公司，通过受自然启发的方法研发 AI 模型，并推出 AI Scientist 自动化科研工具。",
    "why_matters": "由 Transformer 论文作者 Llion Jones 和 Google Brain 东京前负责人 David Ha 创立。A 轮融资 2 亿美元，后续追加 1.35 亿美元，累计融资 4.79 亿美元；投资方包括 MUFG、SMBC、富士通和 KDDI。"
  },
  "skildai": {
    "description": "为不同类型的机器人研发通用基础模型，让机器人理解环境并执行任务。",
    "why_matters": "2026 年 1 月完成 14 亿美元 C 轮融资，主要研发方向是具身智能基础模型。"
  },
  "frankenburg technologies": {
    "description": "2024 年成立于爱沙尼亚塔林的 AI 创业公司，两年内累计融资 4300 万欧元。",
    "why_matters": "最新一轮由 SmartCap 和 Plural 领投，A 轮融资 3000 万欧元，累计融资达到 4300 万欧元。"
  },
  "ai2 robotics": {
    "description": "中国具身智能公司，围绕人形机器人研发 GOVLA 等模型和控制系统。",
    "why_matters": "B 轮融资超过 10 亿元，估值突破 100 亿元，投资方包括百度和 CRRC Capital。资金用于机器人模型研发与量产。"
  },
  "vertical compute": {
    "description": "比利时 AI 芯片公司，通过新型存储器件和芯粒设计，缓解 AI 计算中的内存瓶颈。",
    "why_matters": "从 imec 分拆后一年内，完成首颗 3D 存储与逻辑集成测试芯片的流片。累计融资 5700 万欧元，其中新增融资 3700 万欧元，目标是不更换 CPU 或 GPU 就能提高内存效率。"
  },
  "abridge": {
    "description": "将医生与患者的临床对话整理成结构化病历，帮助医院减少文书工作。",
    "why_matters": "2025 年两轮融资合计 5.5 亿美元，估值达到 53 亿美元。产品直接融入医院的病历记录流程。"
  },
  "anysphere (cursor)": {
    "description": "Cursor 的开发公司，提供支持代码生成、编辑和问答的 AI 编程工具。",
    "why_matters": "2025 年 6 月和 11 月连续融资，估值在 5 个月内从 100 亿美元升至 293 亿美元。"
  },
  "cerebras wse-3": {
    "description": "晶圆级 AI 推理芯片，集成 4 万亿个晶体管和 44GB 片上内存，搭载于采用水冷的 CS-3 系统。",
    "why_matters": "晶体管数量约为 Nvidia B200 的 19 倍，并为 OpenAI 的高速推理服务提供算力。"
  },
  "google x gentle monster android xr glasses": {
    "description": "Google 与 Gentle Monster 合作的 AI 智能眼镜，结合时尚镜框、Android XR 和 Gemini，提供日常场景下的智能辅助。",
    "why_matters": "Google 向 Gentle Monster 投资 1 亿美元。这款产品从镜框设计和日常佩戴需求入手，降低智能眼镜的使用门槛。"
  },
  "google x warby parker android xr glasses": {
    "description": "支持配近视镜片的 AI 智能眼镜，搭载 Android XR 和 Gemini，可通过语音获取日常帮助。",
    "why_matters": "Google 计划投入最多 1.5 亿美元，并结合 Warby Parker 的直营销售渠道，将智能功能融入日常眼镜。"
  },
  "harvey": {
    "description": "面向律师事务所和企业法务的 AI 工具，支持合同审阅、法律检索和文档分析。",
    "why_matters": "以 30 亿美元估值完成 3 亿美元 D 轮融资，专注法律行业的专业工作流程。"
  },
  "hippocratic ai": {
    "description": "面向医疗机构研发 AI 产品，聚焦患者服务等医疗场景。",
    "why_matters": "2025 年两轮融资合计 2.67 亿美元，其中最新 C 轮融资 1.26 亿美元，估值为 35 亿美元。"
  },
  "robco modular ai robots": {
    "description": "面向工厂的模块化机械臂，结合示教学习和数字孪生技术完成自动化作业。",
    "why_matters": "模块化硬件方便中小制造企业按需求部署。已融资 1 亿美元用于拓展美国市场，客户包括 BMW。"
  },
  "sandboxaq": {
    "description": "研发后量子密码学和 AI 安全技术，帮助企业保护数据与系统。",
    "why_matters": "2025 年 4 月完成 4.5 亿美元 E 轮融资，估值为 57 亿美元，重点投入 AI 安全与后量子密码技术。"
  },
  "cudis ai health ring": {
    "description": "无需订阅的 AI 智能戒指，支持健康指标追踪、AI 健康教练和积分奖励。",
    "why_matters": "已售出超过 3 万台，覆盖北美、欧洲和亚洲。除了健康监测，还通过 AI 教练和积分机制鼓励用户养成习惯。"
  },
  "floglasses": {
    "description": "主打实时翻译的 AI 智能眼镜。",
    "why_matters": "专注翻译场景，减少不必要的功能和成本，并支持先试用后购买。"
  },
  "kewazo": {
    "description": "将机器人和数据分析用于建筑施工，帮助工地完成自动化作业和流程管理。",
    "why_matters": "围绕建筑机器人累计融资 1.44 亿美元，面向实际施工场景推进部署。"
  },
  "mentra live": {
    "description": "开源 AI 智能眼镜，配备高清摄像头和小程序商店，支持直播、笔记及翻译。重量 43g，续航超过 12 小时。",
    "why_matters": "通过开源操作系统和应用商店，允许开发者为眼镜添加新功能，用户也能按需求安装应用。"
  },
  "neo1": {
    "description": "印度推出的 AI 智能挂坠，可记录对话、分析情绪并整理讨论内容，无需查看屏幕。",
    "why_matters": "价格约 144 美元，包含不限量订阅服务。产品在印度 AI 峰会上亮相，主要用于对话记录和情绪分析。"
  },
  "project motoko": {
    "description": "AI 无线头显概念产品，探索游戏、日常生活和办公场景中的可穿戴交互。",
    "why_matters": "在 CES 2026 展出，采用头显形态，探索智能眼镜和挂坠之外的 AI 可穿戴设备。"
  },
  "ivee": {
    "description": "面向企业员工的 AI 技能培训平台，通过能力测评和实操训练，帮助团队学会使用 AI 工具。",
    "why_matters": "完成 100 万美元种子轮融资，投资方包括 Steven Bartlett 和 Social Impact Enterprises，并入选英国政府重点活动的合作伙伴。"
  },
  "friend": {
    "description": "AI 智能挂坠，提供实时陪伴对话和情绪支持。采用一次性购买模式，无需订阅。"
  },
  "dreame pilot 20": {
    "description": "配备双机械臂的 AI 智能吹风机，可分析发质并自动调整吹护动作。",
    "why_matters": "将机械臂用于日常吹发护理，尝试自动完成原本需要手动操作的吹护步骤。"
  },
  "godot": {
    "description": "日本行为科学 AI 公司，利用行为分析帮助个人和组织改善行动习惯。",
    "why_matters": "在 Dawn Capital 领投的 A 轮融资后，累计融资 11 亿日元，业务已从神户拓展至澳大利亚和维也纳。在大阪大肠癌筛查项目中实现 46% 的提升，并获得 WHO 奖项。"
  },
  "neureality": {
    "description": "将 NAPU 芯片与配套软件结合，为云端和边缘设备提供 AI 推理方案。",
    "why_matters": "累计融资 5965 万美元，获 SK Hynix 和 Samsung Ventures 投资。通过基础设施服务降低 AI 推理扩容的成本。"
  },
  "rokid スマートaiグラス": {
    "description": "重量 49g 的 AI 智能眼镜，配备 Micro LED 和 1200 万像素摄像头，支持 GPT-5、Gemini 视觉理解、89 种语言翻译及 AR 导航。",
    "why_matters": "将显示、拍摄、翻译和导航集成在接近普通眼镜的重量下，已在日本 Makuake 平台开启预售。"
  },
  "new aiスマートレンズ": {
    "description": "重量 38g 的智能眼镜，配备 800 万像素摄像头，支持 22 种语言实时翻译、AI 语音助手和蓝牙音频。",
    "why_matters": "采用太阳镜造型，将拍摄、翻译和语音助手整合在一起，适合户外和日常佩戴。"
  },
  "seeqc": {
    "description": "基于单磁通量子（SFQ）芯片的量子计算硬件，主要提升系统能效和扩展能力。",
    "why_matters": "2025 年 1 月完成 3000 万美元 A 轮融资，通过芯片设计解决量子计算系统的功耗与扩展问题。"
  },
  "turing inc.": {
    "description": "日本自动驾驶公司，研发端到端驾驶模型、专用算力集群 Gaggle Cluster 和生成式世界模型 Terra。",
    "why_matters": "已在东京市区实现超过 30 分钟无人工接管的自动驾驶，同时研发 Heron 多模态模型和 CoVLA 数据集。"
  },
  "exawizards(エクサウィザーズ)": {
    "description": "为企业提供生成式 AI 服务和智能体，业务从数字化咨询逐步转向订阅制产品。",
    "why_matters": "2026 财年营业利润预计同比增长约 59 倍，exaBase GenAI 和智能体业务正在推动收入从项目制向订阅制转变。"
  },
  "mujinos": {
    "description": "工业机器人操作系统，可为产线机器人自动生成动作，并统一调度多台设备协同作业。",
    "why_matters": "将数字孪生、路径规划和设备执行整合在同一套系统中，面向复杂的物流和制造场景。"
  },
  "basis": {
    "description": "面向会计师事务所和财务团队的 AI 智能体，协助处理审计、台账和日常会计工作。",
    "why_matters": "由 Accel 领投完成 1 亿美元 B 轮融资，估值达到 11.5 亿美元，专注会计行业的工作流程。"
  },
  "xross road": {
    "description": "AI 漫画创作工具，通过 HANASEE 将小说或脚本转成长篇漫画，并尽量保持角色形象一致。",
    "why_matters": "完成 150 万美元种子前轮融资，重点解决长篇漫画生成中的角色一致性和连续叙事问题。"
  },
  "modveon": {
    "description": "以身份验证为核心的系统，为政务和线上协作提供可信身份与交互记录。",
    "why_matters": "完成 1000 万美元融资，投资方包括 Coinbase Ventures，尝试将身份验证延伸到后续的线上交互。"
  },
  "genas.ai": {
    "description": "面向日本市场的 AI 视频生成平台，接入 Sora、Veo 和 Seedance 等模型，用于制作广告和短剧。",
    "why_matters": "2026 年初降低使用门槛，并增加 AI 试穿、口型同步等功能，将视频制作的多个步骤集中到同一平台。"
  },
  "ニュウジア": {
    "description": "面向日本企业提供 AI 解决方案，涵盖数字人、虚拟试衣和智能体等应用。",
    "why_matters": "陆续推出虚拟试衣、沉浸式空间和智能胸牌等产品，覆盖多种企业应用场景。"
  },
  "shizuku ai": {
    "description": "日本 AI 虚拟主播服务，使用 StreamDiffusion 等技术实现实时互动和画面生成。",
    "why_matters": "获得 a16z 投资，将实时生成技术用于虚拟角色，让角色能随对话及时做出反应。"
  },
  "tiergeo": {
    "description": "帮助企业查看和优化品牌在 AI 搜索及推荐结果中的曝光情况。",
    "why_matters": "2026 年初客户数超过 1.4 万家，并通过收购补充功能，关注 AI 搜索中的品牌可见性与信任问题。"
  },
  "helpfeel": {
    "description": "AI 知识管理平台，为客服常见问题、客户反馈分析和生成式 AI 提供结构化知识。",
    "why_matters": "E 轮第二次交割后累计融资约 29 亿日元，已服务超过 800 个站点，重点解决 AI 应用的知识准确性问题。"
  },
  "appier group": {
    "description": "面向销售和营销的 AI 软件服务，覆盖获客、转化和客户价值分析。",
    "why_matters": "将预测式 AI 与营销自动化结合，为亚洲企业提供持续使用的订阅服务。"
  },
  "nao": {
    "description": "小型人形机器人，支持多语言语音识别和肢体动作，可用于接待、教学与陪护。",
    "why_matters": "通过语音和动作与人互动，适合教室、接待区等线下服务场景。"
  },
  "switchbot onero h1": {
    "description": "面向家庭的人形机器人，学习并执行收衣、端盘等家务。",
    "why_matters": "在 CES 2026 亮相，围绕具体家务设计动作和学习能力，专注家庭使用场景。"
  },
  "linse lite": {
    "description": "轻量音频眼镜，配备开放式扬声器和通话麦克风，支持配近视镜片。",
    "why_matters": "主要满足听音频和通话的需求，以更轻的结构适配日常佩戴。"
  },
  "upscale ai": {
    "description": "AI 基础设施公司，为模型训练和推理提供算力及系统支持。",
    "why_matters": "种子轮融资达到 1 亿美元，由关注半导体和基础设施的基金联合领投。"
  },
  "j-style smart rings": {
    "description": "无屏智能戒指，支持连续健康监测、心电检测和 AI 健康提醒。",
    "why_matters": "在戒指中整合无创风险评估、心电检测和 AI 预测功能，聚焦日常健康监测。"
  },
  "snorkel ai": {
    "description": "AI 数据开发与标注平台，帮助团队准备训练数据、搭建评测流程和管理模型。",
    "why_matters": "以 13 亿美元估值完成 1 亿美元 D 轮融资，专注 AI 开发中的数据质量与标注问题。"
  },
  "valkaai": {
    "description": "来自布拉格的实时 AI 数字人和视频技术公司，服务体育与媒体行业。",
    "why_matters": "完成 1200 万欧元种子前轮融资，研发重点是可实时交互的数字人。"
  },
  "vitrealab quantum light chips": {
    "description": "研发量子光芯片的光子技术公司，为 AR 显示和视觉计算设备提供光学器件。",
    "why_matters": "通过底层光学器件缩小 AR 显示模组，为更轻便的可穿戴设备提供支持。"
  },
  "positron asimov": {
    "description": "面向 AI 推理的定制芯片，单芯片内存超过 2TB，主要解决长上下文和视频模型的内存瓶颈。",
    "why_matters": "提高单芯片的内存容量，面向视频处理、量化交易和长上下文模型等高带宽应用。"
  },
  "foodforecast": {
    "description": "来自科隆的食品科技公司，为零售和食品生产企业提供 AI 需求预测与产能规划。",
    "why_matters": "完成 800 万欧元 A 轮融资，帮助企业根据需求安排生产，减少食品损耗。"
  },
  "lmarena": {
    "description": "由加州大学伯克利分校推动的大语言模型评测平台，用于比较不同模型的表现。",
    "why_matters": "由 Felicis 领投，4 个月内估值升至 17 亿美元，主要提供大语言模型的评测和对比。"
  }
};

export function normalizeWebsite(url: string | undefined | null): string {
  if (!url) return "";
  const trimmed = String(url).trim();
  if (!trimmed) return "";
  const lower = trimmed.toLowerCase();
  if (INVALID_WEBSITE_VALUES.has(lower)) return "";
  if (!/^https?:\/\//i.test(trimmed) && trimmed.includes(".")) {
    return `https://${trimmed}`;
  }
  return trimmed;
}

export function isValidWebsite(url: string | undefined | null): boolean {
  const normalized = normalizeWebsite(url);
  return !!normalized && /^https?:\/\//i.test(normalized);
}

export function getProductWebsiteSearchUrl(name: string | undefined | null, locale: SiteLocale = DEFAULT_LOCALE): string {
  const normalizedName = String(name || "").trim();
  const query = locale === "en-US"
    ? `${normalizedName || "AI product"} official website`
    : `${normalizedName || "AI 产品"} 官网`;
  const hl = locale === "en-US" ? "en" : "zh-CN";
  return `https://www.google.com/search?hl=${encodeURIComponent(hl)}&q=${encodeURIComponent(query)}`;
}

export function normalizeLogoSource(url: string | undefined | null): string {
  if (!url) return "";
  const trimmed = String(url).trim();
  if (!trimmed) return "";

  const malformedLocal = trimmed.match(/^https?:\/\/\/+(.+)$/i);
  if (malformedLocal?.[1]) {
    const path = `/${malformedLocal[1].replace(/^\/+/, "")}`;
    return path;
  }

  if (trimmed.startsWith("/")) return trimmed;
  if (/^https?:\/\//i.test(trimmed)) return trimmed;
  if (trimmed.startsWith("//")) return `https:${trimmed}`;

  if (/^[a-z0-9.-]+\.[a-z]{2,}([/:?#]|$)/i.test(trimmed)) {
    return `https://${trimmed}`;
  }

  return "";
}

export function isValidLogoSource(url: string | undefined | null): boolean {
  const normalized = normalizeLogoSource(url);
  return !!normalized && (normalized.startsWith("/") || /^https?:\/\//i.test(normalized));
}

function isLowConfidenceLogoSource(url: string | undefined | null): boolean {
  const normalized = normalizeLogoSource(url);
  if (!normalized || normalized.startsWith("/")) return false;
  return LOW_CONFIDENCE_LOGO_MARKERS.some((marker) => normalized.includes(marker));
}

function isGenericPlaceholderLogo(url: string | undefined | null): boolean {
  const normalized = normalizeLogoSource(url);
  if (!normalized) return false;
  const lower = normalized.toLowerCase();
  return GENERIC_PLACEHOLDER_LOGO_MARKERS.some((marker) => lower.includes(marker));
}

export function shouldRenderLogoImage(url: string | undefined | null): boolean {
  const normalized = normalizeLogoSource(url);
  if (!isValidLogoSource(normalized)) return false;
  return normalized.startsWith("/");
}

function normalizeHost(value: string | undefined | null): string {
  const raw = String(value || "")
    .trim()
    .toLowerCase();
  if (!raw) return "";

  const withoutProtocol = raw.replace(/^https?:\/\//, "");
  const withoutPath = withoutProtocol.replace(/\/.*$/, "");
  const withoutPort = withoutPath.replace(/:\d+$/, "");
  const withoutWww = withoutPort.replace(/^www\./, "");
  if (!/^[a-z0-9.-]+\.[a-z]{2,}$/i.test(withoutWww)) return "";

  return withoutWww;
}

function resolveLogoHost(website: string | undefined | null): string {
  const primary = normalizeWebsite(website);
  if (isValidWebsite(primary)) {
    try {
      return normalizeHost(new URL(primary).hostname);
    } catch {
      // ignore invalid website parsing and continue fallback chain
    }
  }
  return "";
}

function normalizeProductNameKey(value: string | undefined | null): string {
  return String(value || "")
    .normalize("NFKC")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");
}

type LogoBearingEntity = Pick<Product, "_id" | "id" | "name" | "website" | "logo_url" | "logo">;

function getLogoManifestKeys(product: LogoBearingEntity): string[] {
  const keys: string[] = [];
  const id = String(product._id || product.id || "").trim();
  if (id) keys.push(`id::${id}`);

  const host = resolveLogoHost(product.website);
  const name = normalizeProductNameKey(product.name);
  if (host && name) keys.push(`hn::${host}::${name}`);
  if (host) keys.push(`host::${host}`);
  if (name) keys.push(`name::${name}`);

  return keys;
}

function getManifestLogoUrl(product: LogoBearingEntity): string {
  for (const key of getLogoManifestKeys(product)) {
    const value = normalizeLogoSource(LOGO_MANIFEST[key]);
    if (value && !isRejectedCuratedLogoSource(value)) return value;
  }
  return "";
}

function isDirectWebsiteFallbackLogo(
  value: string | undefined | null,
  website: string | undefined | null
): boolean {
  const normalized = normalizeLogoSource(value);
  if (!normalized || normalized.startsWith("/")) return false;
  const directFallbacks = getLogoFallbacks(website).filter((candidate) => !isLowPriorityProviderLogo(candidate));
  return directFallbacks.includes(normalized);
}

function isStandardIconPathLogo(value: string | undefined | null): boolean {
  const normalized = normalizeLogoSource(value);
  if (!normalized || normalized.startsWith("/")) return false;
  try {
    const pathname = new URL(normalized).pathname.toLowerCase();
    return pathname === "/apple-touch-icon.png" || pathname === "/favicon.ico";
  } catch {
    return false;
  }
}

export function resolveProductLogoSources(product: LogoBearingEntity): {
  logoUrl: string;
  secondaryLogoUrl: string;
} {
  const explicitPrimary = normalizeLogoSource(product.logo_url);
  const manifestPrimary = getManifestLogoUrl(product);
  const ordered = [
    ...(manifestPrimary && (isDirectWebsiteFallbackLogo(explicitPrimary, product.website) || isStandardIconPathLogo(explicitPrimary))
      ? [manifestPrimary, explicitPrimary]
      : [explicitPrimary, manifestPrimary]),
    normalizeLogoSource(product.logo),
  ];
  const resolved: string[] = [];
  const seen = new Set<string>();

  for (const candidate of ordered) {
    if (!candidate) continue;
    if (isRejectedCuratedLogoSource(candidate)) continue;
    if (seen.has(candidate)) continue;
    seen.add(candidate);
    resolved.push(candidate);
  }

  return {
    logoUrl: resolved[0] || "",
    secondaryLogoUrl: resolved[1] || "",
  };
}

function isGeneratedFaviconProviderLogo(url: string | undefined | null): boolean {
  const normalized = normalizeLogoSource(url);
  if (!normalized || normalized.startsWith("/")) return false;
  try {
    const host = new URL(normalized).hostname.toLowerCase();
    return (
      host.includes("favicon.bing.com")
      || host.includes("google.com")
      || host.includes("icons.duckduckgo.com")
      || host.includes("icon.horse")
      || host.includes("favicon.yandex.net")
      || host.includes("faviconkit.com")
    );
  } catch {
    return false;
  }
}

function isLowPriorityProviderLogo(url: string | undefined | null): boolean {
  const normalized = normalizeLogoSource(url);
  if (!normalized || normalized.startsWith("/")) return false;
  try {
    const host = new URL(normalized).hostname.toLowerCase();
    return host.includes("logo.clearbit.com");
  } catch {
    return false;
  }
}

function isRejectedCuratedLogoSource(url: string | undefined | null): boolean {
  return (
    isGeneratedFaviconProviderLogo(url)
    || isLowConfidenceLogoSource(url)
    || isLowPriorityProviderLogo(url)
    || isGenericPlaceholderLogo(url)
  );
}

export function getLogoFallbacks(
  website: string | undefined | null
): string[] {
  const host = resolveLogoHost(website);
  if (!host) return [];

  const directIcons = [
    `https://${host}/apple-touch-icon.png`,
    `https://${host}/favicon.ico`,
  ];
  if (!host.startsWith("www.")) {
    directIcons.push(
      `https://www.${host}/apple-touch-icon.png`,
      `https://www.${host}/favicon.ico`,
    );
  }

  return directIcons;
}

type LogoCandidatesInput = {
  logoUrl?: string | null;
  secondaryLogoUrl?: string | null;
  website?: string | null;
  sourceUrl?: string | null;
  trustPrimaryLogo?: boolean;
};

function isSameOrSubdomain(host: string, root: string): boolean {
  const h = host.toLowerCase();
  const r = root.toLowerCase();
  return h === r || h.endsWith(`.${r}`);
}

function hostFromProviderCandidate(candidate: string): string {
  try {
    const parsed = new URL(candidate);
    const host = parsed.hostname.toLowerCase();

    if (host.includes("logo.clearbit.com")) {
      return normalizeHost(decodeURIComponent(parsed.pathname).replace(/^\/+/, ""));
    }

    if (host.includes("google.com") && parsed.pathname.includes("/s2/favicons")) {
      return normalizeHost(parsed.searchParams.get("domain"));
    }

    if (host.includes("favicon.bing.com")) {
      return normalizeHost(parsed.searchParams.get("url"));
    }

    if (host.includes("icons.duckduckgo.com")) {
      return normalizeHost(parsed.pathname.replace(/^\/ip3\//, "").replace(/\.ico$/i, ""));
    }

    if (host.includes("icon.horse")) {
      return normalizeHost(parsed.pathname.replace(/^\/icon\//, ""));
    }
    return normalizeHost(host);
  } catch {
    return "";
  }
}

function isTrustedLogoSource(candidate: string, websiteHost: string): boolean {
  if (!candidate) return false;
  if (candidate.startsWith("/")) return true;
  if (!websiteHost) return false;
  const derivedHost = hostFromProviderCandidate(candidate);
  if (!derivedHost) return false;
  return isSameOrSubdomain(derivedHost, websiteHost);
}

export function getLogoCandidates(input: LogoCandidatesInput): string[] {
  const result: string[] = [];
  const seen = new Set<string>();
  const websiteHost = resolveLogoHost(input.website);

  const pushIfValid = (
    value: string | undefined | null,
    opts?: { trustExplicit?: boolean }
  ) => {
    const normalized = normalizeLogoSource(value);
    if (!isValidLogoSource(normalized)) return;
    if (isGeneratedFaviconProviderLogo(normalized)) return;
    if (isGenericPlaceholderLogo(normalized)) return;
    if (isLowPriorityProviderLogo(normalized)) return;
    if (!opts?.trustExplicit && !isTrustedLogoSource(normalized, websiteHost)) return;
    if (seen.has(normalized)) return;
    seen.add(normalized);
    result.push(normalized);
  };

  pushIfValid(input.logoUrl, { trustExplicit: input.trustPrimaryLogo });
  pushIfValid(input.secondaryLogoUrl, { trustExplicit: input.trustPrimaryLogo });
  const fallbacks = getLogoFallbacks(input.website);
  for (const fallback of fallbacks) {
    pushIfValid(fallback);
  }

  return result;
}

export function isPlaceholderValue(value: string | undefined | null): boolean {
  if (!value) return true;
  const normalized = String(value).trim().toLowerCase();
  if (!normalized) return true;
  return PLACEHOLDER_VALUES.has(normalized);
}

function isLikelyEnglish(text: string): boolean {
  const trimmed = String(text || "").trim();
  if (!trimmed) return false;
  if (/[\u4e00-\u9fff]/.test(trimmed)) return false;
  return /[A-Za-z]/.test(trimmed);
}

function normalizeProductTextKey(value: string | undefined | null): string {
  return String(value || "")
    .normalize("NFKC")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");
}

function getZhProductTextOverride(product: Product, field: ProductTextField): string {
  const key = normalizeProductTextKey(product.name);
  const direct = ZH_PRODUCT_TEXT_OVERRIDES[key]?.[field];
  if (direct) return direct;

  const withoutPunctuation = key.replace(/[().]/g, "");
  if (!withoutPunctuation || withoutPunctuation === key) return "";

  return ZH_PRODUCT_TEXT_OVERRIDES[withoutPunctuation]?.[field] || "";
}

function pickLocalizedText(product: Product, field: keyof Product, locale: SiteLocale): string {
  if (locale !== "en-US" && (field === "description" || field === "why_matters" || field === "latest_news")) {
    const override = getZhProductTextOverride(product, field);
    if (override) return override;
  }

  const zhField = String(product[field] || "").trim();
  const enField = `${String(field)}_en` as keyof Product;
  const zh = isPlaceholderValue(zhField) ? "" : zhField;
  const en = isPlaceholderValue(String(product[enField] || "").trim())
    ? ""
    : String(product[enField] || "").trim();

  if (locale === "en-US") {
    return en || (isLikelyEnglish(zh) ? zh : "");
  }

  return zh || en;
}

export function parseFundingAmount(value: string | undefined): number {
  const text = (value || "").trim();
  if (/in talks|planned|target|grant|市值|估值|valuation|market cap/i.test(text.split("(")[0])) return 0;
  const match = text.match(/^(?:US\$|USD\s*|\$)([\d,]+(?:\.\d+)?)\s*([MBK])?\b/i);
  if (!match) return 0;
  const amount = Number(match[1].replace(/,/g, ""));
  return amount * ({ B: 1000, M: 1, K: .001, "": .000001 }[match[2]?.toUpperCase() || ""] ?? 0);
}

export function getProductScore(product: Product): number {
  return product.dark_horse_index ?? product.final_score ?? product.trending_score ?? product.hot_score ?? 0;
}

export type ScoreTone = "5" | "4" | "3" | "2" | "0";

export function getScoreTone(score: number): ScoreTone {
  if (score >= 5) return "5";
  if (score >= 4) return "4";
  if (score >= 3) return "3";
  if (score >= 2) return "2";
  return "0";
}

export function getScoreBadgeClass(score: number, variant: "score" | "product" = "score"): string {
  const tone = getScoreTone(score);
  if (tone === "5") return variant === "product" ? "product-badge--score-5" : "score-badge--5";
  if (tone === "4") return variant === "product" ? "product-badge--score-4" : "score-badge--4";
  if (tone === "3") return variant === "product" ? "product-badge--score-3" : "score-badge--3";
  if (tone === "2") return "product-badge--rising";
  return "";
}

export function getTierTone(product: Product): "darkhorse" | "rising" | "watch" {
  const score = product.dark_horse_index ?? 0;
  if (score >= 4) return "darkhorse";
  if (score >= 2) return "rising";
  return "watch";
}

export function isHardware(product: Product): boolean {
  if (product.is_hardware) return true;
  if (product.category === "hardware") return true;
  if (product.categories?.includes("hardware")) return true;
  return false;
}

export function tierOf(product: Product): "darkhorse" | "rising" | "other" {
  const index = product.dark_horse_index ?? 0;
  if (index >= 4) return "darkhorse";
  if (index >= 2) return "rising";
  return "other";
}

export function productDate(product: Product): number {
  const raw = product.first_seen || product.published_at || product.discovered_at;
  if (!raw) return 0;
  const ts = new Date(raw).getTime();
  return Number.isFinite(ts) ? ts : 0;
}

function getHeatScore(product: Product): number {
  const primary = Math.max(product.hot_score || 0, product.final_score || 0, product.trending_score || 0);
  const tierSignal = Math.max(0, product.dark_horse_index || 0) * 20;
  return Math.min(100, Math.max(primary, tierSignal));
}

function getFreshnessScore(product: Product, nowTs: number): number {
  const ts = productDate(product);
  if (!ts) return 0;
  const ageDays = Math.max(0, (nowTs - ts) / (1000 * 60 * 60 * 24));
  const decayLambda = Math.log(2) / FRESHNESS_HALF_LIFE_DAYS;
  return Math.min(100, Math.max(0, 100 * Math.exp(-decayLambda * ageDays)));
}

function getFundingBonusScore(product: Product): number {
  const funding = Math.max(0, parseFundingAmount(product.funding_total));
  return Math.min(100, Math.log10(1 + funding) * 35);
}

function getCompositeScore(product: Product, nowTs: number): number {
  return (
    COMPOSITE_HEAT_WEIGHT * getHeatScore(product)
    + COMPOSITE_FRESHNESS_WEIGHT * getFreshnessScore(product, nowTs)
    + COMPOSITE_FUNDING_WEIGHT * getFundingBonusScore(product)
  );
}

function normalizeCategoryTokenForLabel(value: string | undefined | null): string {
  const trimmed = String(value || "").trim();
  if (!trimmed) return "";

  const mapped = normalizeDirectionToken(trimmed);
  if (mapped) return mapped;
  return trimmed.toLowerCase().replace(/[_\s/-]+/g, "_");
}

function getCategoryLabel(category: string, locale: SiteLocale): string {
  const labels = locale === "en-US" ? DIRECTION_LABELS_EN : DIRECTION_LABELS_ZH;
  return labels[category] || category.replace(/_/g, " ");
}

export function formatCategories(product: Product, locale: SiteLocale = DEFAULT_LOCALE) {
  if (product.categories?.length) {
    const normalizedCategories = product.categories
      .map((category) => {
        const normalized = normalizeCategoryTokenForLabel(category);
        if (!normalized) return "";
        return normalized;
      })
      .filter(Boolean);

    const filteredCategories =
      normalizedCategories.length > 1 ? normalizedCategories.filter((category) => category !== "other") : normalizedCategories;

    const localized = filteredCategories.map((category) => getCategoryLabel(category, locale));

    if (localized.length) {
      return localized.join(" · ");
    }
  }
  if (product.category) {
    const normalized = normalizeCategoryTokenForLabel(product.category);
    if (normalized) return getCategoryLabel(normalized, locale);
    return product.category;
  }
  return pickLocaleText(locale, { zh: "精选 AI 工具", en: "Featured AI tools" });
}

export function normalizeDirectionToken(value: string | undefined | null): string {
  const normalized = String(value || "")
    .trim()
    .toLowerCase();
  if (!normalized) return "";
  if (/[;,]/.test(normalized)) return "";

  if (normalized.includes("voice") || normalized.includes("语音")) return "voice";
  if (normalized.includes("image") || normalized.includes("图像")) return "image";
  if (normalized.includes("video") || normalized.includes("视频")) return "video";
  if (normalized.includes("vision") || normalized.includes("视觉")) return "vision";
  if (normalized.includes("coding") || normalized.includes("开发") || normalized.includes("编程")) return "coding";
  if (normalized.includes("agent") || normalized.includes("智能体")) return "agent";
  if (normalized.includes("finance") || normalized.includes("金融")) return "finance";
  if (normalized.includes("health") || normalized.includes("医疗") || normalized.includes("健康")) return "healthcare";
  if (normalized.includes("education") || normalized.includes("教育")) return "education";
  if (normalized.includes("enterprise") || normalized.includes("企业")) return "enterprise";
  if (normalized.includes("productivity") || normalized.includes("效率") || normalized.includes("办公")) return "productivity";
  if (normalized.includes("chip") || normalized.includes("semiconductor") || normalized.includes("芯片")) return "ai_chip";
  if (normalized.includes("robot") || normalized.includes("机器人")) return "robotics";
  if (normalized.includes("driving") || normalized.includes("autonomous") || normalized.includes("驾驶")) return "driving";
  if (normalized.includes("wearable") || normalized.includes("可穿戴")) return "wearables";
  if (normalized.includes("smart_glasses") || normalized.includes("智能眼镜") || normalized.includes("glasses")) return "smart_glasses";
  if (normalized.includes("smart_home") || normalized.includes("智能家居")) return "smart_home";
  if (normalized.includes("edge") || normalized.includes("边缘")) return "edge_ai";
  if (normalized.includes("drone") || normalized.includes("无人机")) return "drone";
  if (normalized.includes("simulation") || normalized.includes("仿真")) return "simulation";
  if (normalized.includes("security") || normalized.includes("安全")) return "security";
  if (normalized.includes("infrastructure") || normalized.includes("基础设施")) return "infrastructure";
  if (normalized.includes("legal") || normalized.includes("法律")) return "legal";
  if (normalized.includes("脑机")) return "brain_computer_interface";
  if (normalized.includes("world model") || normalized.includes("world_model") || normalized.includes("世界模型")) return "world_model";

  const compacted = normalized.replace(/[_\s/-]+/g, "_");
  if ((compacted.match(/_/g)?.length || 0) >= 2 && !DIRECTION_LABELS_EN[compacted]) return "";
  if (compacted.length > 30 && !DIRECTION_LABELS_EN[compacted]) return "";
  return DIRECTION_IGNORED.has(compacted) ? "" : compacted;
}

export function getDirectionLabel(direction: string, locale: SiteLocale = DEFAULT_LOCALE): string {
  const normalized = normalizeDirectionToken(direction);
  if (!normalized) return "";
  const labels = locale === "en-US" ? DIRECTION_LABELS_EN : DIRECTION_LABELS_ZH;
  return labels[normalized] || normalized.replace(/_/g, " ");
}

export type DirectionOption = {
  value: string;
  label: string;
  count: number;
};

export function getProductDirections(product: Product): string[] {
  const extra = (product.extra ?? {}) as Record<string, unknown>;
  const candidates = [
    product.category,
    ...(product.categories || []),
    product.hardware_category,
    product.hardware_type,
    product.use_case,
    product.form_factor,
    ...(product.innovation_traits || []),
    String(extra.hardware_category || ""),
    String(extra.use_case || ""),
    String(extra.form_factor || ""),
  ];

  if (Array.isArray(extra.innovation_traits)) {
    for (const trait of extra.innovation_traits) {
      candidates.push(String(trait || ""));
    }
  }

  const deduped = new Set<string>();
  for (const candidate of candidates) {
    const direction = normalizeDirectionToken(candidate);
    if (!direction || DIRECTION_IGNORED.has(direction)) continue;
    deduped.add(direction);
  }

  return [...deduped];
}

export function collectDirectionOptions(products: Product[], locale: SiteLocale = DEFAULT_LOCALE): DirectionOption[] {
  const counts = new Map<string, number>();

  for (const product of products) {
    for (const direction of getProductDirections(product)) {
      counts.set(direction, (counts.get(direction) || 0) + 1);
    }
  }

  return [...counts.entries()]
    .map(([value, count]) => ({
      value,
      count,
      label: getDirectionLabel(value, locale) || value,
    }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, locale));
}

export function filterDirectionOptions(options: DirectionOption[], query: string): DirectionOption[] {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return options;

  return options.filter((option) => {
    const haystack = `${option.value} ${option.label}`.toLowerCase();
    return haystack.includes(normalized);
  });
}

export function cleanDescription(desc: string | undefined, locale: SiteLocale = DEFAULT_LOCALE) {
  if (!desc) {
    return pickLocaleText(locale, { zh: "暂无描述", en: "Description coming soon" });
  }
  return desc
    .replace(/<[^>]*>/g, " ")
    .replace(/&(?:amp|lt|gt|quot|apos|nbsp);/g, (entity) => ({ "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&apos;": "'", "&nbsp;": " " })[entity] || entity)
    .replace(/&#(x[\da-f]+|\d+);/gi, (entity, code: string) => {
      const point = code.toLowerCase().startsWith("x") ? parseInt(code.slice(1), 16) : Number(code);
      return point > 0 && point <= 0x10ffff ? String.fromCodePoint(point) : entity;
    })
    .replace(/\[\d+(?:\s*[,，-]\s*\d+)*\]/g, "")
    .replace(/Hugging Face (模型|model|space): [^|]+[|]/gi, "")
    .replace(/[|] ⭐ [\d.]+K?\+? Stars/g, "")
    .replace(/[|] (技术|tech): .+$/gi, "")
    .replace(/[|] (下载量|downloads?): .+$/gi, "")
    .replace(/^\s*[|·]\s*/g, "")
    .replace(/[ \t]{2,}/g, " ")
    .trim();
}

export function getLocalizedProductDescription(product: Product, locale: SiteLocale = DEFAULT_LOCALE): string {
  const picked = pickLocalizedText(product, "description", locale);
  return picked ? cleanDescription(picked, locale) : "";
}

export function getLocalizedProductWhyMatters(product: Product, locale: SiteLocale = DEFAULT_LOCALE): string {
  return pickLocalizedText(product, "why_matters", locale);
}

export function getLocalizedProductLatestNews(product: Product, locale: SiteLocale = DEFAULT_LOCALE): string {
  return pickLocalizedText(product, "latest_news", locale);
}

function pickLocalizedBlogText(
  zhValue: string | undefined | null,
  enValue: string | undefined | null,
  locale: SiteLocale
): string {
  const zh = isPlaceholderValue(_normalizeText(zhValue)) ? "" : _normalizeText(zhValue);
  const en = isPlaceholderValue(_normalizeText(enValue)) ? "" : _normalizeText(enValue);
  if (locale === "en-US") {
    return en || zh;
  }
  return zh || en;
}

function _normalizeText(value: string | undefined | null): string {
  return String(value || "").trim();
}

export function getLocalizedBlogName(
  blog: { name?: string; name_en?: string },
  locale: SiteLocale = DEFAULT_LOCALE
): string {
  return pickLocalizedBlogText(blog.name, blog.name_en, locale);
}

export function getLocalizedBlogDescription(
  blog: { description?: string; description_en?: string },
  locale: SiteLocale = DEFAULT_LOCALE
): string {
  const text = pickLocalizedBlogText(blog.description, blog.description_en, locale);
  return text ? cleanDescription(text, locale) : "";
}

export function getMonogram(name: string | undefined): string {
  if (!name) return "AI";
  const trimmed = name.trim();
  if (!trimmed) return "AI";

  const chars = [...trimmed];
  const firstHan = chars.find((char) => /\p{Script=Han}/u.test(char));
  if (firstHan) return firstHan;

  const firstAlphaNum = chars.find((char) => /[A-Za-z0-9]/.test(char));
  if (firstAlphaNum) return firstAlphaNum.toUpperCase();

  return chars[0]?.toUpperCase() || "AI";
}

export type ProductCountryInfo = {
  code: string;
  name: string;
  flag: string;
  display: string;
  source: string;
  unknown: boolean;
};

function getCountryNameFromCode(code: string, locale: SiteLocale): string {
  if (!code || code === UNKNOWN_COUNTRY_CODE) {
    return pickLocaleText(locale, { zh: "地区待补充", en: UNKNOWN_COUNTRY_NAME });
  }

  if (locale === "en-US") {
    return COUNTRY_CODE_TO_NAME[code] || code;
  }

  return COUNTRY_CODE_TO_NAME_ZH[code] || COUNTRY_CODE_TO_NAME[code] || code;
}

function normalizeCountryCode(value: unknown): string {
  const text = String(value || "").trim();
  if (!text) return "";

  const upper = text.toUpperCase();
  if (COUNTRY_CODE_TO_NAME[upper]) return upper;

  const flag = extractRegionFlag(text);
  if (flag && FLAG_TO_COUNTRY_CODE[flag]) return FLAG_TO_COUNTRY_CODE[flag];

  const normalized = text
    .toLowerCase()
    .replace(/[_\-.]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return COUNTRY_NAME_ALIASES[normalized] || "";
}

function extractRegionFlag(value: unknown): string {
  const text = String(value || "").trim();
  if (!text) return "";
  const match = text.match(REGION_FLAG_RE);
  return match?.[0] || "";
}

function countryCodeFromWebsiteTld(website: string | undefined | null): string {
  const normalized = normalizeWebsite(website);
  if (!normalized) return "";
  try {
    const host = new URL(normalized).hostname.toLowerCase().replace(/^www\./, "");
    if (!host.includes(".")) return "";
    const parts = host.split(".");
    const suffix = parts[parts.length - 1] || "";
    return COUNTRY_BY_CC_TLD[suffix] || "";
  } catch {
    return "";
  }
}

export function resolveProductCountry(product: Product): ProductCountryInfo {
  const raw = product as Product & Record<string, unknown>;
  const extra = (product.extra ?? {}) as Record<string, unknown>;
  const countrySourceHint = String(raw.country_source || "").trim().toLowerCase();
  const skipRegionDerivedCountryFields = REGION_DERIVED_COUNTRY_SOURCES.has(countrySourceHint);
  const explicitFields = [
    raw.company_country_code,
    raw.hq_country_code,
    raw.company_country,
    raw.hq_country,
    raw.headquarters_country,
    raw.origin_country,
    raw.founder_country,
    ...(skipRegionDerivedCountryFields ? [] : [raw.country_code, raw.country_name, raw.country]),
    extra.company_country_code,
    extra.company_country,
    extra.hq_country,
    extra.headquarters_country,
    extra.origin_country,
    extra.founder_country,
    ...(skipRegionDerivedCountryFields ? [] : [extra.country_code, extra.country_name, extra.country]),
  ];

  for (const candidate of explicitFields) {
    const code = normalizeCountryCode(candidate);
    if (code) {
      const name = COUNTRY_CODE_TO_NAME[code] || code;
      const flag = COUNTRY_CODE_TO_FLAG[code] || "";
      return {
        code,
        name,
        flag,
        display: flag ? `${flag} ${name}` : name,
        source: String(raw.country_source || "explicit"),
        unknown: false,
      };
    }
  }

  const explicitFlagFields = skipRegionDerivedCountryFields
    ? [raw.company_country_flag, raw.hq_country_flag]
    : [raw.country_flag, raw.company_country_flag, raw.hq_country_flag];
  for (const candidate of explicitFlagFields) {
    const code = normalizeCountryCode(candidate);
    if (code) {
      const name = COUNTRY_CODE_TO_NAME[code] || code;
      const flag = COUNTRY_CODE_TO_FLAG[code] || "";
      return {
        code,
        name,
        flag,
        display: flag ? `${flag} ${name}` : name,
        source: String(raw.country_source || "explicit:flag"),
        unknown: false,
      };
    }
  }

  const source = String(raw.source || "").trim().toLowerCase();
  const regionFlag = extractRegionFlag(product.region);
  if (source === "curated" && regionFlag && FLAG_TO_COUNTRY_CODE[regionFlag]) {
    const code = FLAG_TO_COUNTRY_CODE[regionFlag];
    const name = COUNTRY_CODE_TO_NAME[code] || code;
    return {
      code,
      name,
      flag: COUNTRY_CODE_TO_FLAG[code] || "",
      display: `${COUNTRY_CODE_TO_FLAG[code] || ""} ${name}`.trim(),
      source: "curated:region",
      unknown: false,
    };
  }

  if (regionFlag && !DISCOVERY_REGION_FLAGS.has(regionFlag) && FLAG_TO_COUNTRY_CODE[regionFlag]) {
    const code = FLAG_TO_COUNTRY_CODE[regionFlag];
    const name = COUNTRY_CODE_TO_NAME[code] || code;
    return {
      code,
      name,
      flag: COUNTRY_CODE_TO_FLAG[code] || "",
      display: `${COUNTRY_CODE_TO_FLAG[code] || ""} ${name}`.trim(),
      source: "region:legacy",
      unknown: false,
    };
  }

  const tldCode = countryCodeFromWebsiteTld(product.website);
  if (tldCode) {
    const name = COUNTRY_CODE_TO_NAME[tldCode] || tldCode;
    return {
      code: tldCode,
      name,
      flag: COUNTRY_CODE_TO_FLAG[tldCode] || "",
      display: `${COUNTRY_CODE_TO_FLAG[tldCode] || ""} ${name}`.trim(),
      source: "website:cc_tld",
      unknown: false,
    };
  }

  return {
    code: UNKNOWN_COUNTRY_CODE,
    name: UNKNOWN_COUNTRY_NAME,
    flag: "",
    display: UNKNOWN_COUNTRY_NAME,
    source: "unknown",
    unknown: true,
  };
}

export function getLocalizedCountryName(country: ProductCountryInfo, locale: SiteLocale): string {
  if (country.unknown) {
    return pickLocaleText(locale, { zh: "地区待补充", en: UNKNOWN_COUNTRY_NAME });
  }

  return getCountryNameFromCode(country.code, locale);
}

export function getFreshnessLabel(
  product: Product,
  now: Date = new Date(),
  locale: SiteLocale = DEFAULT_LOCALE
): string {
  const raw = product.discovered_at || product.first_seen || product.published_at;
  return formatRelativeDate(raw, locale, now);
}

export function formatRelativeDate(
  value: string | Date | number | undefined | null,
  locale: SiteLocale = DEFAULT_LOCALE,
  now: Date = new Date()
): string {
  if (!value) {
    return pickLocaleText(locale, { zh: "时间待补充", en: "Timestamp unavailable" });
  }

  const date = value instanceof Date ? value : new Date(value);
  if (!Number.isFinite(date.getTime())) {
    return pickLocaleText(locale, { zh: "时间待补充", en: "Timestamp unavailable" });
  }

  const diffMs = now.getTime() - date.getTime();
  if (diffMs <= 0) {
    return pickLocaleText(locale, { zh: "刚更新", en: "Just updated" });
  }

  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 60) {
    return pickLocaleText(locale, { zh: "1小时内", en: "Within 1h" });
  }

  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return locale === "en-US" ? `${hours}h ago` : `${hours}小时前`;
  }

  const days = Math.floor(hours / 24);
  if (days < 7) {
    return locale === "en-US" ? `${days}d ago` : `${days}天前`;
  }

  const weeks = Math.floor(days / 7);
  if (weeks < 5) {
    return locale === "en-US" ? `${weeks}w ago` : `${weeks}周前`;
  }

  const months = Math.floor(days / 30);
  if (months < 12) {
    return locale === "en-US" ? `${months}mo ago` : `${months}个月前`;
  }

  const years = Math.floor(days / 365);
  return locale === "en-US" ? `${years}y ago` : `${years}年前`;
}

export function formatAbsoluteDate(
  value: string | Date | number | undefined | null,
  locale: SiteLocale = DEFAULT_LOCALE,
  opts: { includeTime?: boolean } = {}
): string {
  if (!value) return "";
  const date = value instanceof Date ? value : new Date(value);
  if (!Number.isFinite(date.getTime())) return "";

  return new Intl.DateTimeFormat(locale, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    ...(opts.includeTime ? { hour: "2-digit", minute: "2-digit" } : {}),
  }).format(date);
}

export function productKey(product: Product): string {
  const website = normalizeWebsite(product.website);
  return `${website}::${(product.name || "").toLowerCase()}`;
}

export type ProductSortMode = "composite" | "trending" | "recency" | "funding" | "score" | "date";

function resolveSortMode(sortBy: ProductSortMode): "composite" | "trending" | "recency" | "funding" {
  if (sortBy === "score") return "trending";
  if (sortBy === "date") return "recency";
  return sortBy;
}

export function sortProducts(products: Product[], sortBy: ProductSortMode): Product[] {
  const copied = [...products];
  const mode = resolveSortMode(sortBy);
  const nowTs = Date.now();

  if (mode === "recency") {
    return copied.sort((a, b) => productDate(b) - productDate(a) || getHeatScore(b) - getHeatScore(a));
  }

  if (mode === "funding") {
    return copied.sort((a, b) => parseFundingAmount(b.funding_total) - parseFundingAmount(a.funding_total));
  }

  if (mode === "trending") {
    return copied.sort((a, b) => getHeatScore(b) - getHeatScore(a) || productDate(b) - productDate(a));
  }

  return copied.sort((a, b) => getCompositeScore(b, nowTs) - getCompositeScore(a, nowTs));
}

export function filterProducts(
  products: Product[],
  opts: {
    tier: "all" | "darkhorse" | "rising";
    type: "all" | "software" | "hardware";
  }
): Product[] {
  return products.filter((product) => {
    if (opts.tier !== "all" && tierOf(product) !== opts.tier) return false;

    if (opts.type === "hardware" && !isHardware(product)) return false;
    if (opts.type === "software" && isHardware(product)) return false;

    return true;
  });
}
