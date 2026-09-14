"use client";

import Link from "next/link";
import type { Product } from "@/types/api";
import { supportsLiveDemo } from "@/lib/live-demo";
import { SmartLogo } from "@/components/common/smart-logo";
import { FavoriteButton } from "@/components/favorites/favorite-button";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { handleExternalAnchorClick } from "@/lib/external-navigation";
import {
  cleanDescription, formatCategories, getLocalizedCountryName,
  getLocalizedProductDescription, getLocalizedProductWhyMatters,
  getProductWebsiteSearchUrl, getProductScore, isValidWebsite,
  normalizeWebsite, resolveProductLogoSources, resolveProductCountry,
} from "@/lib/product-utils";

type ProductCardProps = {
  product: Product;
  compact?: boolean;
  rank?: number;
  highlighted?: boolean;
  favoritable?: boolean;
};

/** One product briefing for the home, search and related-product surfaces. */
export function ProductCard({ product, compact = false, rank, highlighted = false, favoritable = true }: ProductCardProps) {
  const { locale, t } = useSiteLocale();
  const detailUrl = `/product/${encodeURIComponent(product._id || product.name)}`;
  const website = normalizeWebsite(product.website);
  const hasWebsite = isValidWebsite(website) && !product.needs_verification;
  const score = getProductScore(product);
  const scoreLabel = score > 0 ? `${Number.isInteger(score) ? score : score.toFixed(1)} / 5` : t("待评", "Unrated");
  const region = getLocalizedCountryName(resolveProductCountry(product), locale);
  const recordedDate = (product.discovered_at || product.first_seen || "").slice(0, 10);
  const description = cleanDescription(getLocalizedProductDescription(product, locale), locale);
  const whyMatters = cleanDescription(getLocalizedProductWhyMatters(product, locale), locale);
  const resolvedLogo = resolveProductLogoSources(product);
  const websiteSearchUrl = getProductWebsiteSearchUrl(product.name, locale);

  return (
    <article className={`research-product${compact ? " research-product--compact" : ""}${highlighted ? " research-product--leading" : ""}`}>
      <header className={`research-product__identity${rank !== undefined ? " research-product__identity--ranked" : ""}`}>
        {rank !== undefined ? <span className="research-product__rank" aria-label={`${t("排名", "Rank")} ${rank}`}>{String(rank).padStart(2, "0")}</span> : null}
        <SmartLogo
          key={`${product._id || product.name}-${resolvedLogo.logoUrl}-${resolvedLogo.secondaryLogoUrl}`}
          className="research-product__logo"
          name={product.name}
          {...resolvedLogo}
          website={product.website}
          sourceUrl={product.source_url}
          trustPrimaryLogo
          size={compact ? 44 : 56}
          loading={rank !== undefined && rank <= 3 ? "eager" : "lazy"}
        />
        <div className="research-product__identity-copy">
          <h3 className="research-product__title"><Link href={detailUrl}>{product.name}</Link></h3>
          <p className="research-product__category">{formatCategories(product, locale)}</p>
          <p className="research-product__meta">{region}<span aria-hidden="true"> · </span>{t("发现评分", "Discovery score")} {scoreLabel}</p>
          {recordedDate ? <p className="research-product__date"><time dateTime={recordedDate}>{recordedDate}</time></p> : null}
        </div>
      </header>
      <div className="research-product__briefing">
        <p className="research-product__description">{description || t("产品摘要待补充", "Product summary pending")}</p>
        {whyMatters && whyMatters !== description ? <p className="research-product__why"><span>{t("值得注意", "WHY LOOK")} / </span>{whyMatters}</p> : null}
      </div>
      <footer className="research-product__footer">
        <div className="research-product__reference">
          {product.source_url && isValidWebsite(product.source_url) ? <a href={product.source_url} target="_blank" rel="noopener noreferrer">{t("阅读来源", "Read source")} <span aria-hidden="true">↗</span></a> : null}
          {favoritable ? <FavoriteButton product={product} /> : null}
        </div>
        <div className="research-product__actions">
          <Link href={detailUrl}>{t("详情", "Details")}</Link>
          {supportsLiveDemo(product) ? <Link href={`${detailUrl}?demo=1#try-demo`} className="research-product__try">{t("交互试用", "Try demo")}</Link> : null}
          <a href={hasWebsite ? website : websiteSearchUrl} target="_blank" rel="noopener noreferrer" onClick={(event) => handleExternalAnchorClick(event, hasWebsite ? website : websiteSearchUrl)}>
            {hasWebsite ? t("官网", "Website") : t("查找官网", "Find website")} <span aria-hidden="true">↗</span>
          </a>
        </div>
      </footer>
    </article>
  );
}
