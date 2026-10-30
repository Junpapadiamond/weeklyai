"use client";

import { useMemo, useState } from "react";
import useSWR from "swr";
import { getBlogsClient, getNewsSourceHealth } from "@/lib/api-client";
import { formatNewsDate } from "@/lib/news-date";
import { SmartLogo } from "@/components/common/smart-logo";
import { FavoriteButton } from "@/components/favorites/favorite-button";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { handleExternalAnchorClick } from "@/lib/external-navigation";
import {
  cleanDescription,
  getFreshnessLabel,
  getLocalizedBlogDescription,
  getLocalizedBlogName,
  isValidWebsite,
  normalizeWebsite,
  resolveProductLogoSources,
} from "@/lib/product-utils";
import type { BlogPost } from "@/types/api";

const SOURCE_LABELS_ZH: Record<string, string> = {
  "": "全部",
  cn_news: "国内资讯",
  cn_news_glm: "国内资讯摘要",
  hackernews: "Hacker News",
  producthunt: "Product Hunt",
  youtube: "YouTube",
  x: "X",
  reddit: "Reddit",
  tech_news: "科技媒体",
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

const SOURCE_ORDER = ["x", "reddit", "youtube", "hackernews", "producthunt", "tech_news", "cn_news"] as const;

const MARKET_LABELS_ZH: Record<string, string> = {
  hybrid: "全部地区",
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

function BlogCard({ item }: { item: BlogPost }) {
  const { locale, t } = useSiteLocale();
  const sourceLabels = locale === "en-US" ? SOURCE_LABELS_EN : SOURCE_LABELS_ZH;
  const marketLabels = locale === "en-US" ? MARKET_LABELS_EN : MARKET_LABELS_ZH;
  const website = normalizeWebsite(item.website);
  const hasWebsite = isValidWebsite(website);
  const sourceLabel = sourceLabels[item.source || ""] || item.source || "Blog";
  const marketLabel = marketLabels[inferMarket(item)] || (locale === "en-US" ? "Global" : "全球");
  const localizedName = getLocalizedBlogName(item, locale) || item.name;
  const localizedDescription = getLocalizedBlogDescription(item, locale) || item.description;
  const summary = cleanDescription(localizedDescription, locale);
  const hasSummary = summary.trim().toLocaleLowerCase() !== localizedName.trim().toLocaleLowerCase();
  const freshness = getFreshnessLabel({
    name: localizedName,
    description: localizedDescription,
    published_at: item.published_at,
  }, new Date(), locale);
  const resolvedLogo = resolveProductLogoSources(item);
  const publishedLabel = formatNewsDate(item.published_at, locale);

  return (
    <article className="research-news">
      <div className="research-news__content">
        <p className="research-news__meta">
          {`${marketLabel} · ${sourceLabel} · `}
          <time dateTime={item.published_at} suppressHydrationWarning>{freshness}</time>
        </p>

        <header className="research-news__header">
          <div className="research-news__identity">
            <SmartLogo
              key={`${item.name}-${resolvedLogo.logoUrl}-${resolvedLogo.secondaryLogoUrl}-${item.website || ""}`}
              className="research-product__logo"
              name={item.name}
              logoUrl={resolvedLogo.logoUrl}
              secondaryLogoUrl={resolvedLogo.secondaryLogoUrl}
              website={item.website}
              trustPrimaryLogo
              size={44}
            />
            <div className="research-news__identity-copy">
              <h3 className="research-product__title">{localizedName}</h3>
              <p className="research-product__date">{publishedLabel}</p>
            </div>
          </div>
        </header>

        {summary && hasSummary ? <p className="research-product__description">{summary}</p> : null}

        <div className="research-news__actions">
          <FavoriteButton blog={item} />
          {hasWebsite ? (
            <a
              className="link-btn link-btn--card"
              href={website}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(event) => handleExternalAnchorClick(event, website)}
            >
              {t("阅读原文", "Source")}
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

  const sourceOptions = market === "cn"
    ? ["", "cn_news"]
    : ["", ...SOURCE_ORDER];
  const activeSource = source;
  const { data, isLoading, error, mutate } = useSWR(
    ["blogs", market, source],
    ([, selectedMarket, selectedSource]) => getBlogsClient(selectedSource, 120, selectedMarket),
    {
      fallbackData: market === "hybrid" && !source ? initialBlogs : undefined,
      refreshInterval: 120_000,
      dedupingInterval: 60_000,
      revalidateOnFocus: false,
    }
  );
  const posts = useMemo(() => (data || []).filter((item) => matchesSource(item, source)), [data, source]);
  const { data: health } = useSWR("news-source-health", getNewsSourceHealth, { refreshInterval: 120_000 });
  const sourceHealth = source ? health?.sources[source] : undefined;
  const sourceUnavailable = sourceHealth && (["retained", "unavailable", "pending"].includes(sourceHealth.status) || health?.stale);

  const emptyStateText =
    market === "cn"
      ? t("暂时没有国内资讯，可以切换到全部地区。", "No China updates yet. Please retry later or switch to global.")
      : t("暂时没有相关资讯，试试其他来源。", "No matching data. Switch source or retry later.");

  return (
    <section className="section blog-page">
      <div className="section-header">
        <h1 className="section-title">{t("AI 资讯", "News & Signals")}</h1>
      </div>

      <div className="blog-toolbar">
        <span role="status" aria-live="polite">
          {isLoading ? t("加载中…", "Loading…") : t(`${posts.length} 条资讯`, `${posts.length} articles`)}
        </span>
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

      <div className="source-pills" role="group" aria-label={t("资讯来源筛选", "News source filters")}>
        {sourceOptions.map((option) => {
          const isActive = option === activeSource;
          return (
            <button
              key={option || "all-pill"}
              type="button"
              className={`source-pill ${isActive ? "active" : ""}`}
              aria-pressed={isActive}
              onClick={() => setSource(option)}
            >
              {sourceLabels[option] || option}
            </button>
          );
        })}
      </div>

      {sourceUnavailable ? (
        <p role="status" className="section-micro-note">
          {posts.length ? t("此来源暂未更新，以下为已收录内容。", "This source has not refreshed; showing saved articles.")
            : t("此来源暂时不可用，请稍后再试。", "This source is temporarily unavailable. Please try later.")}
        </p>
      ) : null}

      {error ? (
        <div className="error-block" role="alert">
          <p>{t("资讯暂时无法更新，请重试。", "News could not be refreshed. Please retry.")}</p>
          <button className="link-btn" type="button" onClick={() => void mutate()}>{t("重试", "Retry")}</button>
        </div>
      ) : null}

      <div className="research-news-grid" aria-busy={isLoading}>
        {posts.map((item) => (
          <BlogCard item={item} key={`${item.source || "source"}-${item.website || item.name}`} />
        ))}
      </div>

      {!isLoading && !error && posts.length === 0 ? (
        <div className="empty-state">
          <p className="empty-state-text">{emptyStateText}</p>
        </div>
      ) : null}
    </section>
  );
}
