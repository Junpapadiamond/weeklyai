"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowUpRight } from "@phosphor-icons/react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { ExperiencePlayer } from "@/components/demo/experience-player";
import { ProductLiveDemo } from "@/components/demo/product-live-demo";
import { fetchPreparedDemo } from "@/lib/demo-loading";
import type { DemoResponse } from "@/lib/demo-experience";
import { resolveProductLogoSources } from "@/lib/product-utils";
import type { Product } from "@/types/api";

/** Page arrival only reads a prepared example. Generating requires a deliberate click. */
export function ProductDetailExample({ product }: { product: Product }) {
  const { t } = useSiteLocale();
  const [result, setResult] = useState<DemoResponse | null>(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [launch, setLaunch] = useState(false);
  const section = useRef<HTMLElement>(null);
  const id = product._id || product.id || product.name;
  useEffect(() => {
    const controller = new AbortController();
    fetchPreparedDemo(id, controller.signal).then(next => {
      if (!controller.signal.aborted) { setResult(next); setFailed(!next.success); }
    }).catch(() => { if (!controller.signal.aborted) setFailed(true); });
    return () => controller.abort();
  }, [id, attempt]);

  return <section ref={section} tabIndex={-1} id="try-demo" className="profile-example" aria-label={t("产品示例", "Product example")} aria-busy={!launch && !result && !failed}>
    <span className="profile-sr-only" role="status">{launch ? "" : result?.experience ? t("已有示例已加载。", "Prepared example loaded.") : failed ? t("示例加载失败，可以重新检查。", "The example could not load. You can check again.") : result ? t("暂时没有可展示的已有示例。", "No prepared example is available yet.") : t("正在读取已有示例。", "Loading a prepared example.")}</span>
    {launch ? <div className="profile-example-heading"><button type="button" onClick={() => { setLaunch(false); setAttempt(value => value + 1); section.current?.focus(); }}>{t("收起示例", "Close example")}</button></div> : null}
    {launch ? <ProductLiveDemo product={product} autoOpen compact anchorId={null} /> : result?.experience ? <ExperiencePlayer entry={result.experience} productName={product.name} website={product.website} {...resolveProductLogoSources(product)} embedded /> : <div className="profile-example-empty">
      <h2>{!result && !failed ? t("正在读取已有示例", "Loading a prepared example") : failed ? t("示例暂时未能加载", "The example could not be loaded") : result?.state === "generating" ? t("示例正在准备中", "An example is being prepared") : t("从一个具体场景了解产品", "Explore a concrete use case")}</h2>
      {result && !failed ? <p>{t("独立示例 · 非原厂输出", "Independent example · Not vendor output")}</p> : null}
      {!result && !failed ? <div className="profile-example-skeleton" aria-hidden="true"><span /><span /></div> : <div className="profile-example-actions">
        {failed || result?.state === "generating" ? <button type="button" onClick={() => { setFailed(false); setResult(null); setAttempt(value => value + 1); }}>{t("重新检查", "Check again")}</button> : result?.generation_available ? <button type="button" onClick={() => setLaunch(true)}>{t("生成独立示例", "Generate an illustrated example")}</button> : null}
        <Link href="/demo?filter=ready">{t("浏览已有示例", "Browse prepared examples")}<ArrowUpRight size={15} aria-hidden="true" /></Link>
      </div>}
      {result?.generation_available && !result.experience && !failed && result.state !== "generating" ? <small>{t("点击生成会使用 1 次今日生成额度，已有示例不扣额度。", "Generating uses one daily credit. Prepared examples use no credits.")}</small> : null}
    </div>}
  </section>;
}
