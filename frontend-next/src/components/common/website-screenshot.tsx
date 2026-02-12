"use client";

import { CSSProperties, useMemo, useState } from "react";
import {
  Bot,
  Code2,
  Cpu,
  GraduationCap,
  HeartPulse,
  Image as ImageIcon,
  PenSquare,
  Sparkles,
  Video,
  Wallet,
} from "lucide-react";
import { SmartLogo } from "@/components/common/smart-logo";
import { isValidWebsite, normalizeWebsite } from "@/lib/product-utils";

type WebsiteScreenshotProps = {
  className?: string;
  website?: string;
  name?: string;
  logoUrl?: string;
  secondaryLogoUrl?: string;
  sourceUrl?: string;
  category?: string;
  categories?: string[];
  isHardware?: boolean;
  alt?: string;
  logoSize?: number;
};

type FallbackMode = "logo" | "category" | null;
type FallbackState = {
  key: string;
  mode: FallbackMode;
};

function getThumioUrl(website?: string): string {
  const normalized = normalizeWebsite(website);
  if (!isValidWebsite(normalized)) return "";
  return `https://image.thum.io/get/width/1200/noanimate/${encodeURI(normalized)}`;
}

function normalizeCategory(value?: string): string {
  if (!value) return "";
  return value.trim().toLowerCase();
}

function resolveCategoryToken(input: { category?: string; categories?: string[]; isHardware?: boolean }): string {
  if (input.isHardware) return "hardware";

  const ordered = [input.category, ...(input.categories || [])].map((item) => normalizeCategory(item));
  for (const token of ordered) {
    if (!token) continue;
    if (token.includes("hardware") || token.includes("chip") || token.includes("robot")) return "hardware";
    if (token.includes("coding") || token.includes("code")) return "coding";
    if (token.includes("image")) return "image";
    if (token.includes("video")) return "video";
    if (token.includes("voice") || token.includes("audio")) return "voice";
    if (token.includes("writing") || token.includes("write")) return "writing";
    if (token.includes("education")) return "education";
    if (token.includes("health")) return "healthcare";
    if (token.includes("finance")) return "finance";
    if (token.includes("agent")) return "agent";
  }

  return "other";
}

function categoryVisual(token: string) {
  if (token === "hardware") return { label: "硬件方向", icon: Cpu, colors: ["#3b82f6", "#0891b2"] };
  if (token === "coding") return { label: "编程开发", icon: Code2, colors: ["#2563eb", "#6d28d9"] };
  if (token === "image") return { label: "图像生成", icon: ImageIcon, colors: ["#db2777", "#f97316"] };
  if (token === "video") return { label: "视频创作", icon: Video, colors: ["#f59e0b", "#dc2626"] };
  if (token === "voice") return { label: "语音交互", icon: Bot, colors: ["#0ea5e9", "#6366f1"] };
  if (token === "writing") return { label: "写作助手", icon: PenSquare, colors: ["#0f766e", "#0ea5a3"] };
  if (token === "education") return { label: "教育学习", icon: GraduationCap, colors: ["#16a34a", "#15803d"] };
  if (token === "healthcare") return { label: "医疗健康", icon: HeartPulse, colors: ["#dc2626", "#f43f5e"] };
  if (token === "finance") return { label: "金融工具", icon: Wallet, colors: ["#7c3aed", "#4f46e5"] };
  if (token === "agent") return { label: "Agent 应用", icon: Bot, colors: ["#2563eb", "#7c3aed"] };
  return { label: "AI 产品", icon: Sparkles, colors: ["#475569", "#334155"] };
}

function analyzeScreenshotQuality(image: HTMLImageElement): boolean {
  if (typeof document === "undefined") return false;

  try {
    if (image.naturalWidth < 580 || image.naturalHeight < 300) return true;

    const width = 64;
    const height = Math.max(36, Math.round((image.naturalHeight / image.naturalWidth) * width));
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    if (!context) return false;

    context.drawImage(image, 0, 0, width, height);
    const data = context.getImageData(0, 0, width, height).data;
    if (!data.length) return false;

    const bins = new Map<number, number>();
    let valid = 0;
    let sumL = 0;
    let sumL2 = 0;
    let dominant = 0;

    for (let i = 0; i < data.length; i += 4) {
      const alpha = data[i + 3];
      if (alpha < 180) continue;

      const r = data[i];
      const g = data[i + 1];
      const b = data[i + 2];
      const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
      sumL += luminance;
      sumL2 += luminance * luminance;
      valid += 1;

      const qr = Math.round(r / 26);
      const qg = Math.round(g / 26);
      const qb = Math.round(b / 26);
      const key = (qr << 10) + (qg << 5) + qb;
      const next = (bins.get(key) || 0) + 1;
      bins.set(key, next);
      if (next > dominant) dominant = next;
    }

    if (valid < 240) return true;

    const mean = sumL / valid;
    const variance = Math.max(0, sumL2 / valid - mean * mean);
    const std = Math.sqrt(variance);
    const diversity = bins.size;
    const dominantRatio = dominant / valid;

    return (dominantRatio > 0.58 && std < 36) || diversity < 42 || std < 20;
  } catch {
    return false;
  }
}

export function WebsiteScreenshot({
  className,
  website,
  name,
  logoUrl,
  secondaryLogoUrl,
  sourceUrl,
  category,
  categories,
  isHardware,
  alt,
  logoSize = 44,
}: WebsiteScreenshotProps) {
  const screenshotUrl = useMemo(() => getThumioUrl(website), [website]);
  const [fallbackState, setFallbackState] = useState<FallbackState>({ key: "", mode: null });
  const token = useMemo(() => resolveCategoryToken({ category, categories, isHardware }), [category, categories, isHardware]);
  const visual = useMemo(() => categoryVisual(token), [token]);
  const visualStyle = useMemo(
    () =>
      ({
        "--shot-color-a": visual.colors[0],
        "--shot-color-b": visual.colors[1],
      }) as CSSProperties,
    [visual.colors]
  );
  const fallbackMode = fallbackState.key === screenshotUrl ? fallbackState.mode : null;
  const showImage = !!screenshotUrl && fallbackMode === null;

  return (
    <div className={`website-shot ${className || ""}`}>
      {showImage ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          className="website-shot__image"
          src={screenshotUrl}
          alt={alt || `${name || "产品"} 官网截图`}
          crossOrigin="anonymous"
          loading="lazy"
          decoding="async"
          onError={() => setFallbackState({ key: screenshotUrl, mode: "logo" })}
          onLoad={(event) => {
            if (analyzeScreenshotQuality(event.currentTarget)) {
              setFallbackState({ key: screenshotUrl, mode: "category" });
            }
          }}
        />
      ) : (
        <>
          {fallbackMode === "category" ? (
            <div className="website-shot__category" style={visualStyle} aria-label="截图质量一般，已切换分类占位图">
              <visual.icon className="website-shot__category-icon" size={30} aria-hidden="true" />
              <strong className="website-shot__category-text">{visual.label}</strong>
              <span className="website-shot__category-note">截图质量一般，已显示占位图</span>
            </div>
          ) : (
            <div className="website-shot__fallback" aria-label="官网截图加载失败，已显示 Logo">
              <SmartLogo
                className="website-shot__logo"
                name={name}
                logoUrl={logoUrl}
                secondaryLogoUrl={secondaryLogoUrl}
                website={website}
                sourceUrl={sourceUrl}
                size={logoSize}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}
