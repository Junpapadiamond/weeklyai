"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { Cpu, Flame, Search, Sparkles } from "lucide-react";
import { useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import type { Product } from "@/types/api";
import type { SiteLocale } from "@/lib/locale";
import { parseLastUpdatedLabel, type WeeklyTopSort } from "@/lib/api-client";
import { SmartLogo } from "@/components/common/smart-logo";
import { FavoriteButton } from "@/components/favorites/favorite-button";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { countFavorites, openFavoritesPanel, subscribeFavorites } from "@/lib/favorites";
import {
  cleanDescription,
  collectDirectionOptions,
  filterDirectionOptions,
  filterProducts,
  formatCategories,
  getDirectionLabel,
  getLocalizedCountryName,
  getLocalizedProductDescription,
  getLocalizedProductWhyMatters,
  getProductWebsiteSearchUrl,
  getProductDirections,
  getProductScore,
  isHardware,
  isPlaceholderValue,
  isValidWebsite,
  normalizeWebsite,
  productKey,
  resolveProductCountry,
  sortProducts,
} from "@/lib/product-utils";

const HeroCanvas = dynamic(() => import("@/components/home/hero-canvas"), {
  ssr: false,
  loading: () => <div className="hero-canvas hero-canvas--loading" aria-hidden="true" />,
});

const PRODUCTS_PER_PAGE = 12;
const DARK_HORSE_COLLAPSE_LIMIT = 10;
const POPULAR_DIRECTION_LIMIT = 10;
const DEFAULT_WEEKLY_TOP_SORT: WeeklyTopSort = "composite";

type HomeClientProps = {
  darkHorses: Product[];
  allProducts: Product[];
  freshnessHoursAgo: number | null | undefined;
};

type ContentTypeFilter = "all" | "hardware" | "software";

function formatScore(score: number, locale: SiteLocale): string {
  if (score <= 0) return locale === "en-US" ? "Unrated" : "待评";
  if (locale === "en-US") {
    return Number.isInteger(score) ? `${score}/5` : `${score.toFixed(1)}/5`;
  }
  return Number.isInteger(score) ? `${score}分` : `${score.toFixed(1)}分`;
}

type HomeProductCardProps = {
  product: Product;
  highlighted?: boolean;
  rank: number;
  favoritable?: boolean;
};

function HomeProductCard({ product, highlighted = false, rank, favoritable = false }: HomeProductCardProps) {
  const { locale, t } = useSiteLocale();
  const detailId = encodeURIComponent(product._id || product.name);
  const score = getProductScore(product);
  const scoreLabel = formatScore(score, locale);
  const website = normalizeWebsite(product.website);
  const hasWebsite = isValidWebsite(website) && !product.needs_verification;
  const country = resolveProductCountry(product);
  const regionLabel = getLocalizedCountryName(country, locale);
  const fundingLabel = !isPlaceholderValue(product.funding_total) ? product.funding_total?.trim() : "";
  const summary =
    getLocalizedProductWhyMatters(product, locale)
    || cleanDescription(getLocalizedProductDescription(product, locale), locale)
    || t("产品摘要待补充", "Product summary pending");
  const websiteSearchUrl = getProductWebsiteSearchUrl(product.name, locale);

  const metadata = [
    country.flag ? `${country.flag} ${regionLabel}` : regionLabel,
    fundingLabel || t("融资待补充", "Funding pending"),
    scoreLabel,
  ].join(" · ");

  return (
    <article
      className={`darkhorse-spotlight-card ${highlighted ? "darkhorse-spotlight-card--leading" : ""} ${favoritable ? "darkhorse-spotlight-card--pick" : ""}`}
    >
      <div className="darkhorse-spotlight__body">
        <div className="darkhorse-spotlight__rank-wrap" aria-label={t("排名", "Rank")}>
          <span className="darkhorse-spotlight__rank">{String(rank).padStart(2, "0")}</span>
        </div>

        <SmartLogo
          key={`${product._id || product.name}-${product.logo_url || ""}-${product.logo || ""}-${product.website || ""}-${product.source_url || ""}`}
          className="darkhorse-spotlight__logo"
          name={product.name}
          logoUrl={product.logo_url}
          secondaryLogoUrl={product.logo}
          website={product.website}
          sourceUrl={product.source_url}
          size={64}
          loading={rank <= 3 ? "eager" : "lazy"}
        />

        <div className="darkhorse-spotlight__content">
          <header className="darkhorse-spotlight__header">
            <div className="darkhorse-spotlight__header-main">
              <h3 className="darkhorse-spotlight__title">{product.name}</h3>
              <p className="darkhorse-spotlight__categories">{formatCategories(product, locale)}</p>
            </div>
            {favoritable ? <FavoriteButton product={product} className="darkhorse-spotlight__favorite" /> : null}
          </header>

          <p className="darkhorse-spotlight__meta-line" title={regionLabel}>
            {metadata}
          </p>

          <p className="darkhorse-spotlight__why">{summary}</p>

          <footer className="darkhorse-spotlight__footer">
            <Link href={`/product/${detailId}`} className="link-btn link-btn--card link-btn--card-primary">
              {t("详情", "Details")}
            </Link>
            {hasWebsite ? (
              <a className="link-btn link-btn--card" href={website} target="_blank" rel="noopener noreferrer">
                {t("官网", "Website")}
              </a>
            ) : (
              <a
                className="pending-tag pending-tag--action"
                href={websiteSearchUrl}
                target="_blank"
                rel="noopener noreferrer"
                title={t("点击跳转 Google 搜索官网", "Open Google search for the official website")}
              >
                {t("官网待验证", "Website pending verification")}
              </a>
            )}
          </footer>
        </div>
      </div>
    </article>
  );
}

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
  const [isMobileHero, setIsMobileHero] = useState(false);
  const [showHeroCanvas, setShowHeroCanvas] = useState(false);
  const heroArtRef = useRef<HTMLDivElement | null>(null);
  const listSentinelRef = useRef<HTMLDivElement | null>(null);
  const deferredDirectionQuery = useDeferredValue(directionQuery);

  useEffect(() => {
    const syncCount = () => setFavoritesCount(countFavorites());
    syncCount();
    return subscribeFavorites(syncCount);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const media = window.matchMedia("(max-width: 760px)");
    const update = () => setIsMobileHero(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    if (isMobileHero) return;

    const node = heroArtRef.current;
    if (!node) return;
    if (typeof IntersectionObserver === "undefined") {
      const rafId = window.requestAnimationFrame(() => setShowHeroCanvas(true));
      return () => window.cancelAnimationFrame(rafId);
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setShowHeroCanvas(true);
          observer.disconnect();
        }
      },
      { rootMargin: "120px" }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [isMobileHero]);

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
  const isEnglish = locale === "en-US";
  const heroSubtitle = isEnglish
    ? "Spend 5 minutes each week on the most promising breakouts, then widen out to the broader AI product board."
    : "每周 5 分钟，看完最值得关注的黑马，再延伸到更大的 AI 产品盘面。";

  const activeDirectionLabel =
    activeDirectionFilter === "all" ? t("全部方向", "All directions") : getDirectionLabel(activeDirectionFilter, locale);

  const shouldRenderHeroCanvas = !isMobileHero && showHeroCanvas;

  const selectDirection = (value: string) => {
    setDirectionFilter(value);
    setCurrentPage(1);
    setIsDirectionSheetOpen(false);
  };

  return (
    <div className="home-root" data-vibe="experimental">
      <section className="hero">
        <div className="hero-art" ref={heroArtRef}>
          {shouldRenderHeroCanvas ? (
            <HeroCanvas />
          ) : !isMobileHero ? (
            <div className="hero-canvas hero-canvas--loading" aria-hidden="true" />
          ) : null}
        </div>
        <div className="hero-layout">
          <div className={`hero-content ${isEnglish ? "hero-content--en" : ""}`}>
            <h1 className={`hero-title ${isEnglish ? "hero-title--en" : ""}`}>
              {isEnglish ? (
                <>
                  <span className="hero-title__line">Discover the latest</span>
                  <span className="hero-title__line">
                    global <span className="gradient-text">AI products</span>
                  </span>
                </>
              ) : (
                <>
                  发现全球最新 <span className="gradient-text">AI 产品</span>
                </>
              )}
            </h1>
            <p className={`hero-subtitle ${isEnglish ? "hero-subtitle--en" : ""}`}>
              {heroSubtitle}
            </p>
          </div>
        </div>
      </section>

      <section className="section darkhorse-section" id="darkhorseSection">
        <div className="section-header section-header--tight">
          <h2 className="section-title">
            <span className="title-icon">
              <Flame size={18} />
            </span>
            {t("本周黑马", "Dark Horses This Week")}
          </h2>
          <p className="section-desc">
            {t("先看最值得盯住的 4-5 分产品，减少首页噪声。", "Start with the 4-5 score breakouts worth tracking first.")}
          </p>
        </div>

        <div className="section-utility">
          <div className="section-utility__freshness" aria-live="polite">
            {freshnessLabel}
          </div>

          <div className="section-utility__controls">
            <button
              className={`filter-btn ${contentTypeFilter === "all" ? "active" : ""}`}
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
              type="button"
              onClick={() => {
                setContentTypeFilter("software");
                setCurrentPage(1);
                setShowAllDarkHorses(false);
              }}
            >
              <Sparkles size={14} /> {t("软件", "Software")}
            </button>
          </div>
        </div>

        {visibleDarkHorses.length ? (
          <div className="darkhorse-spotlight-grid">
            {visibleDarkHorses.map((product, index) => (
              <HomeProductCard
                key={product._id || product.name}
                product={product}
                highlighted={index < 3}
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
          <h2 className="section-title">{t("更多推荐", "More Picks")}</h2>
          <p className="section-desc">
            {t("黑马之外，继续看潜力股和剩余高信号产品。", "Move beyond the hero picks into the remaining high-signal products and rising stars.")}
          </p>
        </div>

        <div className="list-controls list-controls--compact">
          <div className="tier-tabs">
            <button
              className={`tier-tab ${tierFilter === "all" ? "active" : ""}`}
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
                <option value="composite">🧠 {t("综合", "Composite")}</option>
                <option value="trending">🔥 {t("热度", "Trending")}</option>
                <option value="recency">🕐 {t("时间", "Recency")}</option>
              </select>
            </label>

            <button
              type="button"
              className={`tag-btn direction-trigger ${activeDirectionFilter === "all" ? "" : "active"}`}
              onClick={() => setIsDirectionSheetOpen(true)}
            >
              <Search size={14} /> {activeDirectionLabel}
            </button>

            <button
              className="favorites-toggle"
              type="button"
              aria-label={t("打开收藏夹", "Open favorites")}
              onClick={() => openFavoritesPanel("product")}
            >
              ❤️ {favoritesCount}
            </button>
          </div>
        </div>

        {visibleProducts.length ? (
          <div className="darkhorse-spotlight-grid picks-grid">
            {visibleProducts.map((product, index) => (
              <HomeProductCard
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
      </section>

      <footer className="section home-footer">
        <div className="home-footer__intro">
          <p className="home-footer__eyebrow">WeeklyAI</p>
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
