import type { Product } from "@/types/api";
import { DEFAULT_LOCALE, pickLocaleText, type SiteLocale } from "@/lib/locale";

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
  agent: "Agent",
  coding: "编程开发",
  image: "图像",
  video: "视频",
  vision: "视觉",
  voice: "语音",
  writing: "写作",
  finance: "金融",
  education: "教育",
  healthcare: "医疗健康",
  enterprise: "企业服务",
  productivity: "效率",
  ai_chip: "AI芯片",
  robotics: "机器人",
  driving: "自动驾驶",
  wearables: "可穿戴",
  smart_glasses: "智能眼镜",
  smart_home: "智能家居",
  edge_ai: "边缘AI",
  drone: "无人机",
  simulation: "仿真",
  security: "AI安全",
  infrastructure: "基础设施",
  legal: "法律",
  brain_computer_interface: "脑机接口",
  world_model: "世界模型",
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
  "sakana ai": {
    description: "日本出身的 foundation model 公司，以受自然启发的 AI 方法推进基础模型与 AI Scientist 等研究。",
    why_matters:
      "由 Transformer 作者 Llion Jones 和 Google Brain 东京前负责人 David Ha 创立；Series A 融资 $200M，后续再增资 $135M，总融资达 $479M。拿到 MUFG、SMBC、富士通、KDDI 等日本产业资本支持，以 biologically inspired AI 和 AI Scientist 切入 Japan-led Sovereign AI 布局。",
  },
  "skildai": {
    description: "机器人 foundation model 初创公司，专注为 physical robots 提供通用 embodied AI 能力。",
    why_matters:
      "2026 年 1 月完成 $1.4B Series C，是 2026 年初最大级别的机器人 AI 融资之一，说明资本正在集中押注 embodied AI 基础层。",
  },
  "frankenburg technologies": {
    description: "爱沙尼亚塔林 AI 初创公司，2024 年成立，两年内总融资达到 €43M。",
    why_matters:
      "最新 €30M Series A 后总融资增至 €43M，由 SmartCap 和 Plural 领投，属于 2026 年中东欧最受关注的 AI 融资案例之一。",
  },
  "ai2 robotics": {
    description: "中国具身智能机器人公司，围绕人形机器人推出 GOVLA 等 embodied AI 模型与系统。",
    why_matters:
      "Series B 融资超 10 亿元，估值突破 100 亿元，获百度与 CRRC Capital 等机构支持，用于强化人形机器人“头脑”与量产能力。",
  },
  "vertical compute": {
    description: "比利时 AI 芯片初创公司，研发面向 AI memory bottleneck 的新型 memory component 与 chiplet 方案。",
    why_matters:
      "从 imec 分拆一年内完成首颗 3D memory-logic test chip tape-out，累计融资 €57M（含新增 €37M），目标是在不替换 CPU/GPU 的前提下提升 AI 内存效率。",
  },
  "abridge": {
    description: "医疗 AI 平台，帮助医院和医生把临床对话转成结构化记录与工作流。",
    why_matters:
      "2025 年两轮融资累计 $550M，估值升至 $5.3B，说明 healthcare AI 已从工具尝试走向系统级预算投入。",
  },
  "anysphere (cursor)": {
    description: "由 AI 驱动的 coding platform，凭借 Cursor 在开发者群体中快速病毒式传播。",
    why_matters:
      "2025 年 6 月与 11 月连续完成大额融资，11 月融资后估值达 $29.3B，5 个月内估值从 $10B 跳升至近三倍，成为 AI coding 赛道最强商业信号之一。",
  },
  "cerebras wse-3": {
    description: "wafer-scale AI inference chip，集成 4 trillion transistors 和 44GB on-chip SRAM，以水冷 CS-3 system 形态交付。",
    why_matters:
      "目前已知最大的 AI chip，晶体管数量约为 Nvidia B200 的 19 倍，并为 OpenAI 的高速 inference 提供算力支撑。",
  },
  "google x gentle monster android xr glasses": {
    description: "结合 Gentle Monster 时尚镜框、Android XR 与 Gemini 的 AI smart glasses，主打高颜值与 contextual assistance。",
    why_matters:
      "Google 向 Gentle Monster 投资 $100M，希望以 fashion-first 路线重启 smart glasses，避免 Google Glass 时代的审美阻力。",
  },
  "google x warby parker android xr glasses": {
    description: "面向日常佩戴场景的 AI smart glasses，支持矫正镜片、Android XR 与 Gemini 的 hands-free contextual help。",
    why_matters:
      "Google 最多投入 $150M，与 Warby Parker 的 DTC 眼镜渠道结合，目标是把 AI glasses 推向更主流的 everyday eyewear 市场。",
  },
  "harvey": {
    description: "面向律师事务所和法务团队的 legal AI platform，用于合同审阅、检索和文档分析。",
    why_matters:
      "以 $3B 估值完成 $300M Series D，代表 legal AI 已从试点工具进入行业级采购阶段。",
  },
  "hippocratic ai": {
    description: "专注医疗场景的 healthcare AI 公司。",
    why_matters:
      "2025 年两轮融资累计 $267M，最新 Series C 为 $126M、估值 $3.5B，说明临床与患者服务型 AI 正获得持续资本验证。",
  },
  "robco modular ai robots": {
    description: "模块化 AI robotic arms，用于工业自动化，结合 physical AI、示教学习和 digital twins。",
    why_matters:
      "面向中小制造企业的 robotics platform，模块化硬件降低部署门槛；已融资 $100M 扩张美国市场，客户包括 BMW。",
  },
  "sandboxaq": {
    description: "聚焦 quantum-safe cryptography 和 AI security 的技术公司。",
    why_matters:
      "2025 年 4 月完成 $450M Series E，估值 $5.7B，显示 AI 安全与后量子密码学正成为长期基础设施议题。",
  },
  "cudis ai health ring": {
    description: "AI smart ring，结合 agent coach、健康指标追踪与 gamified rewards，且无需订阅费。",
    why_matters:
      "把 smart ring、AI coach 和积分激励结合起来，区别于传统 wearable；已售出 3 万+ 台，在北美、欧洲和亚洲市场都有验证。",
  },
  "floglasses": {
    description: "主打 real-time translation 的 wearable AI glasses。",
    why_matters:
      "聚焦翻译单一场景，降低了 AI glasses 的功能复杂度和价格门槛，支持试用购买，产品定位清晰。",
  },
  "kewazo": {
    description: "用 robotics 与 data analytics digitize construction workflow 的建筑科技公司。",
    why_matters:
      "围绕 AI-powered construction robotics 累计融资 $144M，说明建筑自动化开始从 demo 走向可规模化部署。",
  },
  "mentra live": {
    description: "开源 AI smart glasses，配备 HD camera、MiniApp Store 与直播能力，并支持笔记、翻译等 AI 功能，重量 43g，续航 12 小时以上。",
    why_matters:
      "通过 open-source OS 和 app store 打开开发者生态，让 AI glasses 不再是封闭硬件，而是可以持续演化的 wearable platform。",
  },
  neo1: {
    description: "印度 AI-native pendant，可持续听取对话、分析情绪、总结讨论，在无屏状态下充当 second brain。",
    why_matters:
      "用 screenless pendant 形态切入 conversation memory 与 emotion analysis，价格约 $144 且含 unlimited subscription，在 India AI Summit 获得较高曝光。",
  },
  "project motoko": {
    description: "AI-native 无线头显概念产品，尝试把 gaming、lifestyle 与 productivity 融到同一 wearable 形态。",
    why_matters:
      "在 CES 2026 以 AI-native headset 概念切入，展示出 wearable 设备不再局限于 glasses 或 pendant 的产品方向。",
  },
  ivee: {
    description: "面向企业员工的 AI upskilling 平台，通过动态测评和实战训练帮助团队掌握 AI tools。",
    why_matters:
      "完成 $1M seed，投资方包括 Steven Bartlett 与 Social Impact Enterprises，并被选为英国政府重点活动合作方，说明企业级 AI 培训开始从课程走向可验证的 skill infrastructure。",
  },
  friend: {
    description: "AI wearable pendant，提供实时陪伴式对话与情绪支持，采用一次性购买、无订阅模式。",
  },
  "dreame pilot 20": {
    description: "全球首款双机械臂 AI smart hair dryer，可分析发质并自动匹配吹护动作。",
    why_matters:
      "把日常家电、AI 与 robotic arms 融合成新的消费硬件形态，体现“自动护理”方向的产品创新。",
  },
  godot: {
    description: "日本行为科学 AI 创业公司，提供可信的 AI platform，帮助个人、组织和社会做行为改变。",
    why_matters:
      "在 Dawn Capital 领投的 Series A 后累计融资 11 亿日元，已把业务从神户扩展到澳大利亚与维也纳，并在大阪大肠癌筛查项目中取得 46% 提升，还获得 WHO 奖项。",
  },
  "neureality": {
    description: "以 NAPU 与 software stack 组合打造 AI inference semiconductor solution，提升 cloud 与 edge AI 效率。",
    why_matters:
      "累计融资 $59.65M，并获得 SK Hynix、Samsung Ventures 支持；通过 AI infrastructure as a service 思路，用更低成本解决 AI 扩容问题。",
  },
  "rokid スマートaiグラス": {
    description: "49g 轻量 AI smart glasses，集成 Micro LED、12MP camera、GPT-5/Gemini 视觉理解、89 语翻译与 AR 导航。",
    why_matters:
      "在接近普通眼镜的重量下塞进完整 AI 能力，并已在日本 Makuake 开启预售，属于高关注度的 consumer AR glasses。",
  },
  "new aiスマートレンズ": {
    description: "38g 超轻 smart glasses，集成 8MP camera、22 语实时翻译、AI voice assistant 与 Bluetooth speaker。",
    why_matters:
      "以太阳镜形态把 camera、translation 与 AI assistant 合到一起，更强调户外和日常场景，是“轻量多功能 wearable”的典型方向。",
  },
  seeqc: {
    description: "基于 single flux quantum (SFQ) chip 的量子计算硬件方案，强调能效与系统级可扩展性。",
    why_matters:
      "2025 年 1 月完成 $30M Series A，用芯片级实现方式切入 quantum computing 的 scalability 与 power efficiency 问题。",
  },
  "turing inc.": {
    description: "日本自动驾驶公司，开发 E2E driving AI、专用算力集群 Gaggle Cluster，以及生成式 world model Terra。",
    why_matters:
      "已在东京市区实现超过 30 分钟无人工接管自动驾驶，同时推进 Heron 多模态模型与 CoVLA Dataset，体现 Japanese players 在 physical AI / autonomous driving 上的系统能力。",
  },
  "exawizards(エクサウィザーズ)": {
    description: "生成式 AI 平台公司，提供 enterprise 级 GenAI 服务与 AI agents，正从 DX 咨询转向订阅式产品业务。",
    why_matters:
      "2026 财年营业利润预计同比增长约 59 倍，exaBase GenAI 与 AI agents 正推动其从项目制转向 subscription 模式。",
  },
  mujinos: {
    description: "工业机器人操作系统，能够为产线机器人自动生成动作并统一调度多台设备协同执行。",
    why_matters:
      "它把 digital twin、路径规划和真实执行打通成一套 industrial OS，切中复杂物流与制造场景的自动化瓶颈，不只是卖单点机器人。",
  },
  basis: {
    description: "面向会计师事务所和财务团队的 AI agent 平台，用来处理审计、台账和日常会计工作流。",
    why_matters:
      "由 Accel 领投完成 $100M Series B，估值达到 $1.15B，说明 accounting AI 已从效率工具进入垂直行业平台阶段。",
  },
  "xross road": {
    description: "AI 漫画生成工具，通过 HANASEE 把小说或脚本转成长篇漫画，并尽量保持角色设定一致。",
    why_matters:
      "在 pre-seed 获得 $1.5M 融资，用 AI 切入漫画自动生成这一高门槛创作环节，具备重塑内容工业化流程的潜力。",
  },
  modveon: {
    description: "围绕本人性验证构建 identity-first trust OS，为政务和线上协作提供可信交互基础设施。",
    why_matters:
      "获 Coinbase Ventures 参投的 $10M 融资，核心不是单点身份验证，而是把 verified interactions 做成社会级信任底座。",
  },
  "genas.ai": {
    description: "面向日本市场的 AI 视频生成平台，整合 Sora、Veo 和 Seedance 等新模型，用于广告与短剧内容量产。",
    why_matters:
      "在 2026 年初下调接入门槛并快速补齐 AI 试穿、lip sync 等能力，产品方向很明确，就是把生成式视频工作流产品化。",
  },
  "ニュウジア": {
    description: "面向日本市场的 AI 解决方案公司，覆盖 AI digital human、AI 试衣和 agentic AI 等多个商业场景。",
    why_matters:
      "连续推出多条产品线，从 AI 试衣到沉浸式空间和智能 badge，说明它在以“多场景快速产品化”方式抢占企业 AI 落地窗口。",
  },
  "shizuku ai": {
    description: "日本 AI VTuber 服务，基于 StreamDiffusion 等高速生成技术实现更实时的互动与视觉反馈。",
    why_matters:
      "拿到 a16z 投资后，正在把实时生成能力带入 VTuber 形态，卡位的是虚拟角色实时交互而不是传统内容生产。",
  },
  tiergeo: {
    description: "聚焦 LLMO / AIO 暴露面治理的工具平台，帮助企业理解内容在 AI 搜索与推荐系统中的可见性。",
    why_matters:
      "2026 年初客户数突破 1.4 万，并通过并购继续加固能力，说明围绕 AI 可见性与信任的新一代 security / optimization 工具正在成形。",
  },
  helpfeel: {
    description: "AI 知识数据平台，为客服 FAQ、VoC 分析和生成式 AI 提供更准确的结构化知识底座。",
    why_matters:
      "Series E 第二次 close 后累计融资约 29 亿日元，已服务 800+ 站点，核心价值在于解决 GenAI 上线后的知识准确性问题。",
  },
  "appier group": {
    description: "以 AI 驱动销售与营销 SaaS 的亚洲头部公司，覆盖获客、转化和客户价值提升等环节。",
    why_matters:
      "作为日本收入规模领先的 AI 企业之一，它证明了“预测 AI + 营销自动化”在亚洲企业市场已经跑出长期商业模型。",
  },
  nao: {
    description: "小型 humanoid robot，支持多语言语音识别和丰富肢体动作，可用于接待、教育与陪护场景。",
    why_matters:
      "它不是追求极限智能的实验室产品，而是把 humanoid 形态做成可落地的互动终端，适合线下服务空间。",
  },
  "switchbot onero h1": {
    description: "面向家庭场景的 humanoid robot，主打收衣、端盘等家务任务学习与执行。",
    why_matters:
      "在 CES 2026 亮相后，它代表的是“家务专用 humanoid”这一更窄但更可能先落地的机器人路线。",
  },
  "linse lite": {
    description: "轻量音频眼镜，主打开放式扬声器与麦克风通话体验，并支持度数镜片。",
    why_matters:
      "相比全功能 AI glasses，它选择更克制的 audio-first 路线，用更轻形态切入日常佩戴市场。",
  },
  "upscale ai": {
    description: "AI infrastructure 初创公司，围绕训练与推理底层能力提供更强的算力与系统支持。",
    why_matters:
      "在 seed 轮就拿到 $100M，且由半导体与基础设施导向基金联合领投，说明市场正在提前押注下一代 AI infra 供给。",
  },
  "j-style smart rings": {
    description: "无屏 AI 智能戒指，强调连续健康监测、ECG 和 AI 驱动的预测式 wellness 提示。",
    why_matters:
      "把无创风险评估、心电与 AI 预测结合到 screenless ring 形态里，产品定位比通用穿戴更聚焦健康预防。",
  },
  "snorkel ai": {
    description: "AI 数据开发与标注平台，帮助团队构建训练数据、评测流程和更可控的模型工作流。",
    why_matters:
      "以 $1.3B 估值完成 $100M Series D，说明数据层工具在生成式 AI 周期里仍然是基础设施级赛道。",
  },
  valkaai: {
    description: "来自布拉格的实时交互式 AI avatar 与视频技术公司，服务体育和媒体场景。",
    why_matters:
      "完成 €12M pre-seed，是当地极少见的大额早期 AI 融资，押注的是实时 avatar 而不是传统预生成视频。",
  },
  "vitrealab quantum light chips": {
    description: "研发 quantum light chips 的 photonics 公司，面向更紧凑的 AR 显示与下一代视觉计算设备。",
    why_matters:
      "它关注的不是软件层体验，而是 AR 显示的底层光学器件，一旦成熟会直接影响 AI wearable 的形态上限。",
  },
  "positron asimov": {
    description: "下一代 AI inference custom silicon，单芯片内存超过 2TB，目标是缓解长上下文和视频模型的 memory bottleneck。",
    why_matters:
      "它从 memory-per-chip 这个更底层的指标切入推理瓶颈，瞄准的是视频、量化交易和长上下文模型的高带宽场景。",
  },
  foodforecast: {
    description: "来自科隆的 AI FoodTech 公司，为零售与食品生产企业做需求预测和产能规划。",
    why_matters:
      "完成 €8M Series A，说明 AI 在食品供应链里的价值点已经从分析报表转向直接影响损耗与产能配置。",
  },
  lmarena: {
    description: "由 UC Berkeley 推动的 LLM evaluation 与 benchmarking 平台。",
    why_matters:
      "由 UC Berkeley 孵化，4 个月内估值升至 $1.7B，Felicis 领投，已经成为 LLM 评测标准基础设施的重要节点。",
  },
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

  return [
    ...directIcons,
    `https://logo.clearbit.com/${host}`,
  ];
}

