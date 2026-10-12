"use client";

import { useId, useState } from "react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { DemoWidget } from "@/components/demo/demo-widgets";
import type { DemoSpec } from "@/lib/demo-schema";

export function DemoPlayer({ spec, onRegenerate }: { spec: DemoSpec; onRegenerate?: () => void }) {
  const { locale, t } = useSiteLocale();
  const [step, setStep] = useState(0);
  const panelId = useId();
  const pick = (value: { zh: string; en: string }) =>
    locale === "en-US" ? value.en || value.zh : value.zh || value.en;
  const active = Math.min(step, spec.steps.length - 1);
  const current = spec.steps[active];
  // This renderer only shows prepared content and local interactions. A stored
  // sandbox tier or live-mode flag does not establish a real API execution.
  const disclosure = spec.tier === "simulation"
    ? t("独立虚构示例 · 非原厂输出", "Independent fictional example · Not vendor output")
    : spec.tier === "concept"
      ? t("独立概念说明 · 未运行设备", "Independent concept example · No device operation")
      : t("独立预设示例 · 非实时运行", "Independent prepared example · No live execution");

  return (
    <section className="demo-player" aria-label={pick(spec.title)}>
      <header className="demo-player__head">
        <span className="demo-player__product">{spec.product_name}</span>
        <h2>{pick(spec.title)}</h2>
      </header>

      <nav className="demo-steps" aria-label={t("选择示例内容", "Example sections")}>
        {spec.steps.map((item, index) => (
          <button key={item.id} type="button" className={`demo-step${index === active ? " is-active" : ""}`}
            onClick={() => setStep(index)} aria-pressed={index === active} aria-controls={panelId}>
            {pick(item.label)}
          </button>
        ))}
      </nav>

      <section id={panelId} className="demo-stage-body" aria-label={pick(current.label)}>
        <p className="demo-disclosure" role="note">{disclosure}</p>
        <DemoWidget key={`${spec.product_slug}-${current.id}`} widget={current.widget} evidence={spec.evidence} />
      </section>

      <details className="demo-explanation" key={`${spec.product_slug}-${current.id}-explanation`}>
        <summary>{t("了解这段示例", "About this example")}</summary>
        <p className="demo-narration">{pick(current.narration)}</p>
        <p className="demo-premise">{pick(spec.premise)}</p>
      </details>

      <details className="demo-evidence">
        <summary>{t("来源与制作说明", "Sources and provenance")}{spec.evidence.length ? ` (${spec.evidence.length})` : ""}</summary>
        <p className="demo-provenance">{t(
          `这是黑马雷达对 ${spec.product_name} 的独立讲解，不是其真实产品界面。`,
          `An independent DarkHorseRadar explanation of ${spec.product_name}, not its actual interface.`
        )}</p>
        {spec.vendor_status === "key_supplied" ? <p className="demo-provenance">{t(
          "资料记录厂商曾提供沙箱密钥；此页面只展示预设内容，不调用沙箱。产品评分独立。",
          "The record notes a vendor-supplied sandbox key. This page displays prepared content without calling that sandbox. Product scoring is independent."
        )}</p> : spec.vendor_status === "corrected" ? <p className="demo-provenance">{t(
          "资料记录厂商曾审阅此示例。产品评分独立。",
          "The record notes a vendor review of this example. Product scoring is independent."
        )}</p> : null}
        {spec.evidence.length ? <ul>
          {spec.evidence.map((item, index) => <li key={item.source_url + index}>
            <span>{item.claim}</span>
            <a href={item.source_url} target="_blank" rel="noopener noreferrer">{item.source_url}</a>
          </li>)}
        </ul> : null}
        <p className="demo-provenance">{spec.generated_at
          ? t(`制作日期 ${spec.generated_at.slice(0, 10)}${spec.reviewed_by ? " · 已人工审阅" : " · 尚未人工审阅"}`,
            `Prepared ${spec.generated_at.slice(0, 10)}${spec.reviewed_by ? " · Human-reviewed" : " · Not yet human-reviewed"}`)
          : t("由黑马雷达手工制作。", "Hand-authored by DarkHorseRadar.")}
        </p>
        <div className="demo-provenance-actions">
          <a href="/demo-feedback">{t("反馈示例中的问题", "Report an issue with this example")}</a>
          {onRegenerate ? <button type="button" className="demo-btn" onClick={onRegenerate}>
            {t("重新生成示例", "Regenerate example")}
          </button> : null}
        </div>
      </details>
    </section>
  );
}
