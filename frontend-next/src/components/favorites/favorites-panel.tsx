"use client";

import Link from "next/link";
import { X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { FavoriteButton } from "@/components/favorites/favorite-button";
import { useSiteLocale } from "@/components/layout/locale-provider";
import {
  FAVORITES_OPEN_EVENT,
  type FavoriteKind,
  getLegacyOnlyFavoritesCount,
  readFavorites,
  subscribeFavorites,
} from "@/lib/favorites";
import {
  cleanDescription,
  getDirectionLabel,
  getLocalizedProductDescription,
  getProductDirections,
  getTierTone,
  isValidWebsite,
  normalizeDirectionToken,
  normalizeWebsite,
} from "@/lib/product-utils";

const BLOG_SOURCE_LABELS: Record<string, string> = {
  hackernews: "Hacker News",
  producthunt: "Product Hunt",
  youtube: "YouTube",
  x: "X",
  reddit: "Reddit",
  tech_news: "Tech News",
};

function formatSavedTime(value: string | undefined, locale: "zh-CN" | "en-US") {
  if (!value) return locale === "en-US" ? "Just now" : "刚刚";
  const ts = new Date(value);
  if (!Number.isFinite(ts.getTime())) return locale === "en-US" ? "Just now" : "刚刚";
  return ts.toLocaleString(locale, {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function scoreLabel(score: number | undefined, locale: "zh-CN" | "en-US"): string {
  const safe = score || 0;
  if (safe >= 4) return locale === "en-US" ? `Dark Horse ${safe}/5` : `黑马 ${safe}分`;
  if (safe >= 2) return locale === "en-US" ? `Rising ${safe}/5` : `潜力 ${safe}分`;
  if (safe > 0) return locale === "en-US" ? `${safe}/5` : `${safe}分`;
  return locale === "en-US" ? "Unrated" : "待评";
}

function toneLabel(tone: "darkhorse" | "rising" | "watch", locale: "zh-CN" | "en-US"): string {
  if (tone === "darkhorse") return locale === "en-US" ? "Dark Horse" : "黑马";
  if (tone === "rising") return locale === "en-US" ? "Rising" : "潜力";
  return locale === "en-US" ? "Watch" : "观察";
}

export function FavoritesPanel() {
  const { locale, t } = useSiteLocale();
  const [store, setStore] = useState<ReturnType<typeof readFavorites>>({
    version: 3,
    products: [],
    blogs: [],
  });
  const [legacyOnlyCount, setLegacyOnlyCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [activeKind, setActiveKind] = useState<FavoriteKind>("product");
  const [productDirectionFilter, setProductDirectionFilter] = useState("all");
  const [blogDirectionFilter, setBlogDirectionFilter] = useState("all");

  useEffect(() => {
    const sync = () => {
      const nextStore = readFavorites();
      setStore(nextStore);
      setLegacyOnlyCount(getLegacyOnlyFavoritesCount(nextStore));
    };
    sync();
    const unsubscribe = subscribeFavorites(sync);
    const onOpen = (event: Event) => {
      const customEvent = event as CustomEvent<{ kind?: FavoriteKind }>;
      const kind = customEvent.detail?.kind;
      if (kind === "product" || kind === "blog") {
        setActiveKind(kind);
      }
      setIsOpen(true);
    };

    window.addEventListener(FAVORITES_OPEN_EVENT, onOpen as EventListener);
    return () => {
      unsubscribe();
      window.removeEventListener(FAVORITES_OPEN_EVENT, onOpen as EventListener);
    };
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isOpen]);

  const productDirectionOptions = useMemo(() => {
    const counts = new Map<string, number>();
    for (const entry of store.products) {
      for (const direction of getProductDirections(entry.item)) {
        counts.set(direction, (counts.get(direction) || 0) + 1);
      }
    }
    return [...counts.entries()]
      .map(([value, count]) => ({ value, count, label: getDirectionLabel(value, locale) || value }))
      .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, locale));
  }, [locale, store.products]);

  const blogDirectionOptions = useMemo(() => {
    const counts = new Map<string, { label: string; count: number }>();

    for (const entry of store.blogs) {
      const source = String(entry.item.source || "")
        .trim()
        .toLowerCase();
      if (source) {
        const key = `source:${source}`;
        const label = `${t("来源", "Source")} · ${BLOG_SOURCE_LABELS[source] || source}`;
        const current = counts.get(key);
        counts.set(key, { label, count: (current?.count || 0) + 1 });
      }

      for (const category of entry.item.categories || []) {
        const normalized = normalizeDirectionToken(category);
        if (!normalized) continue;
        const key = `direction:${normalized}`;
        const label = `${t("方向", "Direction")} · ${getDirectionLabel(normalized, locale) || normalized}`;
        const current = counts.get(key);
        counts.set(key, { label, count: (current?.count || 0) + 1 });
      }
    }

    return [...counts.entries()]
      .map(([value, payload]) => ({ value, label: payload.label, count: payload.count }))
      .sort((a, b) => {
        const sourceDelta = Number(a.value.startsWith("source:")) - Number(b.value.startsWith("source:"));
        if (sourceDelta !== 0) return sourceDelta * -1;
        return b.count - a.count || a.label.localeCompare(b.label, locale);
      });
  }, [locale, store.blogs, t]);

  const activeProductDirectionFilter =
    productDirectionFilter === "all" || productDirectionOptions.some((option) => option.value === productDirectionFilter)
      ? productDirectionFilter
      : "all";

  const activeBlogDirectionFilter =
    blogDirectionFilter === "all" || blogDirectionOptions.some((option) => option.value === blogDirectionFilter)
      ? blogDirectionFilter
      : "all";

  const filteredProducts = useMemo(() => {
    if (activeProductDirectionFilter === "all") return store.products;
    return store.products.filter((entry) => getProductDirections(entry.item).includes(activeProductDirectionFilter));
  }, [activeProductDirectionFilter, store.products]);

  const filteredBlogs = useMemo(() => {
    if (activeBlogDirectionFilter === "all") return store.blogs;
    if (activeBlogDirectionFilter.startsWith("source:")) {
      const source = activeBlogDirectionFilter.slice("source:".length);
      return store.blogs.filter((entry) => String(entry.item.source || "").trim().toLowerCase() === source);
    }
    if (activeBlogDirectionFilter.startsWith("direction:")) {
      const direction = activeBlogDirectionFilter.slice("direction:".length);
      return store.blogs.filter((entry) =>
        (entry.item.categories || []).some((category) => normalizeDirectionToken(category) === direction)
      );
    }
    return store.blogs;
  }, [activeBlogDirectionFilter, store.blogs]);

  const totalCount = store.products.length + store.blogs.length + legacyOnlyCount;

  return (
    <>
      <div
        className={`favorites-panel__backdrop ${isOpen ? "is-open" : ""}`}
        aria-hidden={!isOpen}
        onClick={() => setIsOpen(false)}
      />
      <aside className={`favorites-panel ${isOpen ? "is-open" : ""}`} aria-hidden={!isOpen}>
        <header className="favorites-panel__header">
          <div>
            <h2>{t("收藏夹", "Favorites")}</h2>
            <p>{t("共", "Total")} {totalCount} {t("条", "items")}</p>
          </div>
          <button className="favorites-panel__close" type="button" aria-label={t("关闭收藏夹", "Close favorites")} onClick={() => setIsOpen(false)}>
            <X size={16} />
          </button>
        </header>

        <div className="favorites-panel__tabs">
          <button
            className={`tier-tab ${activeKind === "product" ? "active" : ""}`}
            type="button"
            onClick={() => setActiveKind("product")}
          >
            {t("产品", "Products")} ({store.products.length})
          </button>
          <button
            className={`tier-tab ${activeKind === "blog" ? "active" : ""}`}
            type="button"
            onClick={() => setActiveKind("blog")}
          >
            {t("博客动态", "News")} ({store.blogs.length})
          </button>
        </div>

        {activeKind === "product" ? (
          <>
            <div className="favorites-panel__filters">
              <button
                type="button"
                className={`tag-btn ${activeProductDirectionFilter === "all" ? "active" : ""}`}
                onClick={() => setProductDirectionFilter("all")}
              >
                {t("全部方向", "All directions")}
              </button>
              {productDirectionOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={`tag-btn ${activeProductDirectionFilter === option.value ? "active" : ""}`}
                  onClick={() => setProductDirectionFilter(option.value)}
                >
                  {option.label} ({option.count})
                </button>
              ))}
            </div>

            <div className="favorites-panel__list">
              {filteredProducts.map((entry) => {
                const product = entry.item;
                const detailId = encodeURIComponent(product._id || product.id || product.name);
                const tone = getTierTone(product);
                const website = normalizeWebsite(product.website);
                const hasWebsite = isValidWebsite(website);
                const directionLabel = getProductDirections(product)
                  .map((value) => getDirectionLabel(value, locale) || value)
                  .join(" · ");
                return (
                  <article className="favorites-panel__item" key={`product-${entry.key}`}>
                    <div className="favorites-panel__item-head">
                      <h3>{product.name}</h3>
                      <FavoriteButton product={product} />
                    </div>
                    <p className="favorites-panel__item-meta">
                      {toneLabel(tone, locale)} ·{" "}
                      {scoreLabel(product.dark_horse_index || product.final_score || product.trending_score, locale)} ·{" "}
                      {t("收藏于", "Saved")} {formatSavedTime(entry.saved_at, locale)}
                    </p>
                    {directionLabel ? <p className="favorites-panel__item-tags">{t("方向", "Direction")}: {directionLabel}</p> : null}
                    <p className="favorites-panel__item-desc">{cleanDescription(product.description, locale)}</p>
                    <div className="favorites-panel__item-actions">
                      <Link href={`/product/${detailId}`} className="link-btn link-btn--card link-btn--card-primary">
                        {t("详情", "Details")}
                      </Link>
                      {hasWebsite ? (
                        <a className="link-btn link-btn--card" href={website} target="_blank" rel="noopener noreferrer">
                          {t("官网", "Website")}
                        </a>
                      ) : (
                        <span className="pending-tag">{t("官网待验证", "Website pending verification")}</span>
                      )}
                    </div>
                  </article>
                );
              })}
            </div>
          </>
        ) : (
          <>
            <div className="favorites-panel__filters">
              <button
                type="button"
                className={`tag-btn ${activeBlogDirectionFilter === "all" ? "active" : ""}`}
                onClick={() => setBlogDirectionFilter("all")}
              >
                {t("全部分类", "All categories")}
              </button>
              {blogDirectionOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={`tag-btn ${activeBlogDirectionFilter === option.value ? "active" : ""}`}
                  onClick={() => setBlogDirectionFilter(option.value)}
                >
                  {option.label} ({option.count})
                </button>
              ))}
            </div>

            <div className="favorites-panel__list">
              {filteredBlogs.map((entry) => {
                const blog = entry.item;
                const website = normalizeWebsite(blog.website);
                const hasWebsite = isValidWebsite(website);
                const source = String(blog.source || "").toLowerCase();
                const sourceLabel = BLOG_SOURCE_LABELS[source] || blog.source || "Blog";
                const categoryLabel = (blog.categories || [])
                  .map((value) => getDirectionLabel(normalizeDirectionToken(value), locale) || value)
                  .join(" · ");
                return (
                  <article className="favorites-panel__item" key={`blog-${entry.key}`}>
                    <div className="favorites-panel__item-head">
                      <h3>{blog.name}</h3>
                      <FavoriteButton blog={blog} />
                    </div>
                    <p className="favorites-panel__item-meta">
                      {sourceLabel} · {t("收藏于", "Saved")} {formatSavedTime(entry.saved_at, locale)}
                    </p>
                    {categoryLabel ? <p className="favorites-panel__item-tags">{t("方向", "Direction")}: {categoryLabel}</p> : null}
                    <p className="favorites-panel__item-desc">{cleanDescription(blog.description, locale)}</p>
                    <div className="favorites-panel__item-actions">
                      {hasWebsite ? (
                        <a className="link-btn link-btn--card link-btn--card-primary" href={website} target="_blank" rel="noopener noreferrer">
                          {t("原文", "Source")}
                        </a>
                      ) : (
                        <span className="pending-tag">{t("链接待补充", "Link pending")}</span>
                      )}
                    </div>
                  </article>
                );
              })}
            </div>
          </>
        )}

        {activeKind === "product" && filteredProducts.length === 0 ? (
          <div className="empty-state">
            <p className="empty-state-text">{t("该分类下暂无收藏产品。", "No saved products in this category.")}</p>
          </div>
        ) : null}

        {activeKind === "blog" && filteredBlogs.length === 0 ? (
          <div className="empty-state">
            <p className="empty-state-text">{t("该分类下暂无收藏博客动态。", "No saved news posts in this category.")}</p>
          </div>
        ) : null}

        {legacyOnlyCount > 0 ? (
          <p className="favorites-panel__legacy-note">
            {t(
              `另有 ${legacyOnlyCount} 条历史收藏仅包含旧键值，建议重新收藏一次以补全产品信息。`,
              `${legacyOnlyCount} legacy favorites use old keys only. Re-save them once to complete product details.`
            )}
          </p>
        ) : null}
      </aside>
    </>
  );
}
