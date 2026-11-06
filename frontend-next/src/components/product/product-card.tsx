"use client";

import Link from "next/link";
import { ArrowRight, CaretDown } from "@phosphor-icons/react";
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
  featured?: boolean;
  favoritable?: boolean;
};

/** One product briefing for the home, search and related-product surfaces. */
export function ProductCard({ product, compact = false, rank, featured = false, favoritable = true }: ProductCardProps) {
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

  const destination = hasWebsite ? website : websiteSearchUrl;
  const category = formatCategories(product, locale);
  const rationale = whyMatters !== description ? whyMatters : "";
  const summary = description || t("暂无产品介绍", "Product summary pending");
  const logo = (
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
  );
  const favorite = favoritable ? <FavoriteButton product={product} /> : null;
  const sourceLink = product.source_url && isValidWebsite(product.source_url) ? (
    <a href={product.source_url} target="_blank" rel="noopener noreferrer">
      {t("查看来源", "Read source")} <span aria-hidden="true">↗</span>
    </a>
  ) : null;
  const secondaryLinks = (
    <>
      {supportsLiveDemo(product) ? (
        <Link href={`${detailUrl}?demo=1#try-demo`} className="research-product__try">{t("查看演示", "Try demo")}</Link>
      ) : null}
      <a href={destination} target="_blank" rel="noopener noreferrer" onClick={(event) => handleExternalAnchorClick(event, destination)}>
        {hasWebsite ? t("访问官网", "Website") : t("查找官网", "Find website")} <span aria-hidden="true">↗</span>
      </a>
    </>
  );
  const scoreText = <>{t("黑马指数", "Discovery score")} {scoreLabel}</>;
  const date = recordedDate ? <time dateTime={recordedDate}>{recordedDate}</time> : null;

  if (featured) {
    return (
      <article className={rank === 1 ? "radar-product radar-product--lead" : "radar-product"}>
        <header className="radar-product__identity">
          <h3><Link href={detailUrl}>{logo}<span>{product.name}</span></Link></h3>
          <p className="radar-product__meta"><span>{category}</span><span>{region}</span><span>{scoreText}</span></p>
        </header>
        {favorite}
        <div className="radar-product__body">
          <p className="radar-product__summary">{summary}</p>
          <div className="radar-product__actions">
            <Link href={detailUrl} className="radar-product__details">{t("查看详情", "Details")} <ArrowRight size={16} aria-hidden="true" /></Link>
            {sourceLink}
          </div>
          <details className="radar-product__notes">
            <summary>{t("产品笔记与链接", "Notes & links")} <CaretDown size={14} aria-hidden="true" /></summary>
            {rationale ? <p>{rationale}</p> : null}
            <div className="radar-product__links">
              {secondaryLinks}
              {date ? <span>{t("收录于 ", "Added ")}{date}</span> : null}
            </div>
          </details>
        </div>
      </article>
    );
  }

  return (
    <article className={`research-product${compact ? " research-product--compact" : ""}`}>
      <header className={`research-product__identity${rank !== undefined ? " research-product__identity--ranked" : ""}`}>
        {rank !== undefined ? <span className="research-product__rank" aria-label={`${t("排名", "Rank")} ${rank}`}>{String(rank).padStart(2, "0")}</span> : null}
        {logo}
        <div className="research-product__identity-copy">
          <h3 className="research-product__title"><Link href={detailUrl}>{product.name}</Link></h3>
          <p className="research-product__category">{category}</p>
          <p className="research-product__meta">{region}<span aria-hidden="true"> · </span>{scoreText}</p>
          {date ? <p className="research-product__date">{t("收录于 ", "")}{date}</p> : null}
        </div>
      </header>
      <div className="research-product__briefing">
        <p className="research-product__description">{summary}</p>
        {rationale ? <p className="research-product__why">{rationale}</p> : null}
      </div>
      <footer className="research-product__footer">
        <div className="research-product__reference">
          {sourceLink}
          {favorite}
        </div>
        <div className="research-product__actions">
          <Link href={detailUrl}>{t("查看详情", "Details")}</Link>
          {secondaryLinks}
        </div>
      </footer>
    </article>
  );
}
