"use client";

import type { Product } from "@/types/api";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { ProductCard } from "@/components/product/product-card";

type DiscoverGridProps = {
  products: Product[];
};

export function DiscoverGrid({ products }: DiscoverGridProps) {
  const { t } = useSiteLocale();

  return (
    <div className="discover-grid-shell" aria-label={t("桌面速览网格", "Desktop quick scan grid")}>
      <p className="discover-grid-shell__hint">
        {t("桌面端改为高密速览：一次浏览更多产品，点击详情深挖。", "Desktop quick scan mode: review more products at once, then open details.")}
      </p>
      <div className="products-grid discover-grid-shell__grid">
        {products.map((product) => (
          <ProductCard key={`discover-grid-${product._id || product.name}`} product={product} />
        ))}
      </div>
    </div>
  );
}
