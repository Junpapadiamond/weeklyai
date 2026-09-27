"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { BookmarkSimple, House } from "@phosphor-icons/react";
import { useEffect, useState } from "react";
import type { Product } from "@/types/api";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { addProductFavorite, countFavorites, openFavoritesPanel, subscribeFavorites } from "@/lib/favorites";

const DiscoveryDeck = dynamic(() => import("@/components/home/discovery-deck"), {
  ssr: false,
  loading: () => <div className="discover-skeleton" aria-busy="true"><div className="discover-skeleton__card"><div className="discover-skeleton__topline" /><div className="discover-skeleton__line discover-skeleton__line--lg" /><div className="discover-skeleton__line" /></div></div>,
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
        <p className="briefing-kicker">{t("换个方式找产品", "THE SERENDIPITY FILE / DISCOVER")}</p>
        <h1 className="section-title">
          {t("随便看看", "Discover")}
        </h1>
        <p className="section-desc">
          {t("每次认识一款新产品。感兴趣就右滑收藏，不感兴趣就左滑跳过。", "Swipe right to save, left to skip. Find an idea worth following in the product archive.")}
        </p>
        <p className="section-micro-note">
          {t("也可以点击下方按钮操作，收藏的产品随时可在收藏夹查看。", "Gesture tips appear on first visit; swipe history resets after 7 days.")}
        </p>
      </div>

      <div className="list-controls discover-page__controls">
        <button className="favorites-toggle" type="button" aria-label={t("打开收藏夹", "Open favorites")} onClick={() => openFavoritesPanel("product")}>
          <BookmarkSimple size={17} aria-hidden="true" /> {favoritesCount}
        </button>
        <Link className="link-btn" href="/">
          <House size={14} /> {t("返回首页", "Back to home")}
        </Link>
      </div>

      {products.length ? (
        <DiscoveryDeck key={`discover-${products.length}`} products={products} onLike={addFavorite} />
      ) : (
        <div className="empty-state">
          <p className="empty-state-text">{t("暂时没有更多产品，过会儿再来看看。", "No products available to explore right now. Please try again later.")}</p>
        </div>
      )}
    </section>
  );
}
