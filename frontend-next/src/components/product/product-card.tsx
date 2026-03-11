"use client";

import Link from "next/link";
import type { Product } from "@/types/api";
import { SmartLogo } from "@/components/common/smart-logo";
import { FavoriteButton } from "@/components/favorites/favorite-button";
import { useSiteLocale } from "@/components/layout/locale-provider";
import {
  cleanDescription,
  formatCategories,
  getFreshnessLabel,
  getLocalizedCountryName,
  getLocalizedProductDescription,
  getLocalizedProductWhyMatters,
  getProductWebsiteSearchUrl,
  getProductScore,
  getScoreBadgeClass,
  isHardware,
  isValidWebsite,
  normalizeWebsite,
  resolveProductCountry,
} from "@/lib/product-utils";

type ProductCardProps = {
  product: Product;
  compact?: boolean;
};

function formatScore(score: number, locale: "zh-CN" | "en-US"): string {
  if (score <= 0) return locale === "en-US" ? "Unrated" : "待评";
  if (locale === "en-US") {
    return Number.isInteger(score) ? `${score}/5` : `${score.toFixed(1)}/5`;
  }
  return Number.isInteger(score) ? `${score}分` : `${score.toFixed(1)}分`;
}

export function ProductCard({ product, compact = false }: ProductCardProps) {
  const { locale, t } = useSiteLocale();
  const website = normalizeWebsite(product.website);
  const hasWebsite = isValidWebsite(website) && !product.needs_verification;
  const detailId = encodeURIComponent(product._id || product.name);
  const score = getProductScore(product);
  const scoreLabel = formatScore(score, locale);
  const freshness = getFreshnessLabel(product, new Date(), locale);
  const country = resolveProductCountry(product);
  const regionLabel = getLocalizedCountryName(country, locale);
  const regionMark = country.flag;
  const hasRegionText = true;
  const microlineParts = [freshness, product.source || t("来源待补充", "Source pending")];
  const description = cleanDescription(getLocalizedProductDescription(product, locale), locale);
  const whyMatters = getLocalizedProductWhyMatters(product, locale);
  const summary = whyMatters || description || t("产品摘要待补充", "Product summary pending");
  const tierClass = score >= 4 ? "product-card--darkhorse" : score >= 2 ? "product-card--rising" : "product-card--watch";
  const secondaryBadge = product.funding_total || (isHardware(product) ? t("硬件", "Hardware") : t("软件", "Software"));
  const websiteSearchUrl = getProductWebsiteSearchUrl(product.name, locale);

  return (
    <article className={`product-card product-card--signal ${tierClass} ${compact ? "product-card--compact" : ""}`}>
      <div className="product-card__content">
        <div className="product-card__topline">
          <span className="product-card__region-pill" aria-label={`${t("地区", "Region")}: ${regionLabel}`} title={`${t("地区", "Region")}: ${regionLabel}`}>
            {regionMark ? (
              <span className="product-card__region-flag" aria-hidden="true">
                {regionMark}
              </span>
            ) : null}
            {hasRegionText ? <span className="product-card__region-text">{regionLabel}</span> : null}
          </span>
          <p className="product-card__microline">{microlineParts.join(" · ")}</p>
        </div>

        <header className="product-card__header">
          <div className="product-card__identity">
            <SmartLogo
              key={`${product._id || product.name}-${product.logo_url || ""}-${product.logo || ""}-${product.website || ""}-${product.source_url || ""}`}
              className="product-card__logo"
              name={product.name}
              logoUrl={product.logo_url}
              secondaryLogoUrl={product.logo}
              website={product.website}
              sourceUrl={product.source_url}
              size={compact ? 44 : 48}
            />
            <div className="product-card__identity-copy">
              <h3 className="product-card__title">{product.name}</h3>
              <p className="product-card__meta">{formatCategories(product, locale)}</p>
            </div>
          </div>

          <div className="product-card__badges">
            <span className={`product-badge ${getScoreBadgeClass(score, "product")}`}>
              {score >= 4 ? `${t("黑马", "Dark Horse")} ${scoreLabel}` : score >= 2 ? `${t("潜力", "Rising")} ${scoreLabel}` : scoreLabel}
            </span>
            <span className="product-badge">{secondaryBadge}</span>
          </div>
        </header>

        <div className="product-card__summary">
          <p className={`product-card__summary-text ${whyMatters ? "product-card__summary-text--why" : ""}`}>
            {whyMatters ? <span className="product-card__summary-why-label">WHY</span> : null}
            {summary}
          </p>
        </div>

        <footer className="product-card__footer">
          <FavoriteButton product={product} />
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
    </article>
  );
}
