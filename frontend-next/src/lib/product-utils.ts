import type { Product } from "@/types/api";
import { DEFAULT_LOCALE, pickLocaleText, type SiteLocale } from "@/lib/locale";

const INVALID_WEBSITE_VALUES = new Set(["unknown", "n/a", "na", "none", "null", "undefined", ""]);
const PLACEHOLDER_VALUES = new Set(["unknown", "n/a", "na", "none", "tbd", "暂无", "未公开", "待定", "unknown.", "n/a."]);
const COMPOSITE_HEAT_WEIGHT = 0.65;
const COMPOSITE_FRESHNESS_WEIGHT = 0.3;
const COMPOSITE_FUNDING_WEIGHT = 0.05;
const FRESHNESS_HALF_LIFE_DAYS = 21;
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
  if (normalized.startsWith("/")) return true;
  try {
    const host = normalizeHost(new URL(normalized).hostname);
    return isAllowedCdnLogoHost(host);
  } catch {
    return false;
  }
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

const ENABLE_EXTERNAL_LOGO_FALLBACK = (() => {
  const raw = String(process.env.NEXT_PUBLIC_LOGO_EXTERNAL_FALLBACK || "")
    .trim()
    .toLowerCase();
  if (!raw) return true;
  return raw === "true";
})();
const LOGO_CDN_HOST = normalizeHost(process.env.NEXT_PUBLIC_LOGO_CDN_BASE_URL);

function isAllowedCdnLogoHost(host: string): boolean {
  if (!host) return false;
  if (!LOGO_CDN_HOST) return false;
  return isSameOrSubdomain(host, LOGO_CDN_HOST);
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

export function getLogoFallbacks(
  website: string | undefined | null
): string[] {
  if (!ENABLE_EXTERNAL_LOGO_FALLBACK) return [];

  const host = resolveLogoHost(website);
  if (!host) return [];

  const directFavicons = [`https://${host}/favicon.ico`];
  if (!host.startsWith("www.")) {
    directFavicons.push(`https://www.${host}/favicon.ico`);
  }

  return directFavicons;
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
    return normalizeHost(parsed.hostname);
  } catch {
    return "";
  }
}

function isTrustedLogoSource(candidate: string, websiteHost: string): boolean {
  if (!candidate) return false;
  if (candidate.startsWith("/")) return true;

  const derivedHost = hostFromProviderCandidate(candidate);
  if (!derivedHost) return false;
  if (isAllowedCdnLogoHost(derivedHost)) return true;
  if (!ENABLE_EXTERNAL_LOGO_FALLBACK) return false;
  if (!websiteHost) return false;
  return isSameOrSubdomain(derivedHost, websiteHost);
}

