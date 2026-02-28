"use client";

import { useMemo, useState } from "react";
import { SmartLogo } from "@/components/common/smart-logo";
import { FavoriteButton } from "@/components/favorites/favorite-button";
import { useSiteLocale } from "@/components/layout/locale-provider";
import {
  cleanDescription,
  getFreshnessLabel,
  isValidWebsite,
  normalizeWebsite,
} from "@/lib/product-utils";
import type { BlogPost } from "@/types/api";

const SOURCE_LABELS_ZH: Record<string, string> = {
  "": "全部",
  cn_news: "中国本土源",
  cn_news_glm: "中国本土源（GLM）",
  hackernews: "Hacker News",
  producthunt: "Product Hunt",
  youtube: "YouTube",
  x: "X",
  reddit: "Reddit",
  tech_news: "Tech News",
};

const SOURCE_LABELS_EN: Record<string, string> = {
  "": "All",
  cn_news: "China Local Sources",
  cn_news_glm: "China Local Sources (GLM)",
  hackernews: "Hacker News",
  producthunt: "Product Hunt",
  youtube: "YouTube",
  x: "X",
  reddit: "Reddit",
  tech_news: "Tech News",
};

const SOURCE_ORDER = ["cn_news", "cn_news_glm", "hackernews", "reddit", "tech_news", "producthunt", "youtube", "x"] as const;

const MARKET_LABELS_ZH: Record<string, string> = {
  hybrid: "全球 Hybrid",
  cn: "中国",
  us: "美国",
  global: "全球",
};

const MARKET_LABELS_EN: Record<string, string> = {
  hybrid: "Global Hybrid",
  cn: "China",
  us: "United States",
  global: "Global",
};
type MarketValue = "hybrid" | "cn" | "us";

const US_SOURCES = new Set(["hackernews", "producthunt", "youtube", "x", "reddit", "tech_news"]);
const SOURCE_ALIASES: Record<string, string[]> = {
  youtube: ["youtube", "youtube_rss", "yt"],
  x: ["x", "twitter"],
  reddit: ["reddit"],
};

function normalizeSource(value: string | undefined): string {
  return String(value || "").trim().toLowerCase();
}

function matchesSource(item: BlogPost, selectedSource: string): boolean {
  const target = normalizeSource(selectedSource);
  if (!target) return true;

  const source = normalizeSource(item.source);
  if (source === target) return true;

  const aliases = SOURCE_ALIASES[target];
  if (aliases && aliases.includes(source)) return true;

  return false;
}

function inferMarket(item: BlogPost): "cn" | "us" | "global" {
  const explicit = String(item.market || "").trim().toLowerCase();
  if (explicit === "cn" || explicit === "us" || explicit === "global" || explicit === "hybrid") {
    return explicit === "hybrid" ? "global" : (explicit as "cn" | "us" | "global");
  }
  const source = String(item.source || "").trim().toLowerCase();
  if (source === "cn_news") return "cn";
  if (US_SOURCES.has(source)) return "us";
  const extra = item.extra && typeof item.extra === "object" ? (item.extra as Record<string, unknown>) : {};
  const fromExtra = String(extra.news_market || "").trim().toLowerCase();
  if (fromExtra === "cn" || fromExtra === "us" || fromExtra === "global") return fromExtra as "cn" | "us" | "global";
  return "global";
}

function matchesMarket(item: BlogPost, selectedMarket: string): boolean {
  const market = String(selectedMarket || "").trim().toLowerCase();
  if (!market || market === "hybrid" || market === "global") return true;
  return inferMarket(item) === market;
}

function buildSourceOptions(data: BlogPost[] | undefined) {
  const seen = new Set<string>();
  for (const item of data || []) {
    const source = String(item.source || "").trim();
    if (source) seen.add(source);
  }

  const ordered: string[] = [];
  for (const source of SOURCE_ORDER) {
    if (seen.has(source)) ordered.push(source);
  }

  const rest = [...seen]
    .filter((source) => !(SOURCE_ORDER as readonly string[]).includes(source))
    .sort((a, b) => a.localeCompare(b, "en"));

  return ["", ...ordered, ...rest];
}

