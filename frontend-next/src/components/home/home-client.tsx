"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { ChevronDown, ChevronUp, Cpu, Flame, Newspaper, Sparkles } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Product } from "@/types/api";
import type { WeeklyTopSort } from "@/lib/api-client";
import { ChatBar } from "@/components/chat/chat-bar";
import { SmartLogo } from "@/components/common/smart-logo";
import { ProductCard } from "@/components/product/product-card";
import { countFavorites, openFavoritesPanel, subscribeFavorites } from "@/lib/favorites";
import {
  cleanDescription,
  filterProducts,
  formatCategories,
  getDirectionLabel,
  getProductDirections,
  getProductScore,
  isHardware,
  isPlaceholderValue,
  isValidWebsite,
  normalizeWebsite,
  resolveProductCountry,
  sortProducts,
} from "@/lib/product-utils";

const HeroCanvas = dynamic(() => import("@/components/home/hero-canvas"), {
  ssr: false,
  loading: () => <div className="hero-canvas hero-canvas--loading" aria-hidden="true" />,
});

const PRODUCTS_PER_PAGE = 12;
const DARK_HORSE_COLLAPSE_LIMIT = 10;
const DEFAULT_WEEKLY_TOP_SORT: WeeklyTopSort = "composite";

type HomeClientProps = {
  darkHorses: Product[];
  allProducts: Product[];
  freshnessLabel: string;
};

function formatScore(score: number): string {
  if (score <= 0) return "待评";
  return Number.isInteger(score) ? `${score}分` : `${score.toFixed(1)}分`;
}

function getScoreBadgeClass(score: number): string {
  if (score >= 5) return "score-badge--5";
  if (score >= 4) return "score-badge--4";
  return "score-badge--3";
}

function parseDateValue(value?: string): Date | null {
  if (!value) return null;
  const timestamp = new Date(value).getTime();
  if (!Number.isFinite(timestamp)) return null;
  return new Date(timestamp);
}

function getCurrentWeekStart(now: Date): Date {
  const weekStart = new Date(now);
  const day = weekStart.getDay();
  const offset = day === 0 ? -6 : 1 - day;
  weekStart.setDate(weekStart.getDate() + offset);
  weekStart.setHours(0, 0, 0, 0);
  return weekStart;
}

type DarkHorseSpotlightCardProps = {
  product: Product;
};

