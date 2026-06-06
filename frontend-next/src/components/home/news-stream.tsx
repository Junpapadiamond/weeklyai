"use client";

import { SmartLogo } from "@/components/common/smart-logo";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { handleExternalAnchorClick } from "@/lib/external-navigation";
import {
  cleanDescription,
  formatAbsoluteDate,
  getLocalizedBlogDescription,
  getLocalizedBlogName,
  isValidWebsite,
  normalizeWebsite,
  resolveProductLogoSources,
} from "@/lib/product-utils";
import type { BlogPost } from "@/types/api";

type NewsStreamProps = {
  blogs: BlogPost[];
};

const SOURCE_LABELS: Record<string, string> = {
  cn_news: "36Kr",
  cn_news_glm: "CN radar",
  hackernews: "Hacker News",
  producthunt: "Product Hunt",
  youtube: "YouTube",
  x: "X",
  reddit: "Reddit",
  tech_news: "Tech News",
};

export function NewsStream({ blogs }: NewsStreamProps) {
  const { locale, t } = useSiteLocale();

  return (
    <section className="v2-section v2-news-section">
      <div className="v2-section-head">
        <h2>{t("AI news", "AI news")}</h2>
        <span>{t("补充消费", "Side stream")}</span>
      </div>
      <div className="v2-news-list">
        {blogs.slice(0, 10).map((blog) => {
          const title = getLocalizedBlogName(blog, locale) || blog.name;
          const desc = cleanDescription(getLocalizedBlogDescription(blog, locale) || blog.description, locale);
          const website = normalizeWebsite(blog.website);
          const hasWebsite = isValidWebsite(website);
          const source = String(blog.source || "").trim().toLowerCase();
          const sourceLabel = SOURCE_LABELS[source] || blog.source || "AI";
          const logo = resolveProductLogoSources(blog);
          const date = formatAbsoluteDate(blog.published_at, locale) || t("时间待补充", "Date pending");

          const inner = (
            <>
              <SmartLogo
                className="v2-news-logo"
                name={sourceLabel}
                logoUrl={logo.logoUrl}
                secondaryLogoUrl={logo.secondaryLogoUrl}
                website={blog.website}
                trustPrimaryLogo
                size={16}
              />
              <div className="v2-news-copy">
                <div className="v2-news-meta">{sourceLabel} · {date}</div>
                <h3>{title}</h3>
                <p>{desc}</p>
              </div>
            </>
          );

          return hasWebsite ? (
            <a
              key={`${blog.name}-${blog.published_at || ""}`}
              className="v2-news-item"
              href={website}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(event) => handleExternalAnchorClick(event, website)}
            >
              {inner}
            </a>
          ) : (
            <article key={`${blog.name}-${blog.published_at || ""}`} className="v2-news-item">
              {inner}
            </article>
          );
        })}
        {blogs.length === 0 ? <div className="v2-strip-empty">{t("暂无新闻", "No news yet")}</div> : null}
      </div>
    </section>
  );
}
