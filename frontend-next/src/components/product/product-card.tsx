import Link from "next/link";
import type { Product } from "@/types/api";
import { SmartLogo } from "@/components/common/smart-logo";
import { FavoriteButton } from "@/components/favorites/favorite-button";
import {
  cleanDescription,
  formatCategories,
  getFreshnessLabel,
  getProductScore,
  isHardware,
  isValidWebsite,
  normalizeWebsite,
} from "@/lib/product-utils";

type ProductCardProps = {
  product: Product;
  compact?: boolean;
};

function formatScore(score: number): string {
  if (score <= 0) return "待评";
  return Number.isInteger(score) ? `${score}分` : `${score.toFixed(1)}分`;
}

export function ProductCard({ product, compact = false }: ProductCardProps) {
  const website = normalizeWebsite(product.website);
  const hasWebsite = isValidWebsite(website);
  const detailId = encodeURIComponent(product._id || product.name);
  const score = getProductScore(product);
  const scoreLabel = formatScore(score);
  const freshness = getFreshnessLabel(product);
  const regionLabel = product.region?.trim() || "全球";
  const regionMark = product.region?.trim() || "🌍";
  const hasRegionText = /[A-Za-z\u4e00-\u9fff]/.test(regionLabel);
  const microlineParts = [freshness, product.source || "来源待补充"];
  const description = cleanDescription(product.description);
  const summaryParts = [description];
  if (product.why_matters) {
    summaryParts.push(`为何重要：${product.why_matters}`);
  }
  const summaryText = summaryParts.join(" ");
  const tierClass = score >= 4 ? "product-card--darkhorse" : score >= 2 ? "product-card--rising" : "product-card--watch";
  const secondaryBadge = product.funding_total || (isHardware(product) ? "硬件" : "软件");

  return (
    <article className={`product-card product-card--signal ${tierClass} ${compact ? "product-card--compact" : ""}`}>
      <div className="product-card__content">
        <div className="product-card__topline">
          <span className="product-card__region-pill" aria-label={`地区：${regionLabel}`} title={`地区：${regionLabel}`}>
            <span className="product-card__region-flag" aria-hidden="true">
              {regionMark}
            </span>
            {hasRegionText ? <span className="product-card__region-text">{regionLabel}</span> : null}
          </span>
          <p className="product-card__microline">{microlineParts.join(" · ")}</p>
        </div>

        <header className="product-card__header">
          <div className="product-card__identity">
            <SmartLogo
              key={`${product._id || product.name}-${product.logo_url || ""}-${product.website || ""}`}
              className="product-card__logo"
              name={product.name}
              logoUrl={product.logo_url}
              website={product.website}
              sourceUrl={product.source_url}
              size={compact ? 44 : 48}
            />
            <div className="product-card__identity-copy">
              <h3 className="product-card__title">{product.name}</h3>
              <p className="product-card__meta">{formatCategories(product)}</p>
            </div>
          </div>

          <div className="product-card__badges">
            <span className={`product-badge ${score >= 4 ? "product-badge--darkhorse" : score >= 2 ? "product-badge--rising" : ""}`}>
              {score >= 4 ? `黑马 ${scoreLabel}` : score >= 2 ? `潜力 ${scoreLabel}` : scoreLabel}
            </span>
            <span className="product-badge">{secondaryBadge}</span>
          </div>
        </header>

        <div className="product-card__summary">
          <p className="product-card__summary-text">{summaryText}</p>
        </div>

        <footer className="product-card__footer">
          <FavoriteButton product={product} />
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
    </article>
  );
}