function DarkHorseSpotlightCard({ product }: DarkHorseSpotlightCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [canExpand, setCanExpand] = useState(false);
  const whyMattersRef = useRef<HTMLParagraphElement | null>(null);
  const detailId = encodeURIComponent(product._id || product.name);
  const score = getProductScore(product);
  const scoreLabel = formatScore(score);
  const description = cleanDescription(product.description);
  const website = normalizeWebsite(product.website);
  const hasWebsite = isValidWebsite(website);
  const country = resolveProductCountry(product);
  const regionFlag = country.flag || "?";
  const regionLabel = country.unknown ? "Unknown" : country.name;
  const fundingLabel = !isPlaceholderValue(product.funding_total) ? product.funding_total?.trim() : "";

  useEffect(() => {
    const node = whyMattersRef.current;
    if (!node || !product.why_matters) return;

    const checkOverflow = () => {
      setCanExpand(node.scrollHeight - node.clientHeight > 2);
    };

    const rafId = window.requestAnimationFrame(checkOverflow);
    if (typeof ResizeObserver === "undefined") {
      return () => window.cancelAnimationFrame(rafId);
    }

    const observer = new ResizeObserver(checkOverflow);
    observer.observe(node);
    return () => {
      window.cancelAnimationFrame(rafId);
      observer.disconnect();
    };
  }, [product.why_matters, expanded]);

  return (
    <article className="darkhorse-spotlight-card">
      <span className="darkhorse-spotlight__region-flag-corner" aria-hidden="true" title={regionLabel}>
        {regionFlag}
      </span>
      <div className="darkhorse-spotlight__body">
        <SmartLogo
          key={`${product._id || product.name}-${product.logo_url || ""}-${product.logo || ""}-${product.website || ""}-${product.source_url || ""}`}
          className="darkhorse-spotlight__logo"
          name={product.name}
          logoUrl={product.logo_url}
          secondaryLogoUrl={product.logo}
          website={product.website}
          sourceUrl={product.source_url}
          size={64}
        />

        <div className="darkhorse-spotlight__content">
          <header className="darkhorse-spotlight__header">
            <h3 className="darkhorse-spotlight__title">{product.name}</h3>
            <p className="darkhorse-spotlight__categories">{formatCategories(product)}</p>
          </header>

          <p className="darkhorse-spotlight__description">{description}</p>

          <div className="darkhorse-spotlight__badges">
            <span className="darkhorse-spotlight__region-tag">{regionLabel}</span>
            <span className={`darkhorse-spotlight__badge darkhorse-spotlight__badge--funding ${fundingLabel ? "" : "is-muted"}`}>
              {fundingLabel || "融资待补充"}
            </span>
            <span className={`score-badge ${getScoreBadgeClass(score)} darkhorse-spotlight__badge darkhorse-spotlight__badge--score`}>
              {scoreLabel}
            </span>
          </div>

          <div className="darkhorse-spotlight__why-wrap">
            <p ref={whyMattersRef} className={`darkhorse-spotlight__why ${expanded ? "is-expanded" : ""}`}>
              {product.why_matters || "why_matters 待补充"}
            </p>
            {canExpand ? (
              <button
                className="darkhorse-spotlight__expand-btn"
                type="button"
                onClick={() => setExpanded((value) => !value)}
                aria-expanded={expanded}
              >
                {expanded ? (
                  <>
                    <ChevronUp size={14} /> 收起
                  </>
                ) : (
                  <>
                    <ChevronDown size={14} /> 展开
                  </>
                )}
              </button>
            ) : null}
          </div>

          <footer className="darkhorse-spotlight__footer">
            <Link href={`/product/${detailId}`} className="link-btn link-btn--card link-btn--card-primary">
              详情
            </Link>
            {hasWebsite ? (
              <a className="link-btn link-btn--card" href={website} target="_blank" rel="noopener noreferrer">
                官网
              </a>
            ) : (
              <span className="pending-tag">官网待验证</span>
            )}
          </footer>
        </div>
      </div>
    </article>
  );
}

