import type { Product } from "@/types/api";

const INVALID_WEBSITE_VALUES = new Set(["unknown", "n/a", "na", "none", "null", "undefined", ""]);
const PLACEHOLDER_VALUES = new Set(["unknown", "n/a", "na", "none", "tbd", "暂无", "未公开", "待定", "unknown.", "n/a."]);
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
]);

const DIRECTION_LABELS: Record<string, string> = {
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

export function getLogoFallbacks(website: string | undefined | null, sourceUrl?: string | undefined | null): string[] {
  const primary = normalizeWebsite(website);
  const fallbackSource = normalizeWebsite(sourceUrl);
  const candidate = isValidWebsite(primary) ? primary : isValidWebsite(fallbackSource) ? fallbackSource : "";
  if (!candidate) return [];

  try {
    const host = new URL(candidate).hostname.replace(/^www\./, "");
    if (!host) return [];
    return [
      `https://logo.clearbit.com/${host}`,
      `https://www.google.com/s2/favicons?domain=${host}&sz=128`,
      `https://favicon.bing.com/favicon.ico?url=${host}&size=128`,
      `https://icons.duckduckgo.com/ip3/${host}.ico`,
      `https://icon.horse/icon/${host}`,
    ];
  } catch {
    return [];
  }
}

type LogoCandidatesInput = {
  logoUrl?: string | null;
  website?: string | null;
  sourceUrl?: string | null;
};

export function getLogoCandidates(input: LogoCandidatesInput): string[] {
  const result: string[] = [];
  const seen = new Set<string>();

  const pushIfValid = (value: string | undefined | null) => {
    const normalized = normalizeLogoSource(value);
    if (!isValidLogoSource(normalized)) return;
    if (seen.has(normalized)) return;
    seen.add(normalized);
    result.push(normalized);
  };

  pushIfValid(input.logoUrl);
  const fallbacks = getLogoFallbacks(input.website, input.sourceUrl);
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

export function formatCategories(product: Product) {
  if (product.categories?.length) return product.categories.join(" · ");
  if (product.category) return product.category;
  return "精选 AI 工具";
}

export function normalizeDirectionToken(value: string | undefined | null): string {
  const normalized = String(value || "")
    .trim()
    .toLowerCase();
  if (!normalized) return "";

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
  return DIRECTION_IGNORED.has(compacted) ? "" : compacted;
}

export function getDirectionLabel(direction: string): string {
  const normalized = normalizeDirectionToken(direction);
  if (!normalized) return "";
  return DIRECTION_LABELS[normalized] || normalized.replace(/_/g, " ");
}

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

export function cleanDescription(desc: string | undefined) {
  if (!desc) return "暂无描述";
  return desc
    .replace(/Hugging Face (模型|Space): [^|]+[|]/g, "")
    .replace(/[|] ⭐ [\d.]+K?\+? Stars/g, "")
    .replace(/[|] 技术: .+$/g, "")
    .replace(/[|] 下载量: .+$/g, "")
    .replace(/^\s*[|·]\s*/g, "")
    .trim();
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

export function getFreshnessLabel(product: Product, now: Date = new Date()): string {
  const raw = product.discovered_at || product.first_seen || product.published_at;
  if (!raw) return "时间待补充";

  const date = new Date(raw);
  if (!Number.isFinite(date.getTime())) return "时间待补充";

  const diffMs = now.getTime() - date.getTime();
  if (diffMs <= 0) return "刚更新";

  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 60) return "1小时内";

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}小时前`;

  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}天前`;

  const months = Math.floor(days / 30);
  if (months < 12) return `${months}个月前`;

  const years = Math.floor(days / 365);
  return `${years}年前`;
}

export function productKey(product: Product): string {
  const website = normalizeWebsite(product.website);
  return `${website}::${(product.name || "").toLowerCase()}`;
}

export function sortProducts(
  products: Product[],
  sortBy: "score" | "date" | "funding"
): Product[] {
  const copied = [...products];
  if (sortBy === "date") {
    return copied.sort((a, b) => productDate(b) - productDate(a));
  }
  if (sortBy === "funding") {
    return copied.sort((a, b) => parseFundingAmount(b.funding_total) - parseFundingAmount(a.funding_total));
  }
  return copied.sort((a, b) => getProductScore(b) - getProductScore(a));
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
