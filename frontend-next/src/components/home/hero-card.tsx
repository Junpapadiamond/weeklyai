"use client";

import Link from "next/link";
import { SmartLogo } from "@/components/common/smart-logo";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { handleExternalAnchorClick } from "@/lib/external-navigation";
import { HOOK_COLORS, HOOK_LABELS_EN, HOOK_LABELS_ZH, resolveHook } from "@/lib/hook-colors";
import {
  getLocalizedProductDescription,
  getLocalizedProductWhyMatters,
  normalizeWebsite,
  resolveProductLogoSources,
} from "@/lib/product-utils";
import type { Product } from "@/types/api";
import type { CSSProperties } from "react";

type HeroCardProps = {
  product: Product | null;
  issueNumber: number;
  dateLabel: string;
};

function getHeroImage(product: Product): string {
  return product.image_url || product.cover_image || product.hero_image || product.og_image || product.logo_url || product.logo || "";
}

function hasStrongImage(product: Product): boolean {
  return Boolean(product.has_strong_image || product.image_url || product.cover_image || product.hero_image || product.og_image);
}

function detailHref(product: Product): string {
  return `/product/${encodeURIComponent(product._id || product.id || product.name)}`;
}

function getPickReason(product: Product, locale: "zh-CN" | "en-US"): string {
  if (locale === "en-US") {
    return product.pick_reason_en || product.pick_reason || "";
  }
  return product.pick_reason || product.pick_reason_en || "";
}

export function HeroCard({ product, issueNumber, dateLabel }: HeroCardProps) {
  const { locale, t } = useSiteLocale();

  if (!product) {
    return (
      <section className="v2-hero-card v2-hero-card--empty-hard">
        <div className="v2-hero-top">
          <span>{t("Today", "Today")} · {dateLabel}</span>
          <span>No.{issueNumber}</span>
        </div>
        <div className="v2-hero-empty-copy">
          <span>{t("今天编辑还在选", "Today pick pending")}</span>
          <h1>{t("还没有值得硬推的 pick", "No hard pick yet")}</h1>
          <p>{t("宁缺毋滥。候选池准备好后，curate.py 会把真正值得点开的产品推到这里。", "No filler. When curation finds a real stop-scroller, it lands here.")}</p>
        </div>
      </section>
    );
  }

  const hook = resolveHook(product.hook);
  const hookLabel = locale === "en-US" ? HOOK_LABELS_EN[hook] : HOOK_LABELS_ZH[hook];
  const color = HOOK_COLORS[hook];
  const why = getLocalizedProductWhyMatters(product, locale) || getLocalizedProductDescription(product, locale);
  const pickReason = getPickReason(product, locale);
  const image = getHeroImage(product);
  const strongImage = hasStrongImage(product);
  const website = normalizeWebsite(product.website);
  const resolvedLogo = resolveProductLogoSources(product);
  const isYesterday = Boolean(product.is_yesterday);
  const isBootstrap = Boolean(product.is_bootstrap_pick);

  if (!strongImage) {
    return (
      <section className={`v2-hero-card v2-hero-card--fallback ${isYesterday ? "v2-hero-card--yesterday" : ""}`} style={{ "--hook-color": color } as CSSProperties}>
        {isBootstrap ? <span className="v2-empty-pill">{t("v2 规则预览 · 等待人工精选", "v2 rubric preview · awaiting manual curation")}</span> : null}
        <div className="v2-fallback-bar" />
        <div className="v2-hero-top v2-hero-top--fallback">
          <span>{isYesterday ? t("Yesterday", "Yesterday") : t("Today", "Today")} · {dateLabel}</span>
          <span>No.{issueNumber}</span>
        </div>
        <p className="v2-hook-word">{hookLabel}</p>
        <h1 className="v2-fallback-title">{product.name}</h1>
        <p className="v2-fallback-quote">&ldquo;{why}&rdquo;</p>
        {pickReason ? (
          <div className="v2-pick-reason">
            <span>{t("为什么选它", "Why this pick")}</span>
            <p>{pickReason}</p>
          </div>
        ) : null}
        <div className="v2-fallback-logo">
          <SmartLogo
            className="v2-fallback-logo__box"
            name={product.name}
            logoUrl={resolvedLogo.logoUrl}
            secondaryLogoUrl={resolvedLogo.secondaryLogoUrl}
            website={product.website}
            sourceUrl={product.source_url}
            trustPrimaryLogo
            size={32}
          />
          <span>{website ? new URL(website).hostname.replace(/^www\./, "") : product.source || "WeeklyAI"}</span>
        </div>
        <Link href={detailHref(product)} className="v2-hero-cta">
          {t("看详情", "Details")} →
        </Link>
      </section>
    );
  }

  return (
    <section className={`v2-hero-card v2-hero-card--default ${isYesterday ? "v2-hero-card--yesterday" : ""}`} style={{ "--hook-color": color } as CSSProperties}>
      {isBootstrap ? <span className="v2-empty-pill">{t("v2 规则预览 · 等待人工精选", "v2 rubric preview · awaiting manual curation")}</span> : null}
      <div className="v2-hero-top">
        <span>{isYesterday ? t("Yesterday", "Yesterday") : t("Today", "Today")} · {dateLabel}</span>
        <span>No.{issueNumber}</span>
      </div>
      <div className="v2-hero-media">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        {image ? <img src={image} alt="" /> : <span>photo</span>}
      </div>
      <div className="v2-hero-copy">
        <span className="v2-hook-badge">{hookLabel}</span>
        <h1>{product.name}</h1>
        <p>{why}</p>
        {pickReason ? (
          <div className="v2-pick-reason v2-pick-reason--dark">
            <span>{t("为什么选它", "Why this pick")}</span>
            <p>{pickReason}</p>
          </div>
        ) : null}
        <div className="v2-hero-foot">
          <span>WeeklyAI</span>
          <Link href={detailHref(product)}>{t("看详情", "Details")} →</Link>
        </div>
        {website ? (
          <a
            className="v2-source-link"
            href={website}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(event) => handleExternalAnchorClick(event, website)}
          >
            {t("打开官网", "Open website")}
          </a>
        ) : null}
      </div>
    </section>
  );
}
