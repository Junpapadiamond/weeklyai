"use client";

import { useId, useRef, useState } from "react";
import { ArrowRight, ArrowUpRight, Check, Download, ArrowCounterClockwise } from "@phosphor-icons/react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { availableExperienceOptions, type ExperienceEntry } from "@/lib/demo-experience";
import { defaultExperienceChoices, selectExperienceChoice, initialExperienceIndex, experienceArtifact } from "@/lib/demo-presentation";
import { exampleSpec } from "@/lib/live-demo";
import { DemoAppPreview } from "./demo-app-preview";
import { SmartLogo } from "@/components/common/smart-logo";
import { ExperienceArtifact } from "./experience-artifact";

/** Prepared presets are visible immediately, never recorded as completed user tasks. */
export function ExperiencePlayer({ entry, productName, website, logoUrl, secondaryLogoUrl, embedded = false }: { entry: ExperienceEntry; productName: string; website?: string; logoUrl?: string; secondaryLogoUrl?: string; embedded?: boolean }) {
  const { locale, t } = useSiteLocale();
  const lang = locale === "en-US" ? "en" : "zh";
  const { spec } = entry;
  const [index, setIndex] = useState(() => initialExperienceIndex(spec));
  const [choices, setChoices] = useState(() => defaultExperienceChoices(spec));
  const [dials, setDials] = useState<Record<string, number>>({});
  const [revision, setRevision] = useState(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const id = useId();
  const step = spec.steps[index];
  const options = availableExperienceOptions(step, choices);
  const selected = options.find(o => o.id === choices[step.id]) ?? options[0];
  const artifact = experienceArtifact(spec, step, selected);
  const dialValue = dials[step.id] ?? step.dial?.initial ?? 0;
  const dependencyId = options.find(o => o.when)?.when?.step_id;
  const dependency = spec.steps.find(s => s.id === dependencyId);

  function choose(stepId: string, optionId: string) {
    setChoices(old => selectExperienceChoice(spec, old, stepId, optionId));
  }
  function move(next: number) {
    setIndex(next);
  }
  function download() {
    const lines = [productName + " / DarkHorseRadar", t("独立虚构示例 · 非原厂输出", "Independent fictional example · Not vendor output"),
      t("这是预设示例路径，部分选项可能未经修改。没有运行原厂产品。", "This is a prepared example path; some presets may be unchanged. The vendor product was not run."),
      spec.headline[lang], ...spec.steps.flatMap(s => {
        const option = s.options.find(o => o.id === choices[s.id]);
        const a = option?.artifact;
        return [s.title[lang], option?.label[lang] ?? "", ...(a ? [a.input_label[lang], a.input[lang], a.output_label[lang], a.output[lang],
          ...(a.items?.flatMap(item => [item.label[lang], item.detail[lang]]) ?? []), option && option.output[lang] !== a.output[lang] ? option.output[lang] : ""] : [option?.output[lang] ?? ""]),
          s.dial ? (dials[s.id] ?? s.dial.initial) + " × " + s.dial.factor + " = " + (dials[s.id] ?? s.dial.initial) * s.dial.factor + " (" + s.dial.result_label[lang] + "; " + t("示例算式", "illustrative arithmetic") + ")" : ""];
      }), spec.takeaway[lang], ...spec.sources.map(s => s.url)];
    const url = URL.createObjectURL(new Blob([lines.filter(Boolean).join("\n\n")], { type: "text/plain;charset=utf-8" }));
    const a = document.createElement("a"); a.href = url; a.download = "darkhorseradar-example.txt"; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <div className={`experience-shell experience-focus${embedded ? " experience-focus--embedded" : ""}`}>
    <header className="focus-header">
      {embedded ? <h2 className="focus-promise">{spec.headline[lang]}</h2> : <><div className="focus-product"><SmartLogo className="demo-product-logo" name={productName} logoUrl={logoUrl} secondaryLogoUrl={secondaryLogoUrl} website={website} trustPrimaryLogo size={30} /><h3>{productName}</h3></div><p className="focus-promise">{spec.headline[lang]}</p></>}
    </header>
    <div className="focus-content">
      <h2 ref={heading} tabIndex={-1}>{step.title[lang]}</h2>
      {dependency ? <div className="focus-context-control"><label htmlFor={id + "-context"}>{dependency.title[lang]}</label><select id={id + "-context"} value={choices[dependency.id]} onChange={e => choose(dependency.id, e.target.value)}>
        {availableExperienceOptions(dependency, choices).map(o => <option key={o.id} value={o.id}>{o.label[lang]}</option>)}
      </select></div> : null}
      <div className="focus-result">
        {step.widget === "app" && step.app_kind ? <section className="focus-local-app"><p className="demo-eyebrow">{t("本地示例应用 · 非原厂界面", "LOCAL SAMPLE APP · NOT THE VENDOR INTERFACE")}</p><DemoAppPreview key={revision + step.id} spec={exampleSpec(step.app_kind, lang === "en")} en={lang === "en"} /><p className="focus-app-guidance" aria-live="polite">{selected?.output[lang]}</p></section> : <ExperienceArtifact artifact={artifact} lang={lang} />}
      </div>
      {step.dial ? <section className="experience-dial"><label htmlFor={id + "-dial"}>{step.dial.unit[lang]}<strong>{dialValue}</strong></label>
        <input id={id + "-dial"} type="range" min={step.dial.min} max={step.dial.max} value={dialValue} onChange={e => setDials(old => ({ ...old, [step.id]: Number(e.target.value) }))} />
        <div aria-live="polite">{step.dial.result_label[lang]}<strong>{dialValue * step.dial.factor}</strong></div>
        <small>{t("示例算式，非真实测算：", "Illustrative arithmetic, not a real estimate: ")}{dialValue} × {step.dial.factor} = {dialValue * step.dial.factor}</small></section> : null}
      {options.length > 1 ? <fieldset className="focus-choices"><legend>{t("切换示例", "Compare prepared examples")}</legend><div>
        {options.map(option => <button key={option.id} type="button" aria-pressed={selected?.id === option.id} onClick={() => choose(step.id, option.id)}>
          {selected?.id === option.id ? <Check size={16} aria-hidden="true" /> : <ArrowRight size={16} aria-hidden="true" />}<span>{option.label[lang]}</span>
        </button>)}
      </div></fieldset> : null}
      {spec.steps.length > 1 ? <div className="focus-part-control"><label htmlFor={id + "-part"}>{t("其他部分", "Other parts")}</label><select id={id + "-part"} value={index} onChange={e => move(Number(e.target.value))}>
        {spec.steps.map((s, i) => <option key={s.id} value={i}>{s.title[lang]}</option>)}
      </select></div> : null}
      <details className="focus-details"><summary>{t("示例说明与来源", "About this example & sources")}</summary>
        <p>{step.instruction[lang]}</p><p>{spec.scenario[lang]}</p>
        {spec.product_context ? <><p>{spec.product_context.job[lang]}</p><dl><dt>{t("输入", "Input")}</dt><dd>{spec.product_context.input[lang]}</dd><dt>{t("厂商描述的输出", "Vendor-described output")}</dt><dd>{spec.product_context.output[lang]}</dd></dl></> : null}
        <p>{t("交互会切换预先准备的示例，并非实时调用原厂服务。示例不构成真实研究、模型效果或设备性能的证据。", "Interactions switch prepared examples, not live vendor results. They do not establish research findings, model quality, or device performance.")}</p>
        <ul>{spec.sources.map((s, i) => <li key={s.url + i}><a href={s.url} target="_blank" rel="noopener noreferrer">{s.label[lang]} <ArrowUpRight size={13} /></a></li>)}</ul>
        <p>{spec.takeaway[lang]}</p>
        <div className="focus-tools"><button type="button" onClick={download}><Download size={15} />{t("保存这份示例", "Save this example")}</button><button type="button" onClick={() => { setChoices(defaultExperienceChoices(spec)); setDials({}); setRevision(v => v + 1); move(initialExperienceIndex(spec)); }}><ArrowCounterClockwise size={15} />{t("恢复预设", "Reset presets")}</button></div>
      </details>
    </div>
    {website ? <footer className="focus-footer"><a href={spec.product_context?.trial_url ?? website} target="_blank" rel="noopener noreferrer">{t("前往官方产品", "Visit the official product")} <ArrowUpRight size={16} /></a>{spec.product_context ? <small>{spec.product_context.trial_note[lang]}</small> : null}</footer> : null}
  </div>;
}
