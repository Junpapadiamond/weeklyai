"use client";

import { useRef, useState } from "react";
import { ArrowLeft, ArrowRight, Check, Download, ArrowCounterClockwise } from "@phosphor-icons/react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { availableExperienceOptions, updateExperienceChoice, type ExperienceEntry } from "@/lib/demo-experience";
import { exampleSpec } from "@/lib/live-demo";
import { DemoAppPreview } from "./demo-app-preview";
import { SmartLogo } from "@/components/common/smart-logo";
import { ExperienceWorkspace } from "./experience-workspace";

export function ExperiencePlayer({ entry, productName, website, logoUrl, secondaryLogoUrl }: { entry: ExperienceEntry; productName: string; website?: string; logoUrl?: string; secondaryLogoUrl?: string }) {
  const { locale, t } = useSiteLocale();
  const lang = locale === "en-US" ? "en" : "zh";
  const { spec } = entry;
  const [index, setIndex] = useState(0);
  const [choices, setChoices] = useState<Record<string, string>>({});
  const [dials, setDials] = useState<Record<string, number>>({});
  const [reviews, setReviews] = useState<Record<string, boolean>>({});
  const [revision, setRevision] = useState(0);
  const [customBrief, setCustomBrief] = useState<string | null>(null);
  const [ratio, setRatio] = useState<"9:16" | "16:9">("9:16");
  const brief = customBrief ?? spec.workspace?.initial[lang] ?? spec.scenario[lang];
  const heading = useRef<HTMLHeadingElement>(null);
  const complete = index === spec.steps.length;
  const step = spec.steps[Math.min(index, spec.steps.length - 1)];
  const options = availableExperienceOptions(step, choices);
  const selected = options.find(o => o.id === choices[step.id]);
  const dialValue = dials[step.id] ?? step.dial?.initial ?? 0;
  const canContinue = !!selected && (step.widget !== "review" || reviews[step.id]);
  function choose(optionId: string) {
    if (selected?.id === optionId) return;
    setChoices(old => updateExperienceChoice(spec, old, step.id, optionId));
    const earlier = new Set(spec.steps.slice(0, index).map(s => s.id));
    setReviews(old => Object.fromEntries(Object.entries(old).filter(([id]) => earlier.has(id))));
    setDials(old => Object.fromEntries(Object.entries(old).filter(([id]) => earlier.has(id))));
  }
  function move(next: number) { setIndex(next); requestAnimationFrame(() => { heading.current?.focus({ preventScroll: true }); heading.current?.scrollIntoView({ block: "start", behavior: "instant" }); }); }
  function download() {
    const lines = [productName + " / Darkhorse Radar", t("模拟摘要 · 虚构示例 · 非官方", "Simulation summary · Fictional examples · Unofficial"),
      t("本摘要来自本站示例，没有运行原厂产品、开展访谈或访问原始视频。", "This summary comes from a prepared walkthrough. The vendor product was not run; no interviews or source-video access took place."), spec.headline[lang],
      brief, ...(spec.workspace?.kind === "video" || spec.workspace?.kind === "image" ? [ratio] : []), ...spec.steps.flatMap(s => {
        const choice = s.options.find(o => o.id === choices[s.id]);
        return [s.title[lang], choice?.label[lang] || "", choice?.output[lang] || "",
          s.dial ? (dials[s.id] ?? s.dial.initial) + " " + s.dial.unit[lang] : ""];
      }), spec.takeaway[lang], ...spec.sources.map(s => s.url)];
    const url = URL.createObjectURL(new Blob([lines.join("\n\n")], { type: "text/plain;charset=utf-8" }));
    const a = document.createElement("a"); a.href = url; a.download = "darkhorseradar-demo.txt"; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <div className="experience-shell">
    {spec.product_context ? <section className="experience-product-context" aria-label={t("真实产品与本站示例", "The real product and this walkthrough")}>
      <div><span className="demo-eyebrow">{t("先了解产品", "WHAT THE PRODUCT DOES")}</span><h3>{productName}</h3><p>{spec.product_context.job[lang]}</p>
        <dl><div><dt>{t("你提供", "You provide")}</dt><dd>{spec.product_context.input[lang]}</dd></div><div><dt>{t("厂商描述的交付物", "Vendor-described output")}</dt><dd>{spec.product_context.output[lang]}</dd></div></dl>
        <a href={spec.product_context.source_url} target="_blank" rel="noopener noreferrer">{t("查看厂商说明", "Read the vendor’s explanation")} ↗</a></div>
      <div className="experience-vendor-trial"><strong>{t("想体验真实的 AI 访谈？", "Want to try the actual AI interviewer?")}</strong><p>{spec.product_context.trial_note[lang]}</p><a className="demo-launch" href={spec.product_context.trial_url} target="_blank" rel="noopener noreferrer">{t("前往官网体验入口", "Open the official trial page")} ↗</a><small>{t("下方为本站制作的交互讲解。", "Below: an independent, fictional walkthrough.")}</small></div>
    </section> : null}
    <header className="experience-top"><div><SmartLogo className="demo-product-logo" name={productName} logoUrl={logoUrl} secondaryLogoUrl={secondaryLogoUrl} website={website} trustPrimaryLogo size={29} /><strong>{productName}</strong><span className="experience-origin">{entry.origin === "ai" ? t("预先生成的 AI 示例", "Prepared AI example") : t("已准备的示例", "Prepared example")}</span></div>
      <span className="experience-disclosure">{spec.tier === "concept" ? t("概念演示", "Concept explorer") : t("流程演示", "Workflow simulation")} · {t("示例数据 · 非官方演示", "Example data · Unofficial")}</span></header>
    <div className="experience-body">
      <aside className="experience-rail"><span className="demo-eyebrow">{t("通过示例理解流程", "LEARN THROUGH AN EXAMPLE")}</span><h3>{spec.headline[lang]}</h3><p>{spec.scenario[lang]}</p>
        <ol>{spec.steps.map((s, i) => <li key={s.id}><button type="button" disabled={i > index} aria-current={index === i ? "step" : undefined} onClick={() => move(i)}><span>{i < index ? <Check size={14} /> : String(i + 1).padStart(2, "0")}</span>{s.title[lang]}</button></li>)}</ol>
        <span className="experience-free">{t("查看和操作演示不消耗生成次数", "Interactions use no generation credits")}</span>
      </aside>
      <div className="experience-stage">
        <div className="experience-stage-meta"><span>{complete ? t("模拟完成", "SIMULATION COMPLETE") : t(`第 ${index + 1} 步，共 ${spec.steps.length} 步`, "STEP " + String(index + 1).padStart(2, "0") + " / " + String(spec.steps.length).padStart(2, "0"))}</span><button type="button" onClick={() => { setChoices({}); setDials({}); setReviews({}); setCustomBrief(null); setRatio("9:16"); setRevision(v => v + 1); move(0); }}><ArrowCounterClockwise size={13} />{t("重新开始", "Start over")}</button></div>
        <div className="experience-simulation-note"><strong>{t("本站模拟 · 虚构示例", "SIMULATION ONLY · FICTIONAL EXAMPLES")}</strong><p>{t("选择不同选项，了解决策如何影响示例摘要。这里没有运行原厂产品，也没有开展真实访谈或访问原始视频。", "Explore how choices affect an example summary. The vendor product is not running here; no real interviews or source videos are used.")}</p></div>
        <div className={spec.tier === "workflow" ? "experience-workbench" : undefined}>
        {complete ? <div className="experience-finish">
          <span className="experience-done"><Check size={26} /></span><h2 ref={heading} tabIndex={-1}>{t("你的模拟决策摘要", "Your example decision summary")}</h2><p>{spec.takeaway[lang]}</p>
          <div className="experience-summary">{spec.steps.map(s => <div key={s.id}><span>{s.title[lang]}</span><strong>{s.options.find(o => o.id === choices[s.id])?.label[lang]}</strong></div>)}</div>
          <div className="experience-actions"><button type="button" className="demo-launch" onClick={download}><Download size={16} />{t("下载模拟摘要", "Download simulation summary")}</button>{website ? <a href={spec.product_context?.trial_url ?? website} target="_blank" rel="noopener noreferrer">{t("前往原厂产品", "Continue on the vendor’s site")} ↗</a> : null}</div>
        </div> : <div key={step.id} className="experience-step">
          <h2 ref={heading} tabIndex={-1}>{step.title[lang]}</h2><p>{step.instruction[lang]}</p>
          <div className={"experience-options " + (step.widget === "compare" ? "experience-options--compare" : "")}>
            {options.map(option => <button key={option.id} type="button" aria-pressed={selected?.id === option.id} onClick={() => choose(option.id)}>
              <span className="experience-radio">{selected?.id === option.id ? <Check size={13} /> : null}</span><strong>{option.label[lang]}</strong>
              {step.widget === "compare" ? <span>{option.output[lang]}</span> : <ArrowRight size={15} />}
            </button>)}
          </div>
          {step.dial ? <div className="experience-dial"><label htmlFor={"dial-" + step.id}>{step.dial.unit[lang]}<strong>{dialValue}</strong></label><input id={"dial-" + step.id} type="range" min={step.dial.min} max={step.dial.max} value={dialValue} onChange={event => setDials(old => ({ ...old, [step.id]: Number(event.target.value) }))} /><div>{step.dial.result_label[lang]}<strong>{dialValue * step.dial.factor}</strong></div><small>{t("演示计算：输入 × ", "Example calculation: input × ")}{step.dial.factor}{t("，并非真实测算。", "; not a real estimate.")}</small></div> : null}
          {selected ? <div className="experience-output" aria-live="polite"><span className="demo-eyebrow">{t("虚构示例 · 非原厂输出", "FICTIONAL EXAMPLE · NOT VENDOR OUTPUT")}</span><p>{selected.output[lang]}</p>
            {step.widget === "app" && step.app_kind ? <DemoAppPreview key={revision} spec={exampleSpec(step.app_kind, lang === "en")} en={lang === "en"} /> : null}
          </div> : <div className="experience-empty">{t("选择一项，查看预先写好的示例。", "Make a choice to reveal a prepared example.")}</div>}
          {step.widget === "review" && selected ? <label className="experience-review"><input type="checkbox" checked={!!reviews[step.id]} onChange={e => setReviews(old => ({ ...old, [step.id]: e.target.checked }))} />{t("我已阅读这段虚构示例", "I reviewed this fictional example.")}</label> : null}
          <nav className="experience-controls" aria-label={t("演示步骤", "Experience steps")}><button type="button" disabled={index === 0} onClick={() => move(index - 1)}><ArrowLeft size={16} />{t("上一步", "Back")}</button><button type="button" className="demo-launch" disabled={!canContinue} onClick={() => move(index + 1)}>{index === spec.steps.length - 1 ? t("查看模拟摘要", "See example summary") : t("继续", "Continue")}<ArrowRight size={16} /></button></nav>
        </div>}
        {spec.tier === "workflow" ? <ExperienceWorkspace key={revision} spec={spec} lang={lang} choices={choices} brief={brief} onBriefChange={setCustomBrief} ratio={ratio} onRatioChange={setRatio} /> : null}
        </div>
      </div>
    </div>
    <footer className="experience-sources"><span>{t("产品资料", "Product sources")}</span>{spec.sources.map((source, i) => <a href={source.url} target="_blank" rel="noopener noreferrer" key={source.url + i}>{source.label[lang]} ↗</a>)}<span>{t("本演示根据公开资料制作，实际效果以产品官网为准。", "Based on public information; not a measure of model quality.")}</span></footer>
  </div>;
}
