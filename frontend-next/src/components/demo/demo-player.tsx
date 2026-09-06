"use client";

import { useState } from "react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { DemoWidget } from "@/components/demo/demo-widgets";
import { isReconstruction, type DemoSpec } from "@/lib/demo-schema";

/**
 * The labelling badge required by the Tier 2 contract.
 *
 * It is rendered above the demo body and repeated at the end, it is not
 * dismissible, and it names the product it disclaims. Deleting it is a
 * publishing decision, not a styling one — do not make it conditional on
 * viewport, scroll position or any user preference.
 */
function DemoBadge({ spec }: { spec: DemoSpec }) {
  const { t } = useSiteLocale();
  if (isReconstruction(spec)) {
    return (
      <p className="demo-badge demo-badge--reconstruction" role="note">
        <strong>{t("示意性演示", "Illustrative reconstruction")}</strong>
        {t(
          `非真实产品界面。与 ${spec.product_name} 无关联、未获其背书。`,
          `Not the real product interface. Not affiliated with or endorsed by ${spec.product_name}.`
        )}
      </p>
    );
  }
  if (spec.tier === "concept") {
    return (
      <p className="demo-badge demo-badge--concept" role="note">
        <strong>{t("概念解读", "Concept explainer")}</strong>
        {t(
          `这是对 ${spec.product_name} 所处位置的独立解读，不是产品界面演示。`,
          `An independent explanation of where ${spec.product_name} sits. Not a product interface.`
        )}
      </p>
    );
  }
  return (
    <p className="demo-badge demo-badge--sandbox" role="note">
      <strong>{t("独立制作", "Independently built")}</strong>
      {t(
        `由 WeeklyAI 制作，未获 ${spec.product_name} 背书。`,
        `Built by WeeklyAI. Not endorsed by ${spec.product_name}.`
      )}
    </p>
  );
}

function VendorNote({ spec }: { spec: DemoSpec }) {
  const { t } = useSiteLocale();
  if (spec.vendor_status === "none" || spec.vendor_status === "contacted") return null;
  const detail =
    spec.vendor_status === "key_supplied"
      ? t(
          `${spec.product_name} 提供了本演示使用的沙箱密钥。评分独立进行。`,
          `${spec.product_name} supplied the sandbox key used here. Scoring is independent.`
        )
      : t(
          `${spec.product_name} 审阅过本演示的准确性。评分独立进行。`,
          `${spec.product_name} reviewed this demo for accuracy. Scoring is independent.`
        );
  return (
    <p className="demo-disclosure" role="note">
      {detail}
    </p>
  );
}

export function DemoPlayer({ spec, onRegenerate }: { spec: DemoSpec; onRegenerate?: () => void }) {
  const { locale, t } = useSiteLocale();
  const [step, setStep] = useState(0);
  const pick = (value: { zh: string; en: string }) =>
    locale === "en-US" ? value.en || value.zh : value.zh || value.en;

  const current = spec.steps[Math.min(step, spec.steps.length - 1)];
  const isLast = step >= spec.steps.length - 1;

  return (
    <section className="demo-player" aria-label={pick(spec.title)}>
      <header className="demo-player__head">
        <div className="demo-player__titles">
          <h2>{pick(spec.title)}</h2>
          <p className="demo-premise">{pick(spec.premise)}</p>
        </div>
        <DemoBadge spec={spec} />
        <VendorNote spec={spec} />
      </header>

      <nav className="demo-steps" aria-label={t("演示步骤", "Demo steps")}>
        {spec.steps.map((item, index) => (
          <button
            key={item.id}
            type="button"
            className={`demo-step${index === step ? " is-active" : ""}${index < step ? " is-done" : ""}`}
            onClick={() => setStep(index)}
            aria-current={index === step ? "step" : undefined}
          >
            <span className="demo-step__n">{index + 1}</span>
            <span className="demo-step__label">{pick(item.label)}</span>
          </button>
        ))}
      </nav>

      <div className="demo-stage-body">
        <p className="demo-narration">{pick(current.narration)}</p>
        <DemoWidget widget={current.widget} evidence={spec.evidence} />
      </div>

      <div className="demo-player__controls">
        <button type="button" className="demo-btn" onClick={() => setStep(Math.max(0, step - 1))} disabled={step === 0}>
          {t("上一步", "Back")}
        </button>
        <span className="demo-progress" aria-live="polite">
          {step + 1} / {spec.steps.length}
        </span>
        <button
          type="button"
          className="demo-btn demo-btn--primary"
          onClick={() => setStep(Math.min(spec.steps.length - 1, step + 1))}
          disabled={isLast}
        >
          {t("下一步", "Next")}
        </button>
      </div>

      {spec.evidence.length ? (
        <details className="demo-evidence">
          <summary>{t(`来源（${spec.evidence.length}）`, `Sources (${spec.evidence.length})`)}</summary>
          <ul>
            {spec.evidence.map((item, index) => (
              <li key={index}>
                <span>{item.claim}</span>
                <a href={item.source_url} target="_blank" rel="noopener noreferrer">
                  {item.source_url}
                </a>
              </li>
            ))}
          </ul>
        </details>
      ) : null}

      <footer className="demo-player__foot">
        <DemoBadge spec={spec} />
        <p className="demo-provenance">
          {spec.generated_at
            ? t(
                `生成于 ${spec.generated_at.slice(0, 10)}${spec.reviewed_by ? "，已人工审阅" : "，尚未人工审阅"}。`,
                `Generated ${spec.generated_at.slice(0, 10)}${spec.reviewed_by ? ", human-reviewed" : ", not yet human-reviewed"}.`
              )
            : t("由 WeeklyAI 手工编写。", "Hand-authored by WeeklyAI.")}{" "}
          <a href="/support">{t("发现错误？告诉我们，48 小时内处理。", "Something wrong? Tell us — we fix or remove within 48 hours.")}</a>
        </p>
        {onRegenerate ? (
          <button type="button" className="demo-btn" onClick={onRegenerate}>
            {t("重新生成", "Rebuild this demo")}
          </button>
        ) : null}
      </footer>
    </section>
  );
}
