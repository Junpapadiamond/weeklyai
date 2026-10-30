"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { BookmarkSimple, House } from "@phosphor-icons/react";
import { useEffect, useRef, useState } from "react";
import { getDiscoveryPage } from "@/lib/api-client";
import type { Product } from "@/types/api";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { addProductFavorite, countFavorites, openFavoritesPanel, subscribeFavorites } from "@/lib/favorites";

const DiscoveryDeck = dynamic(() => import("@/components/home/discovery-deck"), {
  ssr: false,
  loading: () => <div className="discover-skeleton" aria-busy="true"><div className="discover-skeleton__card"><div className="discover-skeleton__topline" /><div className="discover-skeleton__line discover-skeleton__line--lg" /><div className="discover-skeleton__line" /></div></div>,
});

type DiscoverClientProps = {
  initialPage: Awaited<ReturnType<typeof getDiscoveryPage>>;
};

export function DiscoverClient({ initialPage }: DiscoverClientProps) {
  const { t } = useSiteLocale();
  const [favoritesCount, setFavoritesCount] = useState(0);
  const [batch, setBatch] = useState(initialPage);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState(false);
  const loadingRef = useRef(false);

  async function loadNext() {
    if (loadingRef.current || !batch.pagination.has_more) return;
    loadingRef.current = true;
    setLoading(true);
    setLoadError(false);
    try {
      setBatch(await getDiscoveryPage(batch.pagination.offset + batch.pagination.limit));
    } catch {
      setLoadError(true);
    } finally {
      loadingRef.current = false;
      setLoading(false);
    }
  }

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
          {t("随便看看", "Discover")}
        </h1>
      </div>

      <div className="list-controls discover-page__controls">
        <button className="favorites-toggle" type="button" aria-label={t("打开收藏夹", "Open favorites")} onClick={() => openFavoritesPanel("product")}>
          <BookmarkSimple size={17} aria-hidden="true" /> {favoritesCount}
        </button>
        <Link className="link-btn" href="/">
          <House size={14} /> {t("返回首页", "Back to home")}
        </Link>
      </div>

      {batch.data.length ? (
        <DiscoveryDeck key={`discover-${batch.pagination.offset}`} products={batch.data} onLike={addFavorite}
          onExhausted={batch.pagination.has_more ? loadNext : undefined} />
      ) : (
        <div className="empty-state">
          <p className="empty-state-text">{t("暂时没有更多产品，过会儿再来看看。", "No products available to explore right now. Please try again later.")}</p>
        </div>
      )}
      {batch.pagination.has_more ? (
        <div className="load-more-container" aria-live="polite">
          {loadError ? <p role="alert">{t("下一组暂时加载失败，可以重试。", "Could not load the next group. Please retry.")}</p> : null}
          <button className="load-more-btn" type="button" disabled={loading} onClick={loadNext}>
            {loading ? t("加载下一组…", "Loading more…") : loadError ? t("重试", "Retry") : t("换一组产品", "Explore another group")}
          </button>
        </div>
      ) : null}
    </section>
  );
}
