"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { Cpu, Flame, Newspaper, Sparkles, Star } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import useSWR from "swr";
import type { Product } from "@/types/api";
import { ProductCard } from "@/components/product/product-card";
import { getWeeklyTopClient } from "@/lib/client-home-api";
import { addProductFavorite, countFavorites, openFavoritesPanel, subscribeFavorites } from "@/lib/favorites";
import { filterProducts, getDirectionLabel, getProductDirections, isHardware, sortProducts } from "@/lib/product-utils";

const HeroCanvas = dynamic(() => import("@/components/home/hero-canvas"), {
  ssr: false,
  loading: () => <div className="hero-canvas hero-canvas--loading" aria-hidden="true" />,
});

const DiscoveryDeck = dynamic(() => import("@/components/home/discovery-deck"), {
  ssr: false,
  loading: () => <div className="swipe-card is-active">加载探索卡片中...</div>,
});

const PRODUCTS_PER_PAGE = 12;

type HomeClientProps = {
  darkHorses: Product[];
  allProducts: Product[];
  freshnessLabel: string;
};

export function HomeClient({ darkHorses, allProducts, freshnessLabel }: HomeClientProps) {
  const [darkFilter, setDarkFilter] = useState<"all" | "hardware" | "software">("all");
  const [tierFilter, setTierFilter] = useState<"all" | "darkhorse" | "rising">("all");
  const [typeFilter, setTypeFilter] = useState<"all" | "software" | "hardware">("all");
  const [directionFilter, setDirectionFilter] = useState("all");
  const [sortBy, setSortBy] = useState<"score" | "date" | "funding">("score");
  const [currentPage, setCurrentPage] = useState(1);
  const [favoritesCount, setFavoritesCount] = useState(0);

  const [shouldLoadFullProducts, setShouldLoadFullProducts] = useState(false);

  const discoverSectionRef = useRef<HTMLElement | null>(null);
  const trendingSectionRef = useRef<HTMLElement | null>(null);

  const { data: fullProducts, isLoading: isHydratingAllProducts } = useSWR(
    shouldLoadFullProducts ? "home-full-products" : null,
    () => getWeeklyTopClient(0),
    {
      revalidateOnFocus: false,
      dedupingInterval: 60_000,
    }
  );

  useEffect(() => {
    const targets = [discoverSectionRef.current, trendingSectionRef.current].filter(Boolean);
    if (!targets.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setShouldLoadFullProducts(true);
          observer.disconnect();
        }
      },
      { rootMargin: "260px 0px" }
    );

    targets.forEach((target) => observer.observe(target as Element));
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const syncCount = () => setFavoritesCount(countFavorites());
    syncCount();
    return subscribeFavorites(syncCount);
  }, []);

  function addFavorite(product: Product) {
    if (addProductFavorite(product)) {
      setFavoritesCount(countFavorites());
    }
  }

  const productPool = useMemo(() => {
    if (fullProducts && fullProducts.length > allProducts.length) {
      return fullProducts;
    }
    return allProducts;
  }, [allProducts, fullProducts]);

  const hasLoadedAllProducts = !!fullProducts && fullProducts.length > allProducts.length;

  const filteredDarkHorses = useMemo(() => {
    return darkHorses.filter((product) => {
      if (darkFilter === "all") return true;
      if (darkFilter === "hardware") return isHardware(product);
      return !isHardware(product);
    });
  }, [darkFilter, darkHorses]);

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
    const directionalFiltered =
      activeDirectionFilter === "all"
        ? filtered
        : filtered.filter((product) => getProductDirections(product).includes(activeDirectionFilter));
    return sortProducts(directionalFiltered, sortBy);
  }, [activeDirectionFilter, productPool, sortBy, tierFilter, typeFilter]);

  const visibleProducts = useMemo(() => {
    return trendingFiltered.slice(0, currentPage * PRODUCTS_PER_PAGE);
  }, [currentPage, trendingFiltered]);

  const hasMore = visibleProducts.length < trendingFiltered.length;

  const signalStats = useMemo(() => {
    const darkhorseCount = productPool.filter((product) => (product.dark_horse_index ?? 0) >= 4).length;
    const hardwareCount = productPool.filter((product) => isHardware(product)).length;
    const regionCount = new Set(productPool.map((product) => product.region).filter(Boolean)).size;

    return {
      total: productPool.length,
      darkhorseCount,
      hardwareCount,
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
            <h1 className="hero-title">发现全球最新AI产品</h1>
            <p className="hero-subtitle">黑马与潜力股，每周更新。</p>
            <div className="data-freshness" aria-live="polite">
              {freshnessLabel}
            </div>
            <div className="hero-stats" role="list" aria-label="本期信号概览">
              <div className="hero-stat" role="listitem">
                <span className="hero-stat__label">样本池</span>
                <strong className="hero-stat__value">{signalStats.total}</strong>
              </div>
              <div className="hero-stat" role="listitem">
                <span className="hero-stat__label">黑马候选</span>
                <strong className="hero-stat__value">{signalStats.darkhorseCount}</strong>
              </div>
              <div className="hero-stat" role="listitem">
                <span className="hero-stat__label">硬件占比</span>
                <strong className="hero-stat__value">{signalStats.hardwareCount}</strong>
              </div>
              <div className="hero-stat" role="listitem">
                <span className="hero-stat__label">覆盖地区</span>
                <strong className="hero-stat__value">{signalStats.regionCount}</strong>
              </div>
            </div>
            <p className="hero-signal">
              本周偏热：<span>Agent 原生工具</span> · <span>AI 硬件新形态</span> · <span>社交一手信号</span>
            </p>
          </div>
        </div>
      </section>

      <section className="section darkhorse-section" id="darkhorseSection">
        <div className="section-header">
          <h2 className="section-title">
            <span className="title-icon">
              <Flame size={18} />
            </span>
            本周黑马 <span className="score-badge score-badge--5">4-5分</span>
          </h2>
          <p className="section-desc">不是最吵的项目，而是最可能突然起飞的项目。</p>
          <p className="section-micro-note">优先看 4-5 分，按硬件/软件切流减少信息噪声。</p>
        </div>

        <div className="darkhorse-filters">
          <button className={`filter-btn ${darkFilter === "all" ? "active" : ""}`} type="button" onClick={() => setDarkFilter("all")}>
            全部
          </button>
          <button
            className={`filter-btn ${darkFilter === "hardware" ? "active" : ""}`}
            type="button"
            onClick={() => setDarkFilter("hardware")}
          >
            <Cpu size={14} /> 硬件
          </button>
          <button
            className={`filter-btn ${darkFilter === "software" ? "active" : ""}`}
            type="button"
            onClick={() => setDarkFilter("software")}
          >
            <Sparkles size={14} /> 软件
          </button>
        </div>

        <div className="products-grid">
          {filteredDarkHorses.length ? (
            filteredDarkHorses.map((product) => (
              <ProductCard key={product._id || product.name} product={product} compact />
            ))
          ) : (
            <div className="empty-state">
              <p className="empty-state-text">该筛选下暂无黑马产品。</p>
            </div>
          )}
        </div>
      </section>

      <section className="section discovery-section" id="discoverSection" ref={discoverSectionRef}>
        <div className="section-header">
          <h2 className="section-title">
            <span className="title-icon">
              <Star size={18} />
            </span>
            快速发现
          </h2>
          <p className="section-desc">向右收藏，向左跳过，候选会越来越准。</p>
          <p className="section-micro-note">收藏行为会直接影响下一轮候选排序。</p>
        </div>

        <DiscoveryDeck key={`deck-${productPool.length}`} products={productPool} onLike={addFavorite} />
      </section>

      <section className="section trending-section" id="trendingSection" ref={trendingSectionRef}>
        <div className="section-header">
          <h2 className="section-title">更多推荐</h2>
          <p className="section-desc">黑马 (4-5分) + 潜力股 (2-3分)</p>
          <p className="section-micro-note">默认按热度排序，你可以切换到融资或时间线。</p>
          {shouldLoadFullProducts && isHydratingAllProducts && !hasLoadedAllProducts ? (
            <p className="section-desc">正在补全完整产品池...</p>
          ) : null}
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
                <option value="score">🔥 热度</option>
                <option value="date">🕐 最新</option>
                <option value="funding">💰 融资</option>
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
          {visibleProducts.map((product) => (
            <ProductCard key={product._id || product.name} product={product} />
          ))}
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
        <Link className="link-banner" href="/blog">
          <Newspaper size={18} /> 查看博客和动态信号
        </Link>
      </section>
    </div>
  );
}
