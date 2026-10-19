"use client";

import Link from "next/link";
import { ArrowLeft, ArrowDown, ArrowUpRight, BookOpen, GlobeHemisphereWest } from "@phosphor-icons/react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { SmartLogo } from "@/components/common/smart-logo";
import { FavoriteButton } from "@/components/favorites/favorite-button";
import { ProductCard } from "./product-card";
import { ProductDetailExample } from "./product-detail-example";
import { supportsLiveDemo } from "@/lib/live-demo";
import { detailDate, detailValue } from "@/lib/product-detail";
import {
  cleanDescription, formatCategories, getLocalizedCountryName,
  getLocalizedProductDescription, getLocalizedProductLatestNews, getLocalizedProductWhyMatters,
  getProductScore, getProductWebsiteSearchUrl, isValidWebsite, normalizeWebsite,
  resolveProductCountry, resolveProductLogoSources,
} from "@/lib/product-utils";
import type { Product } from "@/types/api";
import "@/styles/product-detail.css";

export function ProductDetail({ product, related }: { product: Product; related: Product[] }) {
  const { locale, t } = useSiteLocale();
  const website = normalizeWebsite(product.website);
  const verified = isValidWebsite(website) && !product.needs_verification;
  const source = product.source_url && isValidWebsite(product.source_url) ? product.source_url : null;
  const score = getProductScore(product);
  const description = cleanDescription(getLocalizedProductDescription(product, locale), locale);
  const category = formatCategories(product, locale);
  const region = getLocalizedCountryName(resolveProductCountry(product), locale);
  const why = detailValue(getLocalizedProductWhyMatters(product, locale));
  const news = detailValue(getLocalizedProductLatestNews(product, locale));
  const discovered = detailDate(product.discovered_at || product.first_seen || product.published_at);
  const updated = detailDate(product.news_updated_at);
  const showExample = verified && supportsLiveDemo(product);
  const facts = [
    { label: t("分类", "Category"), value: category },
    { label: t("地区", "Region"), value: region },
    { label: t("融资记录", "Reported funding"), value: detailValue(product.funding_total) },
    { label: t("估值记录", "Reported valuation"), value: detailValue(product.valuation) },
    { label: t("收录价格", "Recorded price"), value: detailValue(product.price) },
    { label: t("收录日期", "Discovered"), value: discovered },
  ].filter(fact => fact.value);

  return <section className="section product-detail-page product-profile">
    <nav className="profile-breadcrumb" aria-label={t("页面位置", "Breadcrumb")}>
      <Link href="/"><ArrowLeft size={15} aria-hidden="true" />{t("产品库", "Product library")}</Link>
      <span aria-hidden="true">/</span><span aria-current="page">{product.name}</span>
    </nav>
    <article>
      <header className="profile-hero">
        <div className="profile-identity">
          <SmartLogo className="profile-logo" name={product.name} {...resolveProductLogoSources(product)}
            website={product.website} sourceUrl={product.source_url} trustPrimaryLogo size={72} loading="eager" />
          <div>
            <div className="profile-eyebrow"><span>{[category, region].filter(Boolean).join(" · ")}</span>
              {score > 0 ? <span className="profile-score">{score >= 4 ? t("黑马", "Dark horse") : t("潜力股", "Rising star")}<strong>{Number.isInteger(score) ? score : score.toFixed(1)}<span> / 5</span></strong></span> : null}
            </div>
            <h1>{product.name}</h1>
          </div>
        </div>
        <p className="profile-description">{description}</p>
        <div className="profile-actions">
          <a className="profile-primary" href={verified ? website : getProductWebsiteSearchUrl(product.name, locale)} target="_blank" rel="noopener noreferrer">
            {verified ? t("访问官网", "Visit website") : t("查找官网", "Find website")}<ArrowUpRight size={17} aria-hidden="true" />
          </a>
          <FavoriteButton product={product} showLabel size="md" />
          {showExample ? <a className="profile-text-link" href="#try-demo">{t("看具体示例", "Explore the example")}<ArrowDown size={15} aria-hidden="true" /></a> : null}
        </div>
      </header>
      {product.needs_verification ? <p className="profile-verification">{t("产品身份与资料尚待核实，请先查看原始来源。", "Product identity and details need verification. Check the original source first.")}</p> : null}
      <div className={`profile-layout${showExample && why ? " profile-layout--insight" : ""}`}>
        <div className="profile-main">
          {showExample ? <ProductDetailExample key={product._id || product.id || product.name} product={product} /> : why ? <section className="profile-section"><h2>{t("为什么值得关注", "Why look closer")}</h2><p>{why}</p></section> : null}
          {news ? <section className="profile-section profile-update">
            <div className="profile-section-heading"><h2>{t("已记录动态", "Recorded update")}</h2>{updated ? <time dateTime={updated}>{updated}</time> : null}</div>
            <p>{news}</p>
            {source ? <a className="profile-source-link" href={source} target="_blank" rel="noopener noreferrer">{t("查看原始来源", "Read original source")}<ArrowUpRight size={14} aria-hidden="true" /></a> : null}
          </section> : null}
          {!showExample && !why && !news ? <section className="profile-section"><h2>{t("继续了解", "Explore further")}</h2><p>{t("详细资料尚待补充，可从原始来源了解这款产品。", "More details are pending. Explore the original source to learn about this product.")}</p></section> : null}
        </div>
        {showExample && why ? <section className="profile-insight"><h2 className="profile-kicker"><BookOpen size={16} aria-hidden="true" />{t("为什么值得关注", "Why look closer")}</h2><p>{why}</p></section> : null}
        <aside className="profile-sidebar" aria-label={t("产品资料", "Product facts")}>
          <section className="profile-facts"><h2>{t("产品档案", "On record")}</h2><dl>
            {facts.map(fact => <div key={fact.label}><dt>{fact.label}</dt><dd>{fact.value}</dd></div>)}
          </dl></section>
          <div className="profile-provenance">
            {verified ? <a href={website} target="_blank" rel="noopener noreferrer"><GlobeHemisphereWest size={17} aria-hidden="true" /><span>{new URL(website).hostname}</span><ArrowUpRight size={14} aria-hidden="true" /></a> : null}
            {source ? <a href={source} target="_blank" rel="noopener noreferrer"><BookOpen size={17} aria-hidden="true" /><span>{t("查看原始来源", "Read original source")}</span><ArrowUpRight size={14} aria-hidden="true" /></a> : null}
            <p>{t("资料来自公开来源，收录信息不代表实时状态。", "Based on public sources. Recorded details may have changed.")}</p>
          </div>
        </aside>
      </div>
    </article>
    {related.length ? <section className="profile-related">
      <div className="profile-section-heading"><div><span className="profile-kicker">{t("继续发现", "Keep exploring")}</span><h2>{t("也看看这些产品", "Other products to explore")}</h2></div><Link className="profile-text-link" href="/search">{t("浏览产品库", "Browse the library")}<ArrowUpRight size={16} aria-hidden="true" /></Link></div>
      <div className="detail-related__grid">{related.map(item => <ProductCard key={item._id || item.name} product={item} compact />)}</div>
    </section> : null}
  </section>;
}
