"use client";

import { useEffect, useId, useState } from "react";
import Link from "next/link";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { ExperiencePlayer } from "./experience-player";
import { readDemo, type DemoResponse } from "@/lib/demo-experience";
import type { Product } from "@/types/api";
import { resolveProductLogoSources } from "@/lib/product-utils";

export function ProductLiveDemo({ product, autoOpen = false, compact = false, onPrepared }: { product: Product; autoOpen?: boolean; compact?: boolean; onPrepared?: () => void }) {
  const { t } = useSiteLocale();
  const [open, setOpen] = useState(autoOpen);
  const [attempt, setAttempt] = useState(0);
  const [data, setData] = useState<DemoResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const panelId = useId();
  const id = product._id || product.name;
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    async function run() {
      setBusy(true); setError(""); setData(null);
      try {
        const url = "/api/v1/demos/product/" + encodeURIComponent(id);
        const signal = AbortSignal.any([controller.signal, AbortSignal.timeout(85000)]);
        let next = await readDemo(await fetch(url, { signal }));
        if (!next.success) throw new Error(next.error || "UNAVAILABLE");
        if (!next.experience && next.generation_available) {
          next = await readDemo(await fetch("/api/v1/demos/generate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ product_id: id }), signal }));
          if (next.state === "generating") {
            for (let i = 0; i < 20 && !next.experience; i++) {
              await new Promise<void>((resolve, reject) => {
                const abort = () => { clearTimeout(timer); reject(new Error("ABORTED")); };
                const timer = setTimeout(() => { signal.removeEventListener("abort", abort); resolve(); }, 3000);
                signal.addEventListener("abort", abort, { once: true });
                if (signal.aborted) abort();
              });
              next = await readDemo(await fetch(url, { signal }));
            }
          }
        }
        if (controller.signal.aborted) return;
        setData(next);
        onPrepared?.();
        if (!next.experience) setError(next.error || (next.generation_available ? "PENDING" : "NOT_CONFIGURED"));
      } catch (cause) {
        if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : "UNAVAILABLE");
      } finally { if (!controller.signal.aborted) setBusy(false); }
    }
    void run();
    return () => controller.abort();
  }, [open, id, attempt, onPrepared]);
  const limit = error === "DAILY_LIMIT";
  return <section id="try-demo" className="product-demo">
    {!compact ? <div className="demo-invitation"><div><span className="demo-eyebrow">TRY BEFORE YOU SIGN UP</span><h2>{t("点开，走一遍它的工作流程。", "Open it. Experience the workflow.")}</h2><p>{t("不用注册，不用写需求。已有演示直接打开，其余由 AI 按产品资料生成。", "No account. No prompt. Open a prepared experience or let AI build one from the product brief.")}</p></div><button type="button" className="demo-launch" aria-expanded={open} aria-controls={panelId} onClick={() => setOpen(v => !v)}>{open ? t("收起试用", "Close demo") : t("交互试用", "Try interactive demo")}<span aria-hidden="true">▷</span></button></div> : null}
    {open ? <div id={panelId} aria-busy={busy}>
      {busy ? <div className="experience-loading" role="status"><span className="demo-status-dot" /><h3>{t("正在准备这个产品的交互体验", "Preparing this product’s experience")}</h3><p>{t("读取产品资料 → 设计完整流程 → 校验可交互结果", "Read the brief → Design the workflow → Validate the experience")}</p><small>{t("首次生成可能需要约 30 秒。生成后可反复打开。", "The first generation may take around 30 seconds. Replays are free.")}</small><div className="experience-loading-track" /></div> : null}
      {!busy && data?.experience ? <ExperiencePlayer key={data.experience.cache_key} entry={data.experience} productName={product.name} website={product.website} {...resolveProductLogoSources(product)} /> : null}
      {!busy && error ? <div className="experience-loading" role="status"><h3>{limit ? t("今日新建演示额度已用完", "Today’s generation limit has been reached") : error === "NOT_CONFIGURED" || error === "GENERATOR_NOT_CONFIGURED" ? t("这个产品的演示还在准备中", "This product’s demo is not ready yet") : error === "PENDING" ? t("演示仍在生成，请稍后重新打开", "Still generating. Check back shortly.") : t("这次生成没有完成", "This generation did not finish")}</h3><p>{t("已准备好的演示仍可免费、无限次体验。失败的生成会返还个人额度。", "Prepared experiences remain free to replay. Failed generations refund your personal credit.")}</p><div className="experience-actions"><Link href="/demo">{t("浏览可立即体验的产品", "Browse ready experiences")} ↗</Link>{!limit && error !== "NOT_CONFIGURED" ? <button type="button" onClick={() => setAttempt(v => v + 1)}>{t("重新检查", "Check again")}</button> : null}</div></div> : null}
      {data?.quota ? <p className="experience-quota-note">{t("今日还可新建 ", "New generations remaining today: ")}<strong>{data.quota.remaining} / {data.quota.limit}</strong> · {t("已有演示不扣额度", "Cached experiences are free")}</p> : null}
    </div> : null}
  </section>;
}
