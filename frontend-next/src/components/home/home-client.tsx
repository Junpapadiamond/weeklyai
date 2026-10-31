"use client";

import Link from "next/link";
import { ProductCard } from "@/components/product/product-card";
import { HorseMark } from "@/components/brand/horse-mark";
import { CategoryPicker } from "@/components/home/category-picker";
import { HomeIntro } from "@/components/home/chinese-home-intro";
import { ArrowUpRight, BookmarkSimple } from "@phosphor-icons/react";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Product } from "@/types/api";
import { parseLastUpdatedLabel, type WeeklyTopSort } from "@/lib/api-client";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { countFavorites, openFavoritesPanel, subscribeFavorites } from "@/lib/favorites";
import {
  collectDirectionOptions,
  filterProducts,
  getProductDirections,
  isHardware,
  productKey,
  sortProducts,
} from "@/lib/product-utils";

const PRODUCTS_PER_PAGE = 12;
const DARK_HORSE_COLLAPSE_LIMIT = 5;
const DEFAULT_WEEKLY_TOP_SORT: WeeklyTopSort = "recency";

type HomeClientProps = {
  darkHorses: Product[];
  allProducts: Product[];
  freshnessHoursAgo: number | null | undefined;
};

type ContentTypeFilter = "all" | "hardware" | "software";

