"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { Dice5, Home } from "lucide-react";
import { useEffect, useState } from "react";
import type { Product } from "@/types/api";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { addProductFavorite, countFavorites, openFavoritesPanel, subscribeFavorites } from "@/lib/favorites";

const DiscoveryDeck = dynamic(() => import("@/components/home/discovery-deck"), {
  ssr: false,
  loading: () => <div className="swipe-card is-active">Loading cards...</div>,
});

type DiscoverClientProps = {
  products: Product[];
};

export function DiscoverClient({ products }: DiscoverClientProps) {
  const { t } = useSiteLocale();
  const [favoritesCount, setFavoritesCount] = useState(0);

  useEffect(() => {
    const sync = () => setFavoritesCount(countFavorites());
    sync();
    return subscribeFavorites(sync);
  }, []);

  function addFavorite(product: Product) {
    if (addProductFavorite(product)) {
      setFavoritesCount(countFavorites());
    }
  }

  return (
    <section className="section discover-page">
      <div className="section-header">
        <h1 className="section-title">
          <span className="title-icon">
            <Dice5 size={18} />
          </span>
          {t("随机发现", "Discover")}
        </h1>
        <p className="section-desc">
          {t("向右收藏，向左跳过，5 分钟筛出今天值得关注的新产品。", "Swipe right to save, left to skip. Find today's most relevant products in 5 minutes.")}
        </p>
        <p className="section-micro-note">
          {t("首次访问会显示手势引导；滑动记录会在 7 天后自动重置。", "Gesture tips appear on first visit; swipe history resets after 7 days.")}
        </p>
      </div>

      <div className="list-controls discover-page__controls">
        <button className="favorites-toggle" type="button" aria-label={t("打开收藏夹", "Open favorites")} onClick={() => openFavoritesPanel("product")}>
          ❤️ {favoritesCount}
        </button>
        <Link className="link-btn" href="/">
          <Home size={14} /> {t("返回首页", "Back to home")}
        </Link>
      </div>

      {products.length ? (
        <DiscoveryDeck key={`discover-${products.length}`} products={products} onLike={addFavorite} />
      ) : (
        <div className="empty-state">
          <p className="empty-state-text">{t("暂无可探索产品，请稍后再试。", "No products available to explore right now. Please try again later.")}</p>
        </div>
      )}
    </section>
  );
}
