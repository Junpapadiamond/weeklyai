"use client";

import Link from "next/link";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { HOOK_COLORS, HOOK_LABELS_EN, HOOK_LABELS_ZH, resolveHook } from "@/lib/hook-colors";
import { formatAbsoluteDate, getLocalizedProductWhyMatters } from "@/lib/product-utils";
import type { Product } from "@/types/api";
import type { CSSProperties } from "react";

type RecentPicksStripProps = {
  picks: Product[];
};

function pickHref(product: Product): string {
  return `/product/${encodeURIComponent(product._id || product.id || product.name)}`;
}

function pickDate(product: Product, locale: "zh-CN" | "en-US"): string {
  return formatAbsoluteDate(product.curated_at || product.discovered_at || product.first_seen || product.published_at, locale) || "";
}

function compactWhy(product: Product, locale: "zh-CN" | "en-US") {
  const value = getLocalizedProductWhyMatters(product, locale).replace(/^["“]|["”]$/g, "").trim();
  if (!value) return "";
  return value.length > 54 ? `${value.slice(0, 53).trim()}…` : value;
}

export function RecentPicksStrip({ picks }: RecentPicksStripProps) {
  const { locale, t } = useSiteLocale();

  return (
    <section className="v2-section">
      <div className="v2-section-head">
        <h2>{t("Recent picks", "Recent picks")}</h2>
        <span>{t("最近 7 个", "Last 7")}</span>
      </div>
      <div className="v2-picks-strip" aria-label={t("最近精选", "Recent picks")}>
        {picks.slice(0, 7).map((product) => {
          const hook = resolveHook(product.hook);
          const label = locale === "en-US" ? HOOK_LABELS_EN[hook] : HOOK_LABELS_ZH[hook];
          const why = compactWhy(product, locale);
          return (
            <Link
              href={pickHref(product)}
              className="v2-mini-card"
              key={`${product._id || product.id || product.name}-${product.first_seen || ""}`}
              style={{ "--hook-color": HOOK_COLORS[hook] } as CSSProperties}
              title={getLocalizedProductWhyMatters(product, locale)}
            >
              <div className="v2-mini-art">
                <span>{label}</span>
              </div>
              <div className="v2-mini-copy">
                <div className="v2-mini-name">{product.name}</div>
                {why ? <p>{why}</p> : null}
              </div>
              <div className="v2-mini-date">{pickDate(product, locale)}</div>
            </Link>
          );
        })}
        {picks.length === 0 ? <div className="v2-strip-empty">{t("还没有精选", "No picks yet")}</div> : null}
      </div>
    </section>
  );
}