function BlogCard({ item }: { item: BlogPost }) {
  const { locale, t } = useSiteLocale();
  const sourceLabels = locale === "en-US" ? SOURCE_LABELS_EN : SOURCE_LABELS_ZH;
  const marketLabels = locale === "en-US" ? MARKET_LABELS_EN : MARKET_LABELS_ZH;
  const website = normalizeWebsite(item.website);
  const hasWebsite = isValidWebsite(website);
  const sourceLabel = sourceLabels[item.source || ""] || item.source || "Blog";
  const marketLabel = marketLabels[inferMarket(item)] || (locale === "en-US" ? "Global" : "全球");
  const freshness = getFreshnessLabel({
    name: item.name,
    description: item.description,
    published_at: item.published_at,
  }, new Date(), locale);
  const publishedLabel = item.published_at
    ? new Date(item.published_at).toLocaleString(locale, {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      })
    : t("时间待补充", "Timestamp unavailable");

  return (
    <article className="product-card product-card--signal product-card--watch product-card--compact">
      <div className="product-card__content blog-card__content">
        <p className="product-card__microline">{`${marketLabel} · ${sourceLabel} · ${freshness}`}</p>

        <header className="product-card__headline blog-card__headline">
          <div className="product-card__identity">
            <SmartLogo
              key={`${item.name}-${item.logo_url || ""}-${item.logo || ""}-${item.website || ""}`}
              className="product-card__logo"
              name={item.name}
              logoUrl={item.logo_url}
              secondaryLogoUrl={item.logo}
              website={item.website}
              size={44}
            />
            <div className="product-card__identity-copy">
              <h3 className="product-card__title">{item.name}</h3>
              <p className="product-card__meta">{publishedLabel}</p>
            </div>
          </div>
        </header>

        <p className="product-card__desc">{cleanDescription(item.description, locale)}</p>

        <div className="product-card__actions blog-card__actions">
          <FavoriteButton blog={item} />
          {hasWebsite ? (
            <a className="link-btn link-btn--card" href={website} target="_blank" rel="noopener noreferrer">
              {t("原文", "Source")}
            </a>
          ) : (
            <span className="pending-tag">{t("链接待补充", "Link pending")}</span>
          )}
        </div>
      </div>
    </article>
  );
}

type BlogClientProps = {
  initialBlogs: BlogPost[];
};

export function BlogClient({ initialBlogs }: BlogClientProps) {
  const { locale, t } = useSiteLocale();
  const [source, setSource] = useState("");
  const [market, setMarket] = useState<MarketValue>("hybrid");
  const sourceLabels = locale === "en-US" ? SOURCE_LABELS_EN : SOURCE_LABELS_ZH;
  const marketLabels = locale === "en-US" ? MARKET_LABELS_EN : MARKET_LABELS_ZH;
  const marketOptions = [
    { value: "hybrid", label: marketLabels.hybrid },
    { value: "cn", label: marketLabels.cn },
    { value: "us", label: marketLabels.us },
  ] as const;

  const marketBlogs = useMemo(() => initialBlogs.filter((item) => matchesMarket(item, market)), [initialBlogs, market]);
  const sourceOptions = useMemo(() => buildSourceOptions(marketBlogs), [marketBlogs]);

  const activeSource = source && sourceOptions.includes(source) ? source : "";
  const posts = useMemo(
    () => marketBlogs.filter((item) => matchesSource(item, activeSource)),
    [activeSource, marketBlogs]
  );

  const sourceSummary = activeSource
    ? `${t("来源", "Source")}: ${sourceLabels[activeSource] || activeSource}`
    : `${t("来源", "Source")}: ${sourceLabels[""]}`;
  const marketSummary = `${t("区域", "Region")}: ${marketLabels[market] || market}`;
  const emptyStateText =
    market === "cn"
      ? t("暂无中国区动态，请稍后重试或切换全球。", "No China updates yet. Please retry later or switch to global.")
      : t("暂无匹配数据，请切换来源或稍后再试。", "No matching data. Switch source or retry later.");

  return (
    <section className="section">
      <div className="section-header">
        <h1 className="section-title">{t("博客 & 动态", "News & Signals")}</h1>
        <p className="section-desc">{t("中国本土源与海外动态共存，可按区域快速切换", "China-local and global sources in one feed, with quick market switching.")}</p>
        <p className="section-micro-note">
          {marketSummary} · {sourceSummary} · {locale === "en-US" ? `${posts.length} items` : `共 ${posts.length} 条`}
        </p>
      </div>

      <div className="blog-toolbar">
        <label>
          {t("区域", "Market")}
          <select
            value={market}
            onChange={(event) => {
              setMarket(event.target.value as MarketValue);
              setSource("");
            }}
          >
            {marketOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="source-pills" role="tablist" aria-label={t("博客来源筛选", "News source filters")}>
        {sourceOptions.map((option) => {
          const isActive = option === activeSource;
          return (
            <button
              key={option || "all-pill"}
              type="button"
              className={`source-pill ${isActive ? "active" : ""}`}
              onClick={() => setSource(option)}
            >
              {sourceLabels[option] || option}
            </button>
          );
        })}
      </div>

      <div className="products-grid">
        {posts.map((item) => (
          <BlogCard item={item} key={`${item.source || "source"}-${item.website || item.name}`} />
        ))}
      </div>

      {posts.length === 0 ? (
        <div className="empty-state">
          <p className="empty-state-text">{emptyStateText}</p>
        </div>
      ) : null}
    </section>
  );
}