export function HomeClient({ darkHorses, allProducts, freshnessHoursAgo }: HomeClientProps) {
  const { locale, t } = useSiteLocale();
  const [contentTypeFilter, setContentTypeFilter] = useState<ContentTypeFilter>("all");
  const [tierFilter, setTierFilter] = useState<"all" | "darkhorse" | "rising">("all");
  const [directionFilter, setDirectionFilter] = useState("all");
  const [sortBy, setSortBy] = useState<WeeklyTopSort>(DEFAULT_WEEKLY_TOP_SORT);
  const [currentPage, setCurrentPage] = useState(1);
  const [favoritesCount, setFavoritesCount] = useState(0);
  const [showAllDarkHorses, setShowAllDarkHorses] = useState(false);
  const listSentinelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const syncCount = () => setFavoritesCount(countFavorites());
    syncCount();
    return subscribeFavorites(syncCount);
  }, []);


  const productPool = useMemo(() => sortProducts(allProducts, sortBy), [allProducts, sortBy]);

  const filteredDarkHorses = useMemo(() => {
    return darkHorses.filter((product) => {
      if (directionFilter !== "all" && !getProductDirections(product).includes(directionFilter)) return false;
      if (contentTypeFilter === "all") return true;
      if (contentTypeFilter === "hardware") return isHardware(product);
      return !isHardware(product);
    });
  }, [contentTypeFilter, darkHorses, directionFilter]);

  const visibleDarkHorses = useMemo(() => {
    if (showAllDarkHorses) return filteredDarkHorses;
    return filteredDarkHorses.slice(0, DARK_HORSE_COLLAPSE_LIMIT);
  }, [filteredDarkHorses, showAllDarkHorses]);

  const visibleDarkHorseKeys = useMemo(() => {
    return new Set(visibleDarkHorses.map((product) => productKey(product)));
  }, [visibleDarkHorses]);

  const allDirectionOptions = useMemo(() => collectDirectionOptions(allProducts, locale), [allProducts, locale]);

  const activeDirectionFilter =
    directionFilter === "all" || allDirectionOptions.some((option) => option.value === directionFilter)
      ? directionFilter
      : "all";

  const trendingFiltered = useMemo(() => {
    const filtered = filterProducts(productPool, {
      tier: tierFilter,
      type: contentTypeFilter === "all" ? "all" : contentTypeFilter,
    });

    const directionMatched =
      activeDirectionFilter === "all"
        ? filtered
        : filtered.filter((product) => getProductDirections(product).includes(activeDirectionFilter));

    return activeDirectionFilter === "all" && tierFilter === "all"
      ? directionMatched.filter((product) => !visibleDarkHorseKeys.has(productKey(product)))
      : directionMatched;
  }, [activeDirectionFilter, contentTypeFilter, productPool, tierFilter, visibleDarkHorseKeys]);

  const visibleProducts = useMemo(() => {
    return trendingFiltered.slice(0, currentPage * PRODUCTS_PER_PAGE);
  }, [currentPage, trendingFiltered]);

  const hasMore = visibleProducts.length < trendingFiltered.length;

  useEffect(() => {
    if (!hasMore) return;

    const node = listSentinelRef.current;
    if (!node || typeof IntersectionObserver === "undefined") return;

    let hasLoaded = false;
    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries.some((entry) => entry.isIntersecting) || hasLoaded) return;
        hasLoaded = true;
        setCurrentPage((value) => value + 1);
      },
      { rootMargin: "280px" }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [hasMore, visibleProducts.length]);

  const freshnessLabel = useMemo(
    () => parseLastUpdatedLabel(freshnessHoursAgo, locale),
    [freshnessHoursAgo, locale]
  );
  const isArchive = darkHorses.length > 0 && darkHorses.every(product => product.is_archived);

  const selectDirection = (value: string) => {
    setDirectionFilter(value);
    setShowAllDarkHorses(false);
    setCurrentPage(1);
  };


  return (
    <div className="home-root" data-vibe="briefing">
      <HomeIntro />

      <section className="section darkhorse-section" id="darkhorseSection">
        <div className="home-catalog-toolbar">
          <div className="home-catalog-heading">
          <h2 className="section-title">
            {isArchive ? t("往期黑马", "The dark horse archive") : t("近期黑马", "On our radar")}
          </h2>
          <div className="section-utility__freshness" aria-live="polite">
            {freshnessLabel}
          </div>
          </div>
          <div className="section-utility__controls">
            <CategoryPicker options={allDirectionOptions} value={activeDirectionFilter} onChange={selectDirection} />
            <button
              className={`filter-btn ${contentTypeFilter === "all" ? "active" : ""}`}
              aria-pressed={contentTypeFilter === "all"}
              type="button"
              onClick={() => {
                setContentTypeFilter("all");
                setCurrentPage(1);
                setShowAllDarkHorses(false);
              }}
            >
              {t("全部", "All")}
            </button>
            <button
              className={`filter-btn ${contentTypeFilter === "hardware" ? "active" : ""}`}
              aria-pressed={contentTypeFilter === "hardware"}
              type="button"
              onClick={() => {
                setContentTypeFilter("hardware");
                setCurrentPage(1);
                setShowAllDarkHorses(false);
              }}
            >
              {t("硬件", "Hardware")}
            </button>
            <button
              className={`filter-btn ${contentTypeFilter === "software" ? "active" : ""}`}
              aria-pressed={contentTypeFilter === "software"}
              type="button"
              onClick={() => {
                setContentTypeFilter("software");
                setCurrentPage(1);
                setShowAllDarkHorses(false);
              }}
            >
              {t("软件", "Software")}
            </button>
          </div>
        </div>

        {visibleDarkHorses.length ? (
          <div className="darkhorse-spotlight-grid">
            {visibleDarkHorses.map((product, index) => (
              <ProductCard
                key={product._id || product.name}
                product={product}
                highlighted={index === 0}
                favoritable
                rank={index + 1}
              />
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p className="empty-state-text">{t("这个分类暂时没有黑马产品，换个分类看看。", "No dark horse products found for this filter.")}</p>
          </div>
        )}

        {filteredDarkHorses.length > DARK_HORSE_COLLAPSE_LIMIT ? (
          <div className="darkhorse-expand-row">
            <button className="load-more-btn" type="button" onClick={() => setShowAllDarkHorses((value) => !value)}>
              {showAllDarkHorses
                ? t("收起黑马列表", "Collapse dark horse list")
                : locale === "en-US"
                  ? `Show the rest (${filteredDarkHorses.length - DARK_HORSE_COLLAPSE_LIMIT})`
                  : `查看其余黑马 (${filteredDarkHorses.length - DARK_HORSE_COLLAPSE_LIMIT} 款)`}
            </button>
          </div>
        ) : null}
      </section>

      <section className="section trending-section" id="trendingSection">
        <div className="section-header section-header--tight">
          <h2 className="section-title">{t("产品库", "Product library")}</h2>
        </div>

        <div className="list-controls list-controls--compact">
          <div className="tier-tabs">
            <button
              className={`tier-tab ${tierFilter === "all" ? "active" : ""}`}
              aria-pressed={tierFilter === "all"}
              type="button"
              onClick={() => {
                setTierFilter("all");
                setCurrentPage(1);
              }}
            >
              {t("全部", "All")}
            </button>
            <button
              className={`tier-tab ${tierFilter === "darkhorse" ? "active" : ""}`}
              aria-pressed={tierFilter === "darkhorse"}
              type="button"
              onClick={() => {
                setTierFilter("darkhorse");
                setCurrentPage(1);
              }}
            >
              {t("黑马", "Dark Horses")}
            </button>
            <button
              className={`tier-tab ${tierFilter === "rising" ? "active" : ""}`}
              aria-pressed={tierFilter === "rising"}
              type="button"
              onClick={() => {
                setTierFilter("rising");
                setCurrentPage(1);
              }}
            >
              {t("潜力股", "Rising Stars")}
            </button>
          </div>

          <div className="controls-right">
            <label>
              {t("排序", "Sort")}
              <select
                value={sortBy}
                onChange={(event) => {
                  setSortBy(event.target.value as typeof sortBy);
                  setCurrentPage(1);
                }}
              >
                <option value="composite">{t("综合排序", "Discovery score")}</option>
                <option value="trending">{t("热度", "Trending")}</option>
                <option value="recency">{t("最新收录", "Recently discovered")}</option>
              </select>
            </label>

            <CategoryPicker options={allDirectionOptions} value={activeDirectionFilter} onChange={selectDirection} />

            <button
              className="favorites-toggle"
              type="button"
              aria-label={t("打开收藏夹", "Open favorites")}
              onClick={() => openFavoritesPanel("product")}
            >
              <BookmarkSimple size={16} /> {favoritesCount}
            </button>
          </div>
        </div>

        {visibleProducts.length ? (
          <div className="darkhorse-spotlight-grid picks-grid">
            {visibleProducts.map((product, index) => (
              <ProductCard
                key={product._id || product.name}
                product={product}
                rank={index + 1}
                favoritable
              />
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p className="empty-state-text">{t("没有符合条件的产品，试试其他分类。", "No additional picks match this filter.")}</p>
          </div>
        )}

        {hasMore ? <div ref={listSentinelRef} className="picks-list__sentinel" aria-hidden="true" /> : null}
        <Link className="briefing-text-link" href="/search">{t("搜索更多产品", "Search the complete product archive")} <ArrowUpRight size={14} /></Link>
      </section>

      <footer className="section home-footer">
        <div className="home-footer__intro">
          <p className="home-footer__eyebrow"><HorseMark className="footer-brand-mark" />{t("黑马雷达", "Darkhorse Radar")}</p>
        </div>

        <div className="home-footer__links">
          <Link className="home-footer__link" href="/discover">
            {t("随便看看", "Discover")}
          </Link>
          <Link className="home-footer__link" href="/blog">
            {t("AI 资讯", "News")}
          </Link>
          <Link className="home-footer__link" href="/search">
            {t("搜索", "Search")}
          </Link>
        </div>

        <div className="home-footer__meta">
          <Link href="/content-sources">{t("收录与来源", "Selection & sources")}</Link>
          <Link href="/support">{t("联系与反馈", "Support")}</Link>
        </div>
      </footer>

    </div>
  );
}
