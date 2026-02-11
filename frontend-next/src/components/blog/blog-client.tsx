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

const SOURCE_OPTIONS = ["", "hackernews", "producthunt", "youtube", "x", "reddit", "tech_news"];
const SOURCE_LABELS: Record<string, string> = {
  "": "全部",
  hackernews: "Hacker News",
  producthunt: "Product Hunt",
  youtube: "YouTube",
  x: "X",
  reddit: "Reddit",
  tech_news: "Tech News",
};

const BIG_COMPANY_FILTERS = [
  { id: "all", label: "全部公司" },
  { id: "big", label: "大公司" },
  { id: "openai", label: "OpenAI" },
  { id: "google", label: "Google" },
  { id: "microsoft", label: "Microsoft" },
  { id: "meta", label: "Meta" },
  { id: "amazon", label: "Amazon" },
  { id: "apple", label: "Apple" },
  { id: "nvidia", label: "NVIDIA" },
  { id: "anthropic", label: "Anthropic" },
] as const;

const BIG_COMPANY_PATTERNS: Record<string, RegExp> = {
  openai: /(openai|chatgpt|sora)\b/i,
  google: /\b(google|gemini|deepmind|android xr)\b/i,
  microsoft: /\b(microsoft|copilot|azure)\b/i,
  meta: /\b(meta|llama|instagram|whatsapp)\b/i,
  amazon: /\b(amazon|aws|bedrock|alexa)\b/i,
  apple: /\b(apple|vision pro|siri)\b/i,
  nvidia: /\b(nvidia|geforce|cuda)\b/i,
  anthropic: /\b(anthropic|claude)\b/i,
};

function detectBigCompany(item: BlogPost): string[] {
  const website = normalizeWebsite(item.website);
  const haystack = [item.name, item.description, item.source, website].filter(Boolean).join(" ").toLowerCase();
  const matches: string[] = [];
  for (const [key, pattern] of Object.entries(BIG_COMPANY_PATTERNS)) {
    if (pattern.test(haystack)) matches.push(key);
  }
  return matches;
}

function BlogCard({ item }: { item: BlogPost }) {
  const website = normalizeWebsite(item.website);
  const hasWebsite = isValidWebsite(website);
  const sourceLabel = SOURCE_LABELS[item.source || ""] || item.source || "Blog";
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
        <p className="product-card__microline">{`${sourceLabel} · ${freshness}`}</p>

        <header className="product-card__headline blog-card__headline">
          <div className="product-card__identity">
            <SmartLogo
              key={`${item.name}-${item.logo_url || ""}-${item.website || ""}`}
              className="product-card__logo"
              name={item.name}
              logoUrl={item.logo_url}
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
  const [companyFilter, setCompanyFilter] = useState<(typeof BIG_COMPANY_FILTERS)[number]["id"]>("all");

  const { data, isLoading, error } = useSWR(["blogs", source], ([, selectedSource]) => getBlogsClient(selectedSource, 40), {
    dedupingInterval: 30_000,
    revalidateOnFocus: false,
  });

  const posts = useMemo(() => {
    const all = data || [];
    if (companyFilter === "all") return all;

    return all.filter((item) => {
      const matches = detectBigCompany(item);
      if (companyFilter === "big") return matches.length > 0;
      return matches.includes(companyFilter);
    });
  }, [companyFilter, data]);
  const sourceSummary = source ? `当前：${SOURCE_LABELS[source] || source}` : "当前：全部来源";

  return (
    <section className="section">
      <div className="section-header">
        <h1 className="section-title">博客 & 动态</h1>
        <p className="section-desc">来自 YouTube / X / Reddit / HN / Product Hunt 的一手信号</p>
        <p className="section-micro-note">{sourceSummary} · 共 {posts.length} 条</p>
      </div>

      <div className="source-pills" role="tablist" aria-label="博客来源筛选">
        {SOURCE_OPTIONS.map((option) => {
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

      <div className="source-pills" role="tablist" aria-label="大公司筛选">
        {BIG_COMPANY_FILTERS.map((item) => {
          const isActive = item.id === companyFilter;
          return (
            <button
              key={item.id}
              type="button"
              className={`source-pill ${isActive ? "active" : ""}`}
              onClick={() => setCompanyFilter(item.id)}
            >
              {item.label}
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
          <p className="empty-state-text">暂无匹配数据，请切换来源或稍后再试。</p>
        </div>
      ) : null}
    </section>
  );
}
