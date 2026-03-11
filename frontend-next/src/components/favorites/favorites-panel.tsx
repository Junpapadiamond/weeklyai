"use client";

import Link from "next/link";
import { Download, Search, Trash2, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { FavoriteButton } from "@/components/favorites/favorite-button";
import { useSiteLocale } from "@/components/layout/locale-provider";
import {
  clearFavorites,
  exportFavorites,
  FAVORITES_OPEN_EVENT,
  type FavoriteKind,
  getLegacyOnlyFavoritesCount,
  readFavorites,
  subscribeFavorites,
} from "@/lib/favorites";
import {
  collectDirectionOptions,
  filterDirectionOptions,
  getDirectionLabel,
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
  const [productSearch, setProductSearch] = useState("");
  const [blogSearch, setBlogSearch] = useState("");

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

  const productDirectionOptions = useMemo(
    () => collectDirectionOptions(store.products.map((entry) => entry.item), locale),
    [locale, store.products]
  );

  const productTopDirections = useMemo(() => productDirectionOptions.slice(0, 5), [productDirectionOptions]);
  const productSearchDirectionMatches = useMemo(
    () => filterDirectionOptions(productDirectionOptions, productSearch).slice(0, 8),
    [productDirectionOptions, productSearch]
  );

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

  const blogTopFilters = useMemo(() => blogDirectionOptions.slice(0, 5), [blogDirectionOptions]);
  const blogSearchMatches = useMemo(() => {
    const normalized = blogSearch.trim().toLowerCase();
    if (!normalized) return blogDirectionOptions.slice(0, 8);
    return blogDirectionOptions.filter((option) => option.label.toLowerCase().includes(normalized) || option.value.includes(normalized)).slice(0, 8);
  }, [blogDirectionOptions, blogSearch]);

  const activeProductDirectionFilter =
    productDirectionFilter === "all" || productDirectionOptions.some((option) => option.value === productDirectionFilter)
      ? productDirectionFilter
      : "all";

  const activeBlogDirectionFilter =
    blogDirectionFilter === "all" || blogDirectionOptions.some((option) => option.value === blogDirectionFilter)
      ? blogDirectionFilter
      : "all";

  const filteredProducts = useMemo(() => {
    const normalized = productSearch.trim().toLowerCase();
    return store.products.filter((entry) => {
      const directionMatches =
        activeProductDirectionFilter === "all" || getProductDirections(entry.item).includes(activeProductDirectionFilter);
      if (!directionMatches) return false;
      if (!normalized) return true;

      const directionLabel = getProductDirections(entry.item)
        .map((value) => getDirectionLabel(value, locale) || value)
        .join(" ");
      const haystack = `${entry.item.name} ${entry.item.website || ""} ${directionLabel}`.toLowerCase();
      return haystack.includes(normalized);
    });
  }, [activeProductDirectionFilter, locale, productSearch, store.products]);

  const filteredBlogs = useMemo(() => {
    const normalized = blogSearch.trim().toLowerCase();
    return store.blogs.filter((entry) => {
      if (activeBlogDirectionFilter !== "all") {
        if (activeBlogDirectionFilter.startsWith("source:")) {
          const source = activeBlogDirectionFilter.slice("source:".length);
          if (String(entry.item.source || "").trim().toLowerCase() !== source) return false;
        } else if (activeBlogDirectionFilter.startsWith("direction:")) {
          const direction = activeBlogDirectionFilter.slice("direction:".length);
          const matched = (entry.item.categories || []).some((category) => normalizeDirectionToken(category) === direction);
          if (!matched) return false;
        }
      }

      if (!normalized) return true;
      const haystack = `${entry.item.name} ${entry.item.source || ""} ${(entry.item.categories || []).join(" ")}`.toLowerCase();
      return haystack.includes(normalized);
    });
  }, [activeBlogDirectionFilter, blogSearch, store.blogs]);

  const totalCount = store.products.length + store.blogs.length + legacyOnlyCount;

  function downloadExport(kind: FavoriteKind) {
    const payload = exportFavorites(kind);
    const blob = new Blob([payload], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `weeklyai-favorites-${kind}-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  function clearActiveFavorites() {
    clearFavorites(activeKind);
  }

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
            <p>
              {t("共", "Total")} {totalCount} {t("条", "items")}
            </p>
          </div>

          <div className="favorites-panel__header-actions">
            <button type="button" className="favorites-panel__ghost-btn" onClick={() => downloadExport(activeKind)}>
              <Download size={14} /> {t("导出", "Export")}
            </button>
            <button type="button" className="favorites-panel__ghost-btn" onClick={clearActiveFavorites}>
              <Trash2 size={14} /> {t("清空全部", "Clear all")}
            </button>
            <button className="favorites-panel__close" type="button" aria-label={t("关闭收藏夹", "Close favorites")} onClick={() => setIsOpen(false)}>
              <X size={16} />
            </button>
          </div>
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
            <label className="favorites-panel__search">
              <Search size={14} />
              <input
                type="search"
                value={productSearch}
                onChange={(event) => setProductSearch(event.target.value)}
                placeholder={t("搜索收藏或方向", "Search favorites or directions")}
                autoComplete="off"
              />
            </label>

            <div className="favorites-panel__filters">
              <button
                type="button"
                className={`tag-btn ${activeProductDirectionFilter === "all" ? "active" : ""}`}
                onClick={() => setProductDirectionFilter("all")}
              >
                {t("全部方向", "All directions")}
              </button>
              {productTopDirections.map((option) => (
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

            {productSearch.trim() ? (
              <div className="favorites-panel__search-tags">
                {productSearchDirectionMatches.map((option) => (
                  <button
                    key={`search-${option.value}`}
                    type="button"
                    className={`tag-btn ${activeProductDirectionFilter === option.value ? "active" : ""}`}
                    onClick={() => setProductDirectionFilter(option.value)}
                  >
                    {option.label} ({option.count})
                  </button>
                ))}
              </div>
            ) : null}

            <div className="favorites-panel__list">
              {filteredProducts.map((entry) => {
                const product = entry.item;
                const detailId = encodeURIComponent(product._id || product.id || product.name);
                const tone = getTierTone(product);
                const website = normalizeWebsite(product.website);
                const hasWebsite = isValidWebsite(website) && !product.needs_verification;

                return (
                  <article className="favorites-panel__item favorites-panel__item--compact" key={`product-${entry.key}`}>
                    <div className="favorites-panel__item-head">
                      <div>
                        <h3>{product.name}</h3>
                        <p className="favorites-panel__item-meta">
                          {toneLabel(tone, locale)} · {scoreLabel(product.dark_horse_index || product.final_score || product.trending_score, locale)} ·{" "}
                          {t("收藏于", "Saved")} {formatSavedTime(entry.saved_at, locale)}
                        </p>
                      </div>
                      <FavoriteButton product={product} />
                    </div>

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
            <label className="favorites-panel__search">
              <Search size={14} />
              <input
                type="search"
                value={blogSearch}
                onChange={(event) => setBlogSearch(event.target.value)}
                placeholder={t("搜索来源或方向", "Search sources or directions")}
                autoComplete="off"
              />
            </label>

            <div className="favorites-panel__filters">
              <button
                type="button"
                className={`tag-btn ${activeBlogDirectionFilter === "all" ? "active" : ""}`}
                onClick={() => setBlogDirectionFilter("all")}
              >
                {t("全部分类", "All categories")}
              </button>
              {blogTopFilters.map((option) => (
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

            {blogSearch.trim() ? (
              <div className="favorites-panel__search-tags">
                {blogSearchMatches.map((option) => (
                  <button
                    key={`blog-search-${option.value}`}
                    type="button"
                    className={`tag-btn ${activeBlogDirectionFilter === option.value ? "active" : ""}`}
                    onClick={() => setBlogDirectionFilter(option.value)}
                  >
                    {option.label} ({option.count})
                  </button>
                ))}
              </div>
            ) : null}

            <div className="favorites-panel__list">
              {filteredBlogs.map((entry) => {
                const blog = entry.item;
                const website = normalizeWebsite(blog.website);
                const hasWebsite = isValidWebsite(website);
                const source = String(blog.source || "").toLowerCase();
                const sourceLabel = BLOG_SOURCE_LABELS[source] || blog.source || "Blog";

                return (
                  <article className="favorites-panel__item favorites-panel__item--compact" key={`blog-${entry.key}`}>
                    <div className="favorites-panel__item-head">
                      <div>
                        <h3>{blog.name}</h3>
                        <p className="favorites-panel__item-meta">
                          {sourceLabel} · {t("收藏于", "Saved")} {formatSavedTime(entry.saved_at, locale)}
                        </p>
                      </div>
                      <FavoriteButton blog={blog} />
                    </div>

                    <div className="favorites-panel__item-actions">
                      {hasWebsite ? (
                        <a className="link-btn link-btn--card link-btn--card-primary" href={website} target="_blank" rel="noopener noreferrer">
                          {t("原文", "Source")}
                        </a>
                      ) : null}
                    </div>
                  </article>
                );
              })}
            </div>
          </>
        )}

        {activeKind === "product" && filteredProducts.length === 0 ? (
          <div className="empty-state">
            <p className="empty-state-text">{t("当前筛选下暂无收藏产品。", "No saved products in the current filter.")}</p>
          </div>
        ) : null}

        {activeKind === "blog" && filteredBlogs.length === 0 ? (
          <div className="empty-state">
            <p className="empty-state-text">{t("当前筛选下暂无收藏博客动态。", "No saved news posts in the current filter.")}</p>
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
