"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Search, ArrowRight, Play, Sparkles } from "lucide-react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { SmartLogo } from "@/components/common/smart-logo";
import { resolveProductLogoSources } from "@/lib/product-utils";
import { ProductLiveDemo } from "./product-live-demo";
import type { DemoQuota } from "@/lib/demo-experience";
import type { Product } from "@/types/api";

type Catalog = { products: (Product & { demo_ready: boolean })[]; total: number; ready_count: number; dark_count: number; catalog_total: number; generation_available: boolean; quota: DemoQuota | null };
export function DemoGallery() {
  const { t, locale } = useSiteLocale();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [selected, setSelected] = useState<Product | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState(false);
  const [revision, setRevision] = useState(0);
  const prepared = useCallback(() => setRevision(v => v + 1), []);
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setBusy(true); setError(false);
      try {
        const response = await fetch("/api/v1/demos/catalog?" + new URLSearchParams({ q: query, filter, page: String(page) }), { signal: controller.signal });
        if (!response.ok) throw new Error("UNAVAILABLE");
        const body = await response.json();
        if (!body.success) throw new Error("INVALID_RESPONSE");
        setCatalog(body);
      } catch { if (!controller.signal.aborted) setError(true); }
      finally { if (!controller.signal.aborted) setBusy(false); }
    }, query ? 250 : 0);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [query, filter, page, revision]);
  const tabs = [{ id: "all", name: t("全部产品", "All products"), count: catalog?.catalog_total }, { id: "ready", name: t("立即体验", "Ready to play"), count: catalog?.ready_count }, { id: "dark", name: t("黑马优先", "Dark horses"), count: catalog?.dark_count }];
  return <section className="demo-gallery">
    <Link className="demo-back-gallery" href="/demo/examples">{t("更多交互示例", "More interactive examples")} ↗</Link>
    <header className="demo-gallery-header"><div><span className="demo-eyebrow">WEEKLYAI / INTERACTIVE DEMOS</span><h1>{t("好产品，点开就懂。", "A first impression, hands on.")}</h1><p>{t("从第一步到结果，亲手走一遍。黑马提前准备，其余现场生成。", "Try the workflow from start to finish. Dark horses are prepared; the rest are generated on demand.")}</p></div><div className="demo-budget"><Sparkles size={17} /><div><span>{t("今日生成额度", "Today’s generation credits")}</span><strong>{catalog?.quota ? catalog.quota.remaining + " / " + catalog.quota.limit : "—"}</strong><small>{t("已有演示免费畅玩 · 每日 UTC 0 点重置", "Free replays · Resets at 00:00 UTC")}</small></div></div></header>
    {selected ? <div className="demo-selected"><button className="demo-back-gallery" type="button" onClick={() => { setSelected(null); setRevision(v => v + 1); }}>{t("← 返回产品列表", "← Back to products")}</button><ProductLiveDemo key={selected._id || selected.name} product={selected} autoOpen compact onPrepared={prepared} /></div> : null}
    <div className="demo-gallery-tools"><div className="demo-filter-tabs" aria-label={t("演示筛选", "Filter experiences")}>{tabs.map(tab => <button key={tab.id} type="button" aria-pressed={filter === tab.id} onClick={() => { setFilter(tab.id); setPage(1); }}>{tab.name}<span>{tab.count ?? "—"}</span></button>)}</div><label className="demo-search"><Search size={16} /><input aria-label={t("搜索演示产品", "Search demo products")} placeholder={t("搜索产品、类别或国家", "Search products, categories, countries")} value={query} onChange={event => { setQuery(event.target.value); setPage(1); }} /></label></div>
    {catalog && !catalog.generation_available ? <p className="demo-availability">{t("现场生成尚未连接。标记「立即体验」的产品现在就能玩。", "On-demand generation is not connected. Products marked ready are available now.")}</p> : <p className="demo-availability">{t("点击即开体验；首次 AI 生成消耗 1 次额度，同一产品生成后免费复用。", "Open an experience in one click. A first generation uses one credit; cached products are free for everyone.")}</p>}
    {error ? <div className="demo-gallery-empty" role="status"><p>{t("产品列表暂时无法加载", "The product list is unavailable")}</p><button type="button" onClick={() => setRevision(v => v + 1)}>{t("重试", "Retry")}</button></div> : null}
    <div className="demo-catalog-grid" aria-busy={busy}>{busy ? Array.from({ length: 12 }, (_, i) => <div className="demo-card-placeholder" key={i} />) : !error ? catalog?.products.map(product => <button type="button" key={product._id || product.name} className="demo-product-card" onClick={() => { setSelected(product); requestAnimationFrame(() => document.getElementById("try-demo")?.scrollIntoView({ block: "start", behavior: "instant" })); }}>
      <div className="demo-card-top"><SmartLogo key={`${product._id}-${product.logo_url || ""}`} className="demo-product-logo" name={product.name} {...resolveProductLogoSources(product)} website={product.website} sourceUrl={product.source_url} trustPrimaryLogo size={29} /><strong>{product.name}</strong><span className={"demo-ready-badge " + (product.demo_ready ? "is-ready" : "")}>{product.demo_ready ? t("立即体验", "Ready") : t("AI 生成", "Generate")}</span></div>
      <p>{locale === "en-US" ? product.description_en || product.description : product.description}</p>
      <div className="demo-card-meta"><span>{product.dark_horse_index || 0}/5 · {product.categories?.[0] || t("其他", "Other")}</span>{product.is_hardware ? <span>{t("概念体验", "Concept")}</span> : null}</div>
      <div className="demo-card-action"><span><Play size={12} />{t("交互试用", "Try the workflow")}</span><ArrowRight size={15} /></div>
    </button>) : null}</div>
    {!busy && !error && !catalog?.products.length ? <div className="demo-gallery-empty">{t("没有匹配的产品，换个词试试。", "No matching products. Try another search.")}</div> : null}
    {catalog && catalog.total > 24 ? <nav className="demo-pagination" aria-label={t("产品分页", "Product pages")}><button type="button" disabled={page <= 1 || busy} onClick={() => setPage(v => v - 1)}>{t("上一页", "Previous")}</button><span>{page} / {Math.ceil(catalog.total / 24)}</span><button type="button" disabled={page * 24 >= catalog.total || busy} onClick={() => setPage(v => v + 1)}>{t("下一页", "Next")}</button></nav> : null}
  </section>;
}
