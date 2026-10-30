"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { MagnifyingGlass, ArrowRight, Play, Gauge } from "@phosphor-icons/react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { SmartLogo } from "@/components/common/smart-logo";
import { cleanDescription, formatCategories, getLocalizedProductDescription, resolveProductLogoSources } from "@/lib/product-utils";
import { ProductLiveDemo } from "./product-live-demo";
import type { DemoQuota } from "@/lib/demo-experience";
import type { Product } from "@/types/api";

type Catalog = { products: (Product & { demo_ready: boolean })[]; total: number; ready_count: number; dark_count: number; catalog_total: number; generation_available: boolean; quota: DemoQuota | null };
export function DemoGallery({ initialFilter = "all" }: { initialFilter?: "all" | "ready" }) {
  const { t, locale } = useSiteLocale();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<string>(initialFilter);
  const [page, setPage] = useState(1);
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [selected, setSelected] = useState<Product | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState(false);
  const [revision, setRevision] = useState(0);
  const searchInput = useRef<HTMLInputElement>(null);
  const backButton = useRef<HTMLButtonElement>(null);
  const prepared = useCallback(() => setRevision(v => v + 1), []);
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setBusy(true); setError(false);
      try {
        const response = await fetch("/api/v1/demos/catalog?" + new URLSearchParams({ q: query, filter, page: String(page) }), { signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]) });
        if (!response.ok) throw new Error("UNAVAILABLE");
        const body = await response.json();
        if (!body.success) throw new Error("INVALID_RESPONSE");
        if (!controller.signal.aborted) setCatalog(body);
      } catch { if (!controller.signal.aborted) setError(true); }
      finally { if (!controller.signal.aborted) setBusy(false); }
    }, query ? 250 : 0);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [query, filter, page, revision]);
  if (selected) return <section className="demo-gallery"><div className="demo-selected">
    <button ref={backButton} className="demo-back-gallery" type="button" onClick={() => { setSelected(null); setRevision(v => v + 1); requestAnimationFrame(() => searchInput.current?.focus()); }}>{t("← 返回产品列表", "← Back to products")}</button>
    <ProductLiveDemo key={selected._id || selected.name} product={selected} autoOpen compact onPrepared={prepared} />
  </div></section>;
  const tabs = [{ id: "all", name: t("全部产品", "All products"), count: catalog?.catalog_total }, { id: "ready", name: t("已有演示", "Ready to play"), count: catalog?.ready_count }, { id: "dark", name: t("黑马产品", "Dark horses"), count: catalog?.dark_count }];
  return <section className="demo-gallery">
    <Link className="demo-back-gallery" href="/demo/examples">{t("更多演示示例", "More interactive examples")} ↗</Link>
    <header className="demo-gallery-header">
      <div><h1>{t("产品演示", "Product demos")}</h1><p>{t("独立示例 · 非原厂输出", "Independent examples · Not vendor output")}</p></div>
      <div className="demo-budget"><Gauge size={17} /><div>
        <span>{t("今日剩余生成次数", "Generations left today")}</span>
        <strong>{catalog?.quota ? catalog.quota.remaining + " / " + catalog.quota.limit : "—"}</strong>
        <details><summary>{t("额度说明", "Credit details")}</summary><p>{t("首次生成使用 1 次额度；已有演示不计次数。每日北京时间 08:00 重置。", "New examples use 1 credit; prepared examples are free. Resets at 00:00 UTC.")}</p></details>
      </div></div>
    </header>
    <div className="demo-gallery-tools"><div className="demo-filter-tabs" aria-label={t("演示筛选", "Filter experiences")}>{tabs.map(tab => <button key={tab.id} type="button" aria-pressed={filter === tab.id} onClick={() => { setFilter(tab.id); setPage(1); }}>{tab.name}<span>{tab.count ?? "—"}</span></button>)}</div><label className="demo-search"><MagnifyingGlass size={16} /><input ref={searchInput} aria-label={t("搜索演示产品", "Search demo products")} placeholder={t("搜索产品、类别或国家", "Search products, categories, countries")} value={query} onChange={event => { setQuery(event.target.value); setPage(1); }} /></label></div>
    {catalog && !catalog.generation_available ? <p className="demo-availability" role="status">{t("暂时无法生成新演示，可查看已有演示。", "New examples are unavailable. Prepared examples remain available.")}</p> : null}
    {error ? <div className="demo-gallery-empty" role="status"><p>{t("产品列表暂时无法加载", "The product list is unavailable")}</p><button type="button" onClick={() => setRevision(v => v + 1)}>{t("重试", "Retry")}</button></div> : null}
    <div className="demo-catalog-grid" aria-busy={busy}>{busy ? Array.from({ length: 12 }, (_, i) => <div className="demo-card-placeholder" key={i} />) : !error ? catalog?.products.map(product => <button type="button" key={product._id || product.name} className="demo-product-card" onClick={() => { setSelected(product); requestAnimationFrame(() => backButton.current?.focus()); }}>
      <div className="demo-card-top"><SmartLogo key={`${product._id}-${product.logo_url || ""}`} className="demo-product-logo" name={product.name} {...resolveProductLogoSources(product)} website={product.website} sourceUrl={product.source_url} trustPrimaryLogo size={29} /><strong>{product.name}</strong></div>
      <p>{cleanDescription(getLocalizedProductDescription(product, locale), locale)}</p>
      <div className="demo-card-meta"><span>{product.dark_horse_index || 0}/5 · {formatCategories(product, locale)}</span>{product.is_hardware ? <span>{t("概念演示", "Concept")}</span> : null}</div>
      <div className="demo-card-action"><span><Play size={12} />{product.demo_ready ? t("查看演示", "View example") : t("生成演示 · 1 次额度", "Generate · 1 credit")}</span><ArrowRight size={15} /></div>
    </button>) : null}</div>
    {!busy && !error && !catalog?.products.length ? <div className="demo-gallery-empty">{t("没有匹配的产品，换个词试试。", "No matching products. Try another search.")}</div> : null}
    {catalog && catalog.total > 24 ? <nav className="demo-pagination" aria-label={t("产品分页", "Product pages")}><button type="button" disabled={page <= 1 || busy} onClick={() => setPage(v => v - 1)}>{t("上一页", "Previous")}</button><span>{page} / {Math.ceil(catalog.total / 24)}</span><button type="button" disabled={page * 24 >= catalog.total || busy} onClick={() => setPage(v => v + 1)}>{t("下一页", "Next")}</button></nav> : null}
  </section>;
}