export function getLogoCandidates(input: LogoCandidatesInput): string[] {
  const result: string[] = [];
  const seen = new Set<string>();
  const websiteHost = resolveLogoHost(input.website);

  const pushIfValid = (value: string | undefined | null) => {
    const normalized = normalizeLogoSource(value);
    if (!isValidLogoSource(normalized)) return;
    if (!isTrustedLogoSource(normalized, websiteHost)) return;
    if (seen.has(normalized)) return;
    seen.add(normalized);
    result.push(normalized);
  };

  pushIfValid(input.logoUrl);
  pushIfValid(input.secondaryLogoUrl);
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

function pickLocalizedText(product: Product, field: keyof Product, locale: SiteLocale): string {
  const zhLocalizedField = `${String(field)}_zh` as keyof Product;
  const zhField = String(product[field] || "").trim();
  const zhLocalized = isPlaceholderValue(String(product[zhLocalizedField] || "").trim())
    ? ""
    : String(product[zhLocalizedField] || "").trim();
  const enField = `${String(field)}_en` as keyof Product;
  const zh = isPlaceholderValue(zhField) ? "" : zhField;
  const en = isPlaceholderValue(String(product[enField] || "").trim())
    ? ""
    : String(product[enField] || "").trim();

  if (locale === "en-US") {
    return en || zh || zhLocalized;
  }

  return zhLocalized || zh || en;
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

function resolvePrimaryProductDate(product: Product): string | undefined {
  return product.discovered_at || product.first_seen || product.published_at;
}

export function productDate(product: Product): number {
  const raw = resolvePrimaryProductDate(product);
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
    const localized = product.categories
      .map((category) => {
        const normalized = normalizeCategoryTokenForLabel(category);
        if (!normalized) return "";
        return getCategoryLabel(normalized, locale);
      })
      .filter(Boolean);

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

export function getDirectionLabel(direction: string, locale: SiteLocale = DEFAULT_LOCALE): string {
  const normalized = normalizeDirectionToken(direction);
  if (!normalized) return "";
  const labels = locale === "en-US" ? DIRECTION_LABELS_EN : DIRECTION_LABELS_ZH;
  return labels[normalized] || normalized.replace(/_/g, " ");
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

export type ProductRegionDisplayInfo = {
  label: string;
  flag: string;
  unknown: boolean;
  source: string;
};

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
  const rawRegion = String(product.region || "").trim();
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
  if (source === "curated" && regionFlag && !DISCOVERY_REGION_FLAGS.has(rawRegion) && FLAG_TO_COUNTRY_CODE[regionFlag]) {
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

  if (
    regionFlag
    && !DISCOVERY_REGION_FLAGS.has(rawRegion)
    && !DISCOVERY_REGION_FLAGS.has(regionFlag)
    && FLAG_TO_COUNTRY_CODE[regionFlag]
  ) {
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

function normalizeMarketToken(value: string): "" | "us" | "cn" | "eu" | "jpkr" | "sea" | "global" {
  const text = String(value || "")
    .trim()
    .toLowerCase();
  if (!text) return "";

  if (text.includes("🇺🇸") || text.includes("美国") || text.includes("united states") || text.includes(" us")) return "us";
  if (text.includes("🇨🇳") || text.includes("中国") || text.includes("china") || text.includes(" cn")) return "cn";
  if (text.includes("🇪🇺") || text.includes("欧洲") || text.includes("europe") || text.includes(" eu")) return "eu";
  if (
    text.includes("🇯🇵🇰🇷")
    || text.includes("🇯🇵")
    || text.includes("🇰🇷")
    || text.includes("日韩")
    || text.includes("日本")
    || text.includes("韩国")
    || text.includes("japan")
    || text.includes("korea")
  ) {
    return "jpkr";
  }
  if (
    text.includes("🇸🇬")
    || text.includes("新加坡")
    || text.includes("东南亚")
    || text.includes("singapore")
    || text.includes("sea")
  ) {
    return "sea";
  }
  if (text.includes("🌍") || text.includes("global") || text.includes("全球")) return "global";
  return "";
}

function marketLabel(token: "us" | "cn" | "eu" | "jpkr" | "sea" | "global", locale: SiteLocale): string {
  if (locale === "en-US") {
    if (token === "us") return "US market";
    if (token === "cn") return "China market";
    if (token === "eu") return "Europe market";
    if (token === "jpkr") return "Japan/Korea market";
    if (token === "sea") return "SEA market";
    return "Global market";
  }

  if (token === "us") return "美国市场";
  if (token === "cn") return "中国市场";
  if (token === "eu") return "欧洲市场";
  if (token === "jpkr") return "日韩市场";
  if (token === "sea") return "东南亚市场";
  return "全球市场";
}

function marketFlag(token: "us" | "cn" | "eu" | "jpkr" | "sea" | "global"): string {
  if (token === "us") return "🇺🇸";
  if (token === "cn") return "🇨🇳";
  if (token === "eu") return "🇪🇺";
  if (token === "jpkr") return "🇯🇵🇰🇷";
  if (token === "sea") return "🇸🇬";
  return "🌍";
}

export function getProductRegionDisplay(product: Product, locale: SiteLocale = DEFAULT_LOCALE): ProductRegionDisplayInfo {
  const country = resolveProductCountry(product);
  if (!country.unknown) {
    return {
      label: country.name,
      flag: country.flag,
      unknown: false,
      source: country.source,
    };
  }

  const regionCandidates = [String(product.source_region || "").trim(), String(product.region || "").trim()].filter(Boolean);
  for (const candidate of regionCandidates) {
    const token = normalizeMarketToken(candidate);
    if (!token) continue;
    return {
      label: marketLabel(token, locale),
      flag: marketFlag(token),
      unknown: false,
      source: "market",
    };
  }

  return {
    label: UNKNOWN_COUNTRY_NAME,
    flag: "",
    unknown: true,
    source: "unknown",
  };
}

export function getFreshnessLabel(
  product: Product,
  now: Date = new Date(),
  locale: SiteLocale = DEFAULT_LOCALE
): string {
  const raw = resolvePrimaryProductDate(product);
  if (!raw) {
    return pickLocaleText(locale, { zh: "时间待补充", en: "Timestamp unavailable" });
  }

  const date = new Date(raw);
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
  if (days < 30) {
    return locale === "en-US" ? `${days}d ago` : `${days}天前`;
  }

  const months = Math.floor(days / 30);
  if (months < 12) {
    return locale === "en-US" ? `${months}mo ago` : `${months}个月前`;
  }

  const years = Math.floor(days / 365);
  return locale === "en-US" ? `${years}y ago` : `${years}年前`;
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
