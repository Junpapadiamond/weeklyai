"use client";

import Link from "next/link";
import { ProductCard } from "@/components/product/product-card";
import { HorseMark } from "@/components/brand/horse-mark";
import { RadarEmblem } from "@/components/brand/radar-emblem";
import { ArrowUpRight, BookmarkSimple, Cpu, MagnifyingGlass, Browser } from "@phosphor-icons/react";
import { useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import type { Product } from "@/types/api";
import { parseLastUpdatedLabel, type WeeklyTopSort } from "@/lib/api-client";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { countFavorites, openFavoritesPanel, subscribeFavorites } from "@/lib/favorites";
import {
  collectDirectionOptions,
  filterDirectionOptions,
  filterProducts,
  getDirectionLabel,
  getProductDirections,
  isHardware,
  productKey,
  sortProducts,
} from "@/lib/product-utils";

const PRODUCTS_PER_PAGE = 12;
const DARK_HORSE_COLLAPSE_LIMIT = 5;
const POPULAR_DIRECTION_LIMIT = 10;
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
  const [isDirectionSheetOpen, setIsDirectionSheetOpen] = useState(false);
  const [directionQuery, setDirectionQuery] = useState("");
  const listSentinelRef = useRef<HTMLDivElement | null>(null);
  const deferredDirectionQuery = useDeferredValue(directionQuery);

  useEffect(() => {
    const syncCount = () => setFavoritesCount(countFavorites());
    syncCount();
    return subscribeFavorites(syncCount);
  }, []);

  useEffect(() => {
    if (!isDirectionSheetOpen) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsDirectionSheetOpen(false);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isDirectionSheetOpen]);

  const productPool = useMemo(() => sortProducts(allProducts, sortBy), [allProducts, sortBy]);

  const filteredDarkHorses = useMemo(() => {
    return darkHorses.filter((product) => {
      if (contentTypeFilter === "all") return true;
      if (contentTypeFilter === "hardware") return isHardware(product);
      return !isHardware(product);
    });
  }, [contentTypeFilter, darkHorses]);

  const visibleDarkHorses = useMemo(() => {
    if (showAllDarkHorses) return filteredDarkHorses;
    return filteredDarkHorses.slice(0, DARK_HORSE_COLLAPSE_LIMIT);
  }, [filteredDarkHorses, showAllDarkHorses]);

  const visibleDarkHorseKeys = useMemo(() => {
    return new Set(visibleDarkHorses.map((product) => productKey(product)));
  }, [visibleDarkHorses]);

  const allDirectionOptions = useMemo(() => {
    const filtered = filterProducts(productPool, {
      tier: tierFilter,
      type: contentTypeFilter === "all" ? "all" : contentTypeFilter,
    });
    return collectDirectionOptions(filtered, locale);
  }, [contentTypeFilter, locale, productPool, tierFilter]);

  const popularDirections = useMemo(
    () => allDirectionOptions.slice(0, POPULAR_DIRECTION_LIMIT),
    [allDirectionOptions]
  );

  const filteredDirectionSheetOptions = useMemo(
    () => filterDirectionOptions(allDirectionOptions, deferredDirectionQuery),
    [allDirectionOptions, deferredDirectionQuery]
  );

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

    return directionMatched.filter((product) => !visibleDarkHorseKeys.has(productKey(product)));
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
  const activeDirectionLabel = activeDirectionFilter === "all" ? t("选择方向", "Choose a direction") : getDirectionLabel(activeDirectionFilter, locale);
  const heroSubtitle = t("从全球早期 AI 产品里，找到值得你多看一眼的那一个。看用途，追来源，亲手试。", "Find the early AI products worth a closer look. Understand the use case, follow the source, and try it for yourself.");

  const selectDirection = (value: string) => {
    setDirectionFilter(value);
    setCurrentPage(1);
    setIsDirectionSheetOpen(false);
  };

  return (
    <div className="home-root" data-vibe="briefing">
      <section className="hero briefing-hero">
        <div className="briefing-masthead">
          <span>THE INDEPENDENT AI PRODUCT BRIEF</span>
          <span>{t("全球视野 / 独立发现", "GLOBAL PERSPECTIVE / EARLY DISCOVERY")}</span>
        </div>
        <div className="hero-layout">
          <div className="hero-content">
            <p className="briefing-kicker"><span className="signal-dot" /> {t("给好奇的产品人", "FOR CURIOUS PRODUCT PEOPLE")}</p>
            <h1 className="hero-title">{t("在热闹之前，", "Before the hype.")}<br /><span>{t("看见下一匹黑马。", "Find the dark horse.")}</span></h1>
            <p className="hero-subtitle">{heroSubtitle}</p>
            <div className="briefing-actions">
              <a className="link-btn link-btn--primary" href="#darkhorseSection">{t("翻开本期观察", "Explore the brief")} <ArrowUpRight size={16} /></a>
              <Link className="briefing-text-link" href="/discover">{t("随机发现一款", "Surprise me")} <ArrowUpRight size={15} /></Link>
            </div>
          </div>
          <aside className="briefing-art" aria-label={t("黑马雷达品牌标识", "Darkhorse Radar brand mark")}>
            <RadarEmblem />
            <p>{t("潜力，往往先于共识。", "Potential precedes consensus.")}</p>
          </aside>
        </div>
        <div className="briefing-colophon">
          <span>{t("关注早期 · 每条附来源 · 可交互试用", "EARLY PRODUCTS · LINKED SOURCES · HANDS-ON DEMOS")}</span>
          <Link href="/content-sources">{t("我们如何发现黑马", "Our selection method")} <ArrowUpRight size={14} /></Link>
        </div>
      </section>

      <section className="section darkhorse-section" id="darkhorseSection">
        <div className="section-header section-header--tight">
          <h2 className="section-title">
            <span className="briefing-section-number">01</span>
            {isArchive ? t("黑马档案", "The dark horse archive") : t("本期黑马观察", "On our radar")}
          </h2>
          <p className="section-desc">
            {isArchive ? t("近期暂无新发现，以下保留历史研究供参考。请查看每条记录的日期与来源。", "No recent discoveries yet. Explore earlier research below, with dates and sources on every record.") : t("有明确用途、有来源可查的早期产品。", "Emerging products with a concrete use case and a source you can check.")}
          </p>
        </div>

        <div className="section-utility">
          <div className="section-utility__freshness" aria-live="polite">
            {freshnessLabel}
          </div>

          <div className="section-utility__controls">
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
              <Cpu size={14} /> {t("硬件", "Hardware")}
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
              <Browser size={14} /> {t("软件", "Software")}
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
            <p className="empty-state-text">{t("该筛选下暂无黑马产品。", "No dark horse products found for this filter.")}</p>
          </div>
        )}

        {filteredDarkHorses.length > DARK_HORSE_COLLAPSE_LIMIT ? (
          <div className="darkhorse-expand-row">
            <button className="load-more-btn" type="button" onClick={() => setShowAllDarkHorses((value) => !value)}>
              {showAllDarkHorses
                ? t("收起黑马列表", "Collapse dark horse list")
                : locale === "en-US"
                  ? `Show the rest (${filteredDarkHorses.length - DARK_HORSE_COLLAPSE_LIMIT})`
                  : `展开剩余黑马 (${filteredDarkHorses.length - DARK_HORSE_COLLAPSE_LIMIT} 款)`}
            </button>
          </div>
        ) : null}
      </section>

      <section className="section trending-section" id="trendingSection">
        <div className="section-header section-header--tight">
          <h2 className="section-title"><span className="briefing-section-number">02</span> {t("继续研究", "Keep exploring")}</h2>
          <p className="section-desc">
            {t("按方向找到与你正在做的事有关的产品。", "Find a product that connects to what you are working on.")}
          </p>
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
                <option value="composite">{t("发现价值", "Discovery score")}</option>
                <option value="trending">{t("热度", "Trending")}</option>
                <option value="recency">{t("最新收录", "Recently discovered")}</option>
              </select>
            </label>

            <button
              type="button"
              className={`tag-btn direction-trigger ${activeDirectionFilter === "all" ? "" : "active"}`}
              onClick={() => setIsDirectionSheetOpen(true)}
            >
              <MagnifyingGlass size={14} /> {activeDirectionLabel}
            </button>

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
            <p className="empty-state-text">{t("当前筛选下暂无更多推荐。", "No additional picks match this filter.")}</p>
          </div>
        )}

        {hasMore ? <div ref={listSentinelRef} className="picks-list__sentinel" aria-hidden="true" /> : null}
        <Link className="briefing-text-link" href="/search">{t("搜索完整产品档案", "Search the complete product archive")} <ArrowUpRight size={14} /></Link>
      </section>

      <footer className="section home-footer">
        <div className="home-footer__intro">
          <p className="home-footer__eyebrow"><HorseMark className="footer-brand-mark" />{t("黑马雷达", "Darkhorse Radar")}</p>
          <p className="home-footer__summary">
            {t(
              "给 PM 和产品团队一个更快的全球 AI 发现入口，先看值得注意的，再决定要不要深挖。",
              "A faster global AI discovery surface for PMs and product teams: scan the notable signals first, then decide what deserves deeper work."
            )}
          </p>
        </div>

        <div className="home-footer__links">
          <Link className="home-footer__link" href="/discover">
            {t("随机发现", "Discover")}
          </Link>
          <Link className="home-footer__link" href="/blog">
            {t("博客动态", "News")}
          </Link>
          <Link className="home-footer__link" href="/search">
            {t("搜索", "Search")}
          </Link>
        </div>

        <div className="home-footer__meta">
          <span>{freshnessLabel}</span>
          <span>{t("默认优先展示黑马与潜力股信号。", "Dark horses and rising stars surface first by default.")}</span>
        </div>
      </footer>

      {isDirectionSheetOpen ? (
        <div className="direction-sheet">
          <button
            type="button"
            className="direction-sheet__backdrop"
            aria-label={t("关闭方向筛选", "Close direction filter")}
            onClick={() => setIsDirectionSheetOpen(false)}
          />
          <div className="direction-sheet__panel" role="dialog" aria-modal="true" aria-label={t("方向筛选", "Direction filter")}>
            <div className="direction-sheet__header">
              <div>
                <h3>{t("更多方向", "More directions")}</h3>
                <p>{t("搜索并切换方向筛选。", "Search and switch the direction filter.")}</p>
              </div>
              <button type="button" className="direction-sheet__close" onClick={() => setIsDirectionSheetOpen(false)}>
                {t("关闭", "Close")}
              </button>
            </div>

            <div className="direction-sheet__popular">
              <span>{t("高频方向", "Popular directions")}</span>
              <div className="direction-sheet__popular-tags">
                <button
                  type="button"
                  className={`tag-btn ${activeDirectionFilter === "all" ? "active" : ""}`}
                  onClick={() => selectDirection("all")}
                >
                  {t("全部方向", "All directions")}
                </button>
                {popularDirections.map((option) => (
                  <button
                    key={`popular-${option.value}`}
                    type="button"
                    className={`tag-btn ${activeDirectionFilter === option.value ? "active" : ""}`}
                    onClick={() => selectDirection(option.value)}
                  >
                    {option.label} ({option.count})
                  </button>
                ))}
              </div>
            </div>

            <label className="direction-sheet__search">
              <span>{t("搜索方向", "Search directions")}</span>
              <input
                type="search"
                value={directionQuery}
                onChange={(event) => setDirectionQuery(event.target.value)}
                placeholder={t("输入 Agent、Healthcare、Robotics...", "Search Agent, Healthcare, Robotics...")}
                autoComplete="off"
              />
            </label>

            <div className="direction-sheet__list">
              <button
                type="button"
                className={`tag-btn ${activeDirectionFilter === "all" ? "active" : ""}`}
                onClick={() => selectDirection("all")}
              >
                {t("全部方向", "All directions")}
              </button>
              {filteredDirectionSheetOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={`tag-btn ${activeDirectionFilter === option.value ? "active" : ""}`}
                  onClick={() => selectDirection(option.value)}
                >
                  {option.label} ({option.count})
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