export function HomeClient({ darkHorses, allProducts, freshnessLabel }: HomeClientProps) {
  const [darkFilter, setDarkFilter] = useState<"all" | "hardware" | "software">("all");
  const [tierFilter, setTierFilter] = useState<"all" | "darkhorse" | "rising">("all");
  const [typeFilter, setTypeFilter] = useState<"all" | "software" | "hardware">("all");
  const [directionFilter, setDirectionFilter] = useState("all");
  const [sortBy, setSortBy] = useState<WeeklyTopSort>(DEFAULT_WEEKLY_TOP_SORT);
  const [currentPage, setCurrentPage] = useState(1);
  const [favoritesCount, setFavoritesCount] = useState(0);
  const [showAllDarkHorses, setShowAllDarkHorses] = useState(false);

  useEffect(() => {
    const syncCount = () => setFavoritesCount(countFavorites());
    syncCount();
    return subscribeFavorites(syncCount);
  }, []);

  const productPool = useMemo(() => sortProducts(allProducts, sortBy), [allProducts, sortBy]);

  const filteredDarkHorses = useMemo(() => {
    return darkHorses.filter((product) => {
      if (darkFilter === "all") return true;
      if (darkFilter === "hardware") return isHardware(product);
      return !isHardware(product);
    });
  }, [darkFilter, darkHorses]);

  const visibleDarkHorses = useMemo(() => {
    if (showAllDarkHorses) return filteredDarkHorses;
    return filteredDarkHorses.slice(0, DARK_HORSE_COLLAPSE_LIMIT);
  }, [filteredDarkHorses, showAllDarkHorses]);

  const directionOptions = useMemo(() => {
    const filtered = filterProducts(productPool, {
      tier: tierFilter,
      type: typeFilter,
    });
    const counts = new Map<string, number>();

    for (const product of filtered) {
      for (const direction of getProductDirections(product)) {
        counts.set(direction, (counts.get(direction) || 0) + 1);
      }
    }

    return [...counts.entries()]
      .map(([value, count]) => ({
        value,
        count,
        label: getDirectionLabel(value) || value,
      }))
      .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, "zh-CN"));
  }, [productPool, tierFilter, typeFilter]);

  const activeDirectionFilter =
    directionFilter === "all" || directionOptions.some((option) => option.value === directionFilter)
      ? directionFilter
      : "all";

  const trendingFiltered = useMemo(() => {
    const filtered = filterProducts(productPool, {
      tier: tierFilter,
      type: typeFilter,
    });
    return activeDirectionFilter === "all"
      ? filtered
      : filtered.filter((product) => getProductDirections(product).includes(activeDirectionFilter));
  }, [activeDirectionFilter, productPool, tierFilter, typeFilter]);

  const visibleProducts = useMemo(() => {
    return trendingFiltered.slice(0, currentPage * PRODUCTS_PER_PAGE);
  }, [currentPage, trendingFiltered]);

  const hasMore = visibleProducts.length < trendingFiltered.length;

  const signalStats = useMemo(() => {
    const now = new Date();
    const weekStart = getCurrentWeekStart(now).getTime();
    const nowTs = now.getTime();
    const weekNewCount = productPool.filter((product) => {
      const discovered = parseDateValue(product.discovered_at);
      if (!discovered) return false;
      const ts = discovered.getTime();
      return ts >= weekStart && ts <= nowTs;
    }).length;
    const fundedCount = productPool.filter((product) => !isPlaceholderValue(product.funding_total)).length;
    const regionCount = new Set(productPool.map((product) => product.region).filter(Boolean)).size;

    return {
      total: productPool.length,
      weekNewCount,
      fundedCount,
      regionCount,
    };
  }, [productPool]);

  return (
    <div className="home-root" data-vibe="experimental">
      <section className="hero">
        <div className="hero-art">
          <HeroCanvas />
        </div>
        <div className="hero-layout">
          <div className="hero-content">
            <div className="hero-kicker">global signal board · weeklyai</div>
            <h1 className="hero-title">
              发现全球最新<span className="gradient-text">AI产品</span>
            </h1>
            <p className="hero-subtitle">每周 5 分钟，看完全球 AI 领域最值得关注的新产品</p>
            <div className="data-freshness" aria-live="polite">
              {freshnessLabel}
            </div>
            <div className="hero-stats" role="list" aria-label="本期信号概览">
              <div className="hero-stat" role="listitem">
                <span className="hero-stat__label">本周新增</span>
                <strong className="hero-stat__value">{signalStats.weekNewCount} 款</strong>
              </div>
              <div className="hero-stat" role="listitem">
                <span className="hero-stat__label">获得融资</span>
                <strong className="hero-stat__value">{signalStats.fundedCount} 款</strong>
              </div>
              <div className="hero-stat" role="listitem">
                <span className="hero-stat__label">覆盖地区</span>
                <strong className="hero-stat__value">{signalStats.regionCount} 个</strong>
              </div>
              <div className="hero-stat" role="listitem">
                <span className="hero-stat__label">累计收录</span>
                <strong className="hero-stat__value">{signalStats.total} 款</strong>
              </div>
            </div>
            <p className="hero-signal">
              本周偏热：<span>Agent 原生工具</span> · <span>AI 硬件新形态</span> · <span>社交一手信号</span>
            </p>
          </div>
        </div>
        <div className="hero-chat-slot">
          <ChatBar />
        </div>
      </section>

      <section className="section darkhorse-section" id="darkhorseSection">
        <div className="section-header">
          <h2 className="section-title">
            <span className="title-icon">
              <Flame size={18} />
            </span>
            本周黑马 <span className="score-badge score-badge--4">4-5分</span>
          </h2>
          <p className="section-desc">不是最吵的项目，而是最可能突然起飞的项目。</p>
          <p className="section-micro-note">优先看 4-5 分，按硬件/软件切流减少信息噪声。</p>
        </div>

        <div className="darkhorse-filters">
          <button
            className={`filter-btn ${darkFilter === "all" ? "active" : ""}`}
            type="button"
            onClick={() => {
              setDarkFilter("all");
              setShowAllDarkHorses(false);
            }}
          >
            全部
          </button>
          <button
            className={`filter-btn ${darkFilter === "hardware" ? "active" : ""}`}
            type="button"
            onClick={() => {
              setDarkFilter("hardware");
              setShowAllDarkHorses(false);
            }}
          >
            <Cpu size={14} /> 硬件
          </button>
          <button
            className={`filter-btn ${darkFilter === "software" ? "active" : ""}`}
            type="button"
            onClick={() => {
              setDarkFilter("software");
              setShowAllDarkHorses(false);
            }}
          >
            <Sparkles size={14} /> 软件
          </button>
        </div>

        <div className="darkhorse-spotlight-grid">
          {visibleDarkHorses.length ? (
            visibleDarkHorses.map((product) => (
              <DarkHorseSpotlightCard key={product._id || product.name} product={product} />
            ))
          ) : (
            <div className="empty-state">
              <p className="empty-state-text">该筛选下暂无黑马产品。</p>
            </div>
          )}
        </div>

        {filteredDarkHorses.length > DARK_HORSE_COLLAPSE_LIMIT ? (
          <div className="darkhorse-expand-row">
            <button className="load-more-btn" type="button" onClick={() => setShowAllDarkHorses((value) => !value)}>
              {showAllDarkHorses ? "收起" : `展开更多 (${filteredDarkHorses.length - DARK_HORSE_COLLAPSE_LIMIT} 款)`}
            </button>
          </div>
        ) : null}
      </section>

      <section className="section trending-section" id="trendingSection">
        <div className="section-header">
          <h2 className="section-title">更多推荐</h2>
          <p className="section-desc">黑马 (4-5分) + 潜力股 (2-3分)</p>
          <p className="section-micro-note">默认按综合排序（热度 + 新鲜度），可切换热度或时间。</p>
        </div>

        <div className="list-controls">
          <div className="tier-tabs">
            <button
              className={`tier-tab ${tierFilter === "all" ? "active" : ""}`}
              type="button"
              onClick={() => {
                setTierFilter("all");
                setCurrentPage(1);
              }}
            >
              全部
            </button>
            <button
              className={`tier-tab ${tierFilter === "darkhorse" ? "active" : ""}`}
              type="button"
              onClick={() => {
                setTierFilter("darkhorse");
                setCurrentPage(1);
              }}
            >
              黑马
            </button>
            <button
              className={`tier-tab ${tierFilter === "rising" ? "active" : ""}`}
              type="button"
              onClick={() => {
                setTierFilter("rising");
                setCurrentPage(1);
              }}
            >
              潜力股
            </button>
          </div>

          <div className="controls-right">
            <label>
              排序
              <select
                value={sortBy}
                onChange={(event) => {
                  setSortBy(event.target.value as typeof sortBy);
                  setCurrentPage(1);
                }}
              >
                <option value="composite">🧠 综合</option>
                <option value="trending">🔥 热度</option>
                <option value="recency">🕐 时间</option>
              </select>
            </label>
            <label>
              一级分类
              <select
                value={typeFilter}
                onChange={(event) => {
                  setTypeFilter(event.target.value as typeof typeFilter);
                  setDirectionFilter("all");
                  setCurrentPage(1);
                }}
              >
                <option value="all">全部</option>
                <option value="software">软件</option>
                <option value="hardware">硬件</option>
              </select>
            </label>
            <label>
              二级方向
              <select
                value={activeDirectionFilter}
                onChange={(event) => {
                  setDirectionFilter(event.target.value);
                  setCurrentPage(1);
                }}
              >
                <option value="all">全部方向</option>
                {directionOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label} ({option.count})
                  </option>
                ))}
              </select>
            </label>
            <button
              className="favorites-toggle"
              type="button"
              aria-label="打开收藏夹"
              onClick={() => openFavoritesPanel("product")}
            >
              ❤️ {favoritesCount}
            </button>
          </div>
        </div>

        <div className="products-grid">
          {visibleProducts.map((product) => <ProductCard key={product._id || product.name} product={product} />)}
        </div>

        {hasMore ? (
          <div className="load-more-container">
            <button className="load-more-btn" type="button" onClick={() => setCurrentPage((value) => value + 1)}>
              加载更多
            </button>
          </div>
        ) : null}
      </section>

      <section className="section section--linkout">
        <Link className="link-banner" href="/discover">
          🎲 随机发现产品 →
        </Link>
        <Link className="link-banner" href="/blog">
          <Newspaper size={18} /> 查看博客和动态信号
        </Link>
      </section>
    </div>
  );
}
