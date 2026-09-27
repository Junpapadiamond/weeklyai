"use client";

import { useEffect, useId, useState } from "react";
import Link from "next/link";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { ExperiencePlayer } from "./experience-player";
import { demoErrorMessage, readDemo, type DemoResponse } from "@/lib/demo-experience";
import type { Product } from "@/types/api";
import { resolveProductLogoSources } from "@/lib/product-utils";

export function ProductLiveDemo({ product, autoOpen = false, compact = false, onPrepared }: { product: Product; autoOpen?: boolean; compact?: boolean; onPrepared?: () => void }) {
  const { t } = useSiteLocale();
  const [open, setOpen] = useState(autoOpen);
  const [attempt, setAttempt] = useState(0);
  const [data, setData] = useState<DemoResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [phase, setPhase] = useState<"checking" | "generating">("checking");
  const [elapsed, setElapsed] = useState(0);
  const panelId = useId();
  const id = product._id || product.name;
  useEffect(() => {
    if (!busy) return;
    const started = Date.now();
    const timer = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(timer);
  }, [busy]);
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    async function run() {
      setBusy(true); setError(""); setData(null); setPhase("checking"); setElapsed(0);
      try {
        const url = "/api/v1/demos/product/" + encodeURIComponent(id);
        const signal = AbortSignal.any([controller.signal, AbortSignal.timeout(130000)]);
        let next = await readDemo(await fetch(url, { signal }));
        if (!controller.signal.aborted) setData(next);
        if (!next.success) throw new Error(next.error || "UNAVAILABLE");
        if (!next.experience && next.generation_available) {
          setPhase("generating");
          next = await readDemo(await fetch("/api/v1/demos/generate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ product_id: id }), signal }));
          if (next.state === "generating") {
            for (let i = 0; i < 35 && !next.experience; i++) {
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
        if (!controller.signal.aborted) setError(cause instanceof Error && cause.name === "TimeoutError" ? "SERVICE_UNAVAILABLE" : cause instanceof Error ? cause.message : "UNAVAILABLE");
      } finally { if (!controller.signal.aborted) setBusy(false); }
    }
    void run();
    return () => controller.abort();
  }, [open, id, attempt, onPrepared]);
  const limit = error === "DAILY_LIMIT";
  const errorCopy = demoErrorMessage(error);
  return <section id="try-demo" className="product-demo">
    {!compact ? <div className="demo-invitation"><div><span className="demo-eyebrow">{t("本站演示", "TRY BEFORE YOU SIGN UP")}</span><h2>{t("看看这个产品怎么用", "Open it. Experience the workflow.")}</h2><p>{t("根据公开资料制作的交互示例，帮助你理解使用流程。实际功能请以产品官网为准。", "No account. No prompt. Open a prepared experience or let AI build one from the product brief.")}</p></div><button type="button" className="demo-launch" aria-expanded={open} aria-controls={panelId} onClick={() => setOpen(v => !v)}>{open ? t("收起演示", "Close demo") : t("查看演示", "Try interactive demo")}<span aria-hidden="true">▷</span></button></div> : null}
    {open ? <div id={panelId} aria-busy={busy}>
      {busy ? <div className="experience-loading" role="status"><span className="demo-status-dot" /><h3>{phase === "checking" ? t("正在加载演示", "Opening the product experience") : t("正在生成演示", "Designing the interactive workspace")}</h3><p>{phase === "checking" ? t("正在查找已有演示，请稍候。", "Checking for a prepared experience") : t("正在根据产品资料生成示例，完成后会自动打开。", "Designing the workflow and validating its interface and outcomes")}</p><small>{t(`已等待 ${elapsed} 秒。首次生成需要一些时间，完成后可重复查看。`, `${elapsed}s elapsed. Prepared experiences open directly; new generation can take about a minute. Replays are free.`)}</small><div className="experience-loading-track" /></div> : null}
      {!busy && data?.experience ? <ExperiencePlayer key={data.experience.cache_key} entry={data.experience} productName={product.name} website={product.website} {...resolveProductLogoSources(product)} /> : null}
      {!busy && error ? <div className="experience-loading" role="status"><h3>{t(...errorCopy)}</h3><p>{t("可以先查看已有演示。生成失败后，本次额度会退回。", "Prepared experiences remain free to replay. Failed generations refund your personal credit.")}</p><div className="experience-actions"><Link href="/demo?filter=ready">{t("查看已有演示", "Browse ready experiences")} ↗</Link>{!limit && error !== "NOT_CONFIGURED" ? <button type="button" onClick={() => setAttempt(v => v + 1)}>{error === "PENDING" || error === "SERVICE_UNAVAILABLE" ? t("重新检查", "Check again") : t("重新生成", "Generate again")}</button> : null}</div></div> : null}
      {data?.quota ? <p className="experience-quota-note">{t("今日剩余生成次数：", "New generations remaining today: ")}<strong>{data.quota.remaining} / {data.quota.limit}</strong> · {t("已有演示不扣额度", "Cached experiences are free")}</p> : null}
    </div> : null}
  </section>;
}
