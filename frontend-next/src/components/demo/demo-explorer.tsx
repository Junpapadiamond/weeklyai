"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { SmartLogo } from "@/components/common/smart-logo";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { DemoPlayer } from "@/components/demo/demo-player";
import {
  demoSlug,
  fetchDemo,
  fetchDemoStatus,
  fetchReadyDemoSlugs,
  generateDemo,
  searchProductsForDemos,
  type DemoError,
  type DemoStatus,
} from "@/lib/demo-client";
import type { DemoSpec } from "@/lib/demo-schema";
import {
  getLocalizedProductDescription,
  getProductScore,
  resolveProductLogoSources,
} from "@/lib/product-utils";
import type { Product } from "@/types/api";

type Phase =
  | { kind: "idle" }
  | { kind: "loading"; productName: string; building: boolean }
  | { kind: "ready"; spec: DemoSpec }
  | { kind: "failed"; error: DemoError; message: string };

function productKey(product: Product): string {
  return String(product._id || product.id || product.name || "");
}

export function DemoExplorer({ products }: { products: Product[] }) {
  const { locale, t } = useSiteLocale();
  const [query, setQuery] = useState("");
  // Server-side results, tagged with the term they answer so a stale response
  // never renders under a newer query.
  const [remote, setRemote] = useState<{ term: string; items: Product[] }>({ term: "", items: [] });
  const [readyOnly, setReadyOnly] = useState(false);
  const [ready, setReady] = useState<Set<string>>(new Set());
  const [status, setStatus] = useState<DemoStatus | null>(null);
  const [phase, setPhase] = useState<Phase>({ kind: "idle" });
  const [selected, setSelected] = useState<Product | null>(null);
  // Generation has no meaningful percentage, so the UI shows seconds actually
  // waited. `run` increments per attempt so the counter restarts each time.
  const [run, setRun] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const abortRef = useRef<AbortController | null>(null);
  const resultRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    void fetchReadyDemoSlugs(controller.signal).then((slugs) => setReady(new Set(slugs)));
    void fetchDemoStatus(controller.signal).then(setStatus);
    return () => controller.abort();
  }, []);

  useEffect(() => () => abortRef.current?.abort(), []);

  useEffect(() => {
    if (phase.kind !== "loading") return;
    const timer = window.setInterval(() => setElapsed((seconds) => seconds + 1), 1000);
    return () => window.clearInterval(timer);
  }, [phase.kind, run]);

  // A typed query goes to the search API rather than filtering the loaded page,
  // because the initial grid is only the top of the catalog and the point of
  // this page is that any product can be picked.
  const term = query.trim();
  const usingRemote = term.length >= 2;
  const searching = usingRemote && remote.term !== term;

  useEffect(() => {
    const needle = query.trim();
    if (needle.length < 2) return;
    const controller = new AbortController();
    const handle = window.setTimeout(() => {
      void searchProductsForDemos(needle, controller.signal).then((items) => setRemote({ term: needle, items }));
    }, 300);
    return () => {
      window.clearTimeout(handle);
      controller.abort();
    };
  }, [query]);

  const filtered = useMemo(() => {
    const source = usingRemote ? (remote.term === term ? remote.items : []) : products;
    return source.filter((product) => !readyOnly || ready.has(demoSlug(product.name))).slice(0, 60);
  }, [products, remote, term, usingRemote, readyOnly, ready]);

  async function open(product: Product, refresh = false) {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setSelected(product);

    const key = productKey(product);
    const isReady = ready.has(demoSlug(product.name)) && !refresh;

    setRun((value) => value + 1);
    setElapsed(0);
    setPhase({ kind: "loading", productName: product.name, building: !isReady });
    window.setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 0);

    // Ask for an existing demo first whatever the ready list says: it is a hint
    // for labelling the cards, not the record of what exists.
    if (!refresh) {
      const existing = await fetchDemo(key, controller.signal);
      if (controller.signal.aborted) return;
      if (existing.ok) {
        setReady((prev) => new Set(prev).add(existing.spec.product_slug));
        setPhase({ kind: "ready", spec: existing.spec });
        return;
      }
    }

    const built = await generateDemo(key, { refresh, signal: controller.signal });
    if (controller.signal.aborted) return;
    if (built.ok) {
      setReady((prev) => new Set(prev).add(built.spec.product_slug));
      setPhase({ kind: "ready", spec: built.spec });
      return;
    }
    setPhase({ kind: "failed", error: built.error, message: built.message });
  }

  const failureCopy: Record<DemoError, string> = {
    NOT_CONFIGURED: t(
      "实时生成尚未接入。已经建好的演示仍可查看——用上面的「可立即查看」筛选。",
      "Live generation is not connected yet. Pre-built demos still work — use the 'Ready now' filter above."
    ),
    PROVIDER_UNAVAILABLE: t("生成服务暂时不可用，请稍后再试。", "The generator is unavailable right now. Try again shortly."),
    INVALID_SPEC: t(
      "生成的演示未通过校验，因此没有展示。宁可不展示，也不展示可能失真的内容。",
      "The generated demo failed validation, so it was not shown. We would rather show nothing than something possibly wrong."
    ),
    TOO_MANY_REQUESTS: t(
      `生成有频率限制${status ? `（每小时 ${status.generateLimitPerHour} 次）` : ""}。已建好的演示不受影响。`,
      `Generation is rate limited${status ? ` (${status.generateLimitPerHour}/hour)` : ""}. Pre-built demos are unaffected.`
    ),
    NOT_FOUND: t("找不到这个产品。", "That product could not be found."),
    NOT_GENERATED: t("这个产品还没有演示。", "No demo exists for this product yet."),
    UNAVAILABLE: t("请求没有完成，请重试。", "The request did not complete. Please try again."),
  };

  return (
    <section className="section demo-explorer">
      <header className="section-header">
        <h1 className="section-title">{t("交互演示", "Interactive demos")}</h1>
        <p className="section-desc">
          {t(
            "挑一个产品，直接看它做什么——不用注册，不用读文档。已建好的立即打开，其余的现场生成。",
            "Pick a product and see what it does — no signup, no docs. Built ones open instantly; the rest are generated on the spot."
          )}
        </p>
      </header>

      <div className="demo-controls">
        <label className="demo-search">
          <span className="sr-only">{t("搜索产品", "Search products")}</span>
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.currentTarget.value)}
            placeholder={t("搜索产品、类别或国家", "Search products, categories or countries")}
          />
        </label>
        <label className="demo-toggle">
          <input type="checkbox" checked={readyOnly} onChange={(event) => setReadyOnly(event.currentTarget.checked)} />
          {t(`可立即查看（${ready.size}）`, `Ready now (${ready.size})`)}
        </label>
        {status && !status.generationAvailable ? (
          <span className="demo-note-inline">
            {t("实时生成未接入，可查看已建好的演示。", "Live generation is off; pre-built demos are available.")}
          </span>
        ) : null}
      </div>

      <ul className="demo-grid">
        {filtered.map((product) => {
          const slug = demoSlug(product.name);
          const isReady = ready.has(slug);
          const logos = resolveProductLogoSources(product);
          return (
            <li key={productKey(product)}>
              <button
                type="button"
                className={`demo-card${selected && productKey(selected) === productKey(product) ? " is-selected" : ""}`}
                onClick={() => void open(product)}
              >
                <span className="demo-card__top">
                  <SmartLogo
                    name={product.name}
                    logoUrl={logos.logoUrl}
                    secondaryLogoUrl={logos.secondaryLogoUrl}
                    website={product.website}
                    size={30}
                  />
                  <span className="demo-card__name">{product.name}</span>
                  <span className={`demo-card__state${isReady ? " is-ready" : ""}`}>
                    {isReady ? t("可查看", "Ready") : t("现场生成", "Build")}
                  </span>
                </span>
                <span className="demo-card__desc">
                  {getLocalizedProductDescription(product, locale).slice(0, 120)}
                </span>
                <span className="demo-card__meta">
                  <span>{getProductScore(product)}/5</span>
                  {(product.categories || []).slice(0, 2).map((category) => (
                    <span key={category}>{category}</span>
                  ))}
                </span>
              </button>
            </li>
          );
        })}
      </ul>

      {!filtered.length ? (
        <p className="demo-empty">
          {searching
            ? t("正在搜索全部产品…", "Searching the whole catalog…")
            : t("没有匹配的产品，换个关键词试试。", "No products match. Try a different search.")}
        </p>
      ) : null}

      <div className="demo-result" ref={resultRef}>
        {phase.kind === "loading" ? (
          <div className="demo-loading" role="status" aria-live="polite">
            <strong>
              {phase.building
                ? t(`正在为 ${phase.productName} 生成演示…`, `Building a demo for ${phase.productName}…`)
                : t(`正在打开 ${phase.productName}…`, `Opening ${phase.productName}…`)}
            </strong>
            <span>
              {phase.building
                ? t(
                    `已用 ${elapsed} 秒。首次生成通常需要 15–40 秒，之后所有人都能立即打开。`,
                    `${elapsed}s elapsed. A first build usually takes 15–40 seconds; after that it opens instantly for everyone.`
                  )
                : t(`已用 ${elapsed} 秒。`, `${elapsed}s elapsed.`)}
            </span>
            <button
              type="button"
              className="demo-btn"
              onClick={() => {
                abortRef.current?.abort();
                setPhase({ kind: "idle" });
              }}
            >
              {t("取消", "Cancel")}
            </button>
          </div>
        ) : null}

        {phase.kind === "failed" ? (
          <div className="demo-failed" role="alert">
            <strong>{t("没能生成这个演示", "Could not build that demo")}</strong>
            <p>{phase.message || failureCopy[phase.error]}</p>
            {selected && phase.error !== "NOT_CONFIGURED" ? (
              <button type="button" className="demo-btn" onClick={() => void open(selected)}>
                {t("重试", "Try again")}
              </button>
            ) : null}
          </div>
        ) : null}

        {phase.kind === "ready" ? (
          <DemoPlayer spec={phase.spec} onRegenerate={selected ? () => void open(selected, true) : undefined} />
        ) : null}
      </div>
    </section>
  );
}