type LogoCandidatesInput = {
  logoUrl?: string | null;
  secondaryLogoUrl?: string | null;
  website?: string | null;
  sourceUrl?: string | null;
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
  const deferredProviderLogos: string[] = [];
  const websiteHost = resolveLogoHost(input.website);

  const pushIfValid = (value: string | undefined | null, opts?: { deferLowPriority?: boolean }) => {
    const normalized = normalizeLogoSource(value);
    if (!isValidLogoSource(normalized)) return;
    if (isGeneratedFaviconProviderLogo(normalized)) return;
    if (!isTrustedLogoSource(normalized, websiteHost)) return;
    if (seen.has(normalized)) return;
    if (opts?.deferLowPriority && isLowPriorityProviderLogo(normalized)) {
      deferredProviderLogos.push(normalized);
      return;
    }
    seen.add(normalized);
    result.push(normalized);
  };

  pushIfValid(input.logoUrl, { deferLowPriority: true });
  pushIfValid(input.secondaryLogoUrl, { deferLowPriority: true });
  const fallbacks = getLogoFallbacks(input.website);
  for (const fallback of fallbacks) {
    pushIfValid(fallback, { deferLowPriority: true });
  }
  for (const candidate of deferredProviderLogos) {
    pushIfValid(candidate);
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
  if (!value) return 0;
  const normalized = value.replace(/,/g, "").trim().toLowerCase();
  const match = normalized.match(/([\d.]+)\s*(b|m|k|亿|万)?/);
  if (!match) return 0;

  const amount = Number(match[1]);
  if (!Number.isFinite(amount)) return 0;

  const unit = match[2];
  if (unit === "b") return amount * 1000;
  if (unit === "m") return amount;
  if (unit === "k") return amount / 1000;
  if (unit === "亿") return amount * 100;
  if (unit === "万") return amount / 100;

  return amount;
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
  if (normalized.includes("image")) return "image";
  if (normalized.includes("video")) return "video";
  if (normalized.includes("vision") || normalized.includes("视觉")) return "vision";
  if (normalized.includes("coding") || normalized.includes("开发") || normalized.includes("编程")) return "coding";
  if (normalized.includes("agent")) return "agent";
  if (normalized.includes("finance") || normalized.includes("金融")) return "finance";
  if (normalized.includes("health") || normalized.includes("医疗") || normalized.includes("健康")) return "healthcare";
  if (normalized.includes("education") || normalized.includes("教育")) return "education";
  if (normalized.includes("enterprise") || normalized.includes("企业")) return "enterprise";
  if (normalized.includes("productivity") || normalized.includes("效率") || normalized.includes("办公")) return "productivity";
  if (normalized.includes("chip") || normalized.includes("semiconductor") || normalized.includes("芯片")) return "ai_chip";
  if (normalized.includes("robot")) return "robotics";
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
    .replace(/Hugging Face (模型|model|space): [^|]+[|]/gi, "")
    .replace(/[|] ⭐ [\d.]+K?\+? Stars/g, "")
    .replace(/[|] (技术|tech): .+$/gi, "")
    .replace(/[|] (下载量|downloads?): .+$/gi, "")
    .replace(/^\s*[|·]\s*/g, "")
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
