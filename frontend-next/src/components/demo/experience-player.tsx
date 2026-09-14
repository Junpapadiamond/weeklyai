"use client";

import { useRef, useState } from "react";
import { ArrowLeft, ArrowRight, Check, Download, RotateCcw } from "lucide-react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import type { ExperienceEntry } from "@/lib/demo-experience";
import { exampleSpec } from "@/lib/live-demo";
import { DemoAppPreview } from "./demo-app-preview";
import { SmartLogo } from "@/components/common/smart-logo";

export function ExperiencePlayer({ entry, productName, website, logoUrl, secondaryLogoUrl }: { entry: ExperienceEntry; productName: string; website?: string; logoUrl?: string; secondaryLogoUrl?: string }) {
  const { locale, t } = useSiteLocale();
  const lang = locale === "en-US" ? "en" : "zh";
  const { spec } = entry;
  const [index, setIndex] = useState(0);
  const [choices, setChoices] = useState<Record<string, string>>({});
  const [dials, setDials] = useState<Record<string, number>>({});
  const [reviews, setReviews] = useState<Record<string, boolean>>({});
  const [revision, setRevision] = useState(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const complete = index === spec.steps.length;
  const step = spec.steps[Math.min(index, spec.steps.length - 1)];
  const selected = step.options.find(o => o.id === choices[step.id]);
  const dialValue = dials[step.id] ?? step.dial?.initial ?? 0;
  const canContinue = !!selected && (step.widget !== "review" || reviews[step.id]);
  function move(next: number) { setIndex(next); requestAnimationFrame(() => { heading.current?.focus({ preventScroll: true }); heading.current?.scrollIntoView({ block: "start", behavior: "instant" }); }); }
  function download() {
    const lines = [productName + " / WeeklyAI", t("流程模拟 · 示例数据 · 非官方产品", "Workflow simulation · Example data · Unofficial"), spec.headline[lang],
      ...spec.steps.flatMap(s => {
        const choice = s.options.find(o => o.id === choices[s.id]);
        return [s.title[lang], choice?.label[lang] || "", choice?.output[lang] || "",
          s.dial ? (dials[s.id] ?? s.dial.initial) + " " + s.dial.unit[lang] : ""];
      }), spec.takeaway[lang], ...spec.sources.map(s => s.url)];
    const url = URL.createObjectURL(new Blob([lines.join("\n\n")], { type: "text/plain;charset=utf-8" }));
    const a = document.createElement("a"); a.href = url; a.download = "weeklyai-demo.txt"; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <div className="experience-shell">
    <header className="experience-top"><div><SmartLogo className="demo-product-logo" name={productName} logoUrl={logoUrl} secondaryLogoUrl={secondaryLogoUrl} website={website} trustPrimaryLogo size={29} /><strong>{productName}</strong><span className="experience-origin">{entry.origin === "ai" ? t("AI 现场生成", "Generated on demand") : t("已准备好", "Ready to explore")}</span></div>
      <span className="experience-disclosure">{spec.tier === "concept" ? t("概念体验", "Concept explorer") : t("流程模拟", "Workflow simulation")} · {t("示例数据 · 非官方产品", "Example data · Unofficial")}</span></header>
    <div className="experience-body">
      <aside className="experience-rail"><span className="demo-eyebrow">A PRODUCT, EXPERIENCED.</span><h3>{spec.headline[lang]}</h3><p>{spec.scenario[lang]}</p>
        <ol>{spec.steps.map((s, i) => <li key={s.id}><button type="button" disabled={i > index} aria-current={index === i ? "step" : undefined} onClick={() => move(i)}><span>{i < index ? <Check size={14} /> : String(i + 1).padStart(2, "0")}</span>{s.title[lang]}</button></li>)}</ol>
        <span className="experience-free">{t("体验内的操作不消耗生成额度", "Interactions use no generation credits")}</span>
      </aside>
      <div className="experience-stage">
        <div className="experience-stage-meta"><span>{complete ? "EXPERIENCE COMPLETE" : "STEP " + String(index + 1).padStart(2, "0") + " / " + String(spec.steps.length).padStart(2, "0")}</span><button type="button" onClick={() => { setChoices({}); setDials({}); setReviews({}); setRevision(v => v + 1); move(0); }}><RotateCcw size={13} />{t("重新体验", "Start over")}</button></div>
        {complete ? <div className="experience-finish">
          <span className="experience-done"><Check size={26} /></span><h2 ref={heading} tabIndex={-1}>{t("这就是它的工作方式。", "Now you know the workflow.")}</h2><p>{spec.takeaway[lang]}</p>
          <div className="experience-summary">{spec.steps.map(s => <div key={s.id}><span>{s.title[lang]}</span><strong>{s.options.find(o => o.id === choices[s.id])?.label[lang]}</strong></div>)}</div>
          <div className="experience-actions"><button type="button" className="demo-launch" onClick={download}><Download size={16} />{t("下载体验结果", "Download your result")}</button>{website ? <a href={website} target="_blank" rel="noopener noreferrer">{t("去官网深入体验", "Explore the real product")} ↗</a> : null}</div>
        </div> : <div key={step.id} className="experience-step">
          <h2 ref={heading} tabIndex={-1}>{step.title[lang]}</h2><p>{step.instruction[lang]}</p>
          <div className={"experience-options " + (step.widget === "compare" ? "experience-options--compare" : "")}>
            {step.options.map(option => <button key={option.id} type="button" aria-pressed={selected?.id === option.id} onClick={() => { setChoices(old => ({ ...old, [step.id]: option.id })); setReviews(old => ({ ...old, [step.id]: false })); }}>
              <span className="experience-radio">{selected?.id === option.id ? <Check size={13} /> : null}</span><strong>{option.label[lang]}</strong>
              {step.widget === "compare" ? <span>{option.output[lang]}</span> : <ArrowRight size={15} />}
            </button>)}
          </div>
          {step.dial ? <div className="experience-dial"><label htmlFor={"dial-" + step.id}>{step.dial.unit[lang]}<strong>{dialValue}</strong></label><input id={"dial-" + step.id} type="range" min={step.dial.min} max={step.dial.max} value={dialValue} onChange={event => setDials(old => ({ ...old, [step.id]: Number(event.target.value) }))} /><div>{step.dial.result_label[lang]}<strong>{dialValue * step.dial.factor}</strong></div><small>{t("演示计算：输入 × ", "Example calculation: input × ")}{step.dial.factor}{t("，并非真实测算。", "; not a real estimate.")}</small></div> : null}
          {selected ? <div className="experience-output" aria-live="polite"><span className="demo-eyebrow">{t("你的操作结果 / 示例", "YOUR RESULT / EXAMPLE")}</span><p>{selected.output[lang]}</p>
            {step.widget === "app" && step.app_kind ? <DemoAppPreview key={revision} spec={exampleSpec(step.app_kind, lang === "en")} en={lang === "en"} /> : null}
          </div> : <div className="experience-empty">{t("选一个选项，看看下一步会发生什么。", "Make a choice to see what happens next.")}</div>}
          {step.widget === "review" && selected ? <label className="experience-review"><input type="checkbox" checked={!!reviews[step.id]} onChange={e => setReviews(old => ({ ...old, [step.id]: e.target.checked }))} />{t("已检查示例内容，继续下一步", "I reviewed the example. Continue.")}</label> : null}
          <nav className="experience-controls" aria-label={t("体验步骤", "Experience steps")}><button type="button" disabled={index === 0} onClick={() => move(index - 1)}><ArrowLeft size={16} />{t("上一步", "Back")}</button><button type="button" className="demo-launch" disabled={!canContinue} onClick={() => move(index + 1)}>{index === spec.steps.length - 1 ? t("查看体验结果", "See your result") : t("继续", "Continue")}<ArrowRight size={16} /></button></nav>
        </div>}
      </div>
    </div>
    <footer className="experience-sources"><span>{t("产品资料", "Product sources")}</span>{spec.sources.map((source, i) => <a href={source.url} target="_blank" rel="noopener noreferrer" key={source.url + i}>{source.label[lang]} ↗</a>)}<span>{t("依据公开资料设计，无法代表真实模型质量。", "Based on public information; not a measure of model quality.")}</span></footer>
  </div>;
}
