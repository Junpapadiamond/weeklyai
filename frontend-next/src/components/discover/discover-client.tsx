"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { Dice5, Home } from "lucide-react";
import { useEffect, useState } from "react";
import type { Product } from "@/types/api";
import { addProductFavorite, countFavorites, openFavoritesPanel, subscribeFavorites } from "@/lib/favorites";

const DiscoveryDeck = dynamic(() => import("@/components/home/discovery-deck"), {
  ssr: false,
  loading: () => <div className="swipe-card is-active">加载探索卡片中...</div>,
});

type DiscoverClientProps = {
  products: Product[];
};

export function DiscoverClient({ products }: DiscoverClientProps) {
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
          随机发现
        </h1>
        <p className="section-desc">向右收藏，向左跳过，5 分钟筛出今天值得关注的新产品。</p>
        <p className="section-micro-note">首次访问会显示手势引导；滑动记录会在 7 天后自动重置。</p>
      </div>

      <div className="list-controls discover-page__controls">
        <button className="favorites-toggle" type="button" aria-label="打开收藏夹" onClick={() => openFavoritesPanel("product")}>
          ❤️ {favoritesCount}
        </button>
        <Link className="link-btn" href="/">
          <Home size={14} /> 返回首页
        </Link>
      </div>

      {products.length ? (
        <DiscoveryDeck key={`discover-${products.length}`} products={products} onLike={addFavorite} />
      ) : (
        <div className="empty-state">
          <p className="empty-state-text">暂无可探索产品，请稍后再试。</p>
        </div>
      )}
    </section>
  );
}
