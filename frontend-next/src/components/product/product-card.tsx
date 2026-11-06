"use client";

import Link from "next/link";
import { useId, useState } from "react";
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
  const notesId = useId();
  const [notesOpen, setNotesOpen] = useState(false);
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
      size={44}
      loading={rank !== undefined && rank <= 3 ? "eager" : "lazy"}
    />
  );
  const favorite = favoritable ? <FavoriteButton product={product} /> : null;
  const sourceLink = product.source_url && isValidWebsite(product.source_url) ? (
    <a className="radar-product__source" href={product.source_url} onClick={(event) => handleExternalAnchorClick(event, event.currentTarget.href)} target="_blank" rel="noopener noreferrer">
      {t("来源", "Source")} <span aria-hidden="true">↗</span>
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

  const layout = compact ? "radar-product--compact" : featured && rank === 1 ? "radar-product--lead" : "";

  return (
    <article className={`radar-product ${layout}`.trim()}>
      <header className="radar-product__identity">
        <h3><Link href={detailUrl}>{logo}<span>{product.name}</span></Link></h3>
        <p className="radar-product__meta">
          {!featured && rank !== undefined ? <span aria-label={`${t("排名", "Rank")} ${rank}`}>#{rank}</span> : null}
          <span>{category}</span><span>{region}</span><span>{scoreText}</span>
          {date}
        </p>
      </header>
      <p className="radar-product__summary">{summary}</p>
      <div className="radar-product__actions">
        <Link href={detailUrl} className="radar-product__details">{t("详情", "Details")} <ArrowRight size={14} aria-hidden="true" /></Link>
        {sourceLink}
        <button type="button" className="radar-product__toggle" aria-expanded={notesOpen} aria-controls={notesId}
          onClick={() => setNotesOpen(open => !open)}>
          {t("笔记", "Notes")} <CaretDown size={13} aria-hidden="true" />
        </button>
        {favorite}
      </div>
      <div id={notesId} className="radar-product__notes" hidden={!notesOpen}>
        {rationale ? <p>{rationale}</p> : null}
        <div className="radar-product__links">
          {secondaryLinks}
        </div>
      </div>
    </article>
  );
}
