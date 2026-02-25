"use client";

import useSWR from "swr";
import { useMemo, useState } from "react";
import { getBlogsClient } from "@/lib/api-client";
import { SmartLogo } from "@/components/common/smart-logo";
import { FavoriteButton } from "@/components/favorites/favorite-button";
import {
  cleanDescription,
  getFreshnessLabel,
  isValidWebsite,
  normalizeWebsite,
} from "@/lib/product-utils";
import type { BlogPost } from "@/types/api";

const SOURCE_LABELS: Record<string, string> = {
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

const SOURCE_ORDER = ["cn_news", "cn_news_glm", "hackernews", "reddit", "tech_news", "producthunt", "youtube", "x"] as const;

const MARKET_OPTIONS = [
  { value: "hybrid", label: "全球 Hybrid" },
  { value: "cn", label: "中国" },
  { value: "us", label: "美国" },
] as const;

const MARKET_LABELS: Record<string, string> = {
  hybrid: "全球 Hybrid",
  cn: "中国",
  us: "美国",
  global: "全球",
};

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
  const website = normalizeWebsite(item.website);
  const hasWebsite = isValidWebsite(website);
  const sourceLabel = SOURCE_LABELS[item.source || ""] || item.source || "Blog";
  const marketLabel = MARKET_LABELS[inferMarket(item)] || "全球";
  const freshness = getFreshnessLabel({
    name: item.name,
    description: item.description,
    published_at: item.published_at,
  });
  const publishedLabel = item.published_at
    ? new Date(item.published_at).toLocaleString("zh-CN", {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "时间待补充";

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

        <p className="product-card__desc">{cleanDescription(item.description)}</p>

        <div className="product-card__actions blog-card__actions">
          <FavoriteButton blog={item} />
          {hasWebsite ? (
            <a className="link-btn link-btn--card" href={website} target="_blank" rel="noopener noreferrer">
              原文
            </a>
          ) : (
            <span className="pending-tag">链接待补充</span>
          )}
        </div>
      </div>
    </article>
  );
}

export function BlogClient() {
  const [source, setSource] = useState("");
  const [market, setMarket] = useState<(typeof MARKET_OPTIONS)[number]["value"]>("hybrid");

  const { data, isLoading, error } = useSWR(
    ["blogs", source, market],
    async ([, selectedSource, selectedMarket]) => {
      try {
        return await getBlogsClient(selectedSource, 80, selectedMarket);
      } catch (err) {
        // 当某些本地环境代理/端口冲突导致请求失败时，回退到 hybrid 并在前端过滤。
        console.warn("Blog fetch failed, fallback to hybrid filter", err);
        try {
          const fallback = await getBlogsClient("", 120, "hybrid");
          return fallback.filter((item) => matchesMarket(item, selectedMarket) && matchesSource(item, selectedSource));
        } catch (fallbackError) {
          console.warn("Blog fallback fetch failed, return empty list", fallbackError);
          return [];
        }
      }
    },
    {
      dedupingInterval: 30_000,
      revalidateOnFocus: false,
    }
  );

  const posts = data || [];
  const sourceOptions = useMemo(() => buildSourceOptions(data), [data]);

  const sourceSummary = source ? `来源：${SOURCE_LABELS[source] || source}` : "来源：全部";
  const marketSummary = `区域：${MARKET_LABELS[market] || market}`;
  const emptyStateText =
    market === "cn"
      ? "暂无中国区动态，请稍后重试或切换全球。"
      : "暂无匹配数据，请切换来源或稍后再试。";

  return (
    <section className="section">
      <div className="section-header">
        <h1 className="section-title">博客 & 动态</h1>
        <p className="section-desc">中国本土源与海外动态共存，可按区域快速切换</p>
        <p className="section-micro-note">{marketSummary} · {sourceSummary} · 共 {posts.length} 条</p>
      </div>

      <div className="blog-toolbar">
        <label>
          区域
          <select
            value={market}
            onChange={(event) => {
              setMarket(event.target.value as (typeof MARKET_OPTIONS)[number]["value"]);
              setSource("");
            }}
          >
            {MARKET_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="source-pills" role="tablist" aria-label="博客来源筛选">
        {sourceOptions.map((option) => {
          const isActive = option === source;
          return (
            <button
              key={option || "all-pill"}
              type="button"
              className={`source-pill ${isActive ? "active" : ""}`}
              onClick={() => setSource(option)}
            >
              {SOURCE_LABELS[option] || option}
            </button>
          );
        })}
      </div>

      {isLoading ? <div className="loading-block">正在加载动态...</div> : null}
      {error ? <div className="error-block">加载失败: {String(error)}</div> : null}

      <div className="products-grid">
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
