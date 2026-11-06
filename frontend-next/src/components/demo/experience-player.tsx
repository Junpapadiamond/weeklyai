"use client";

import dynamic from "next/dynamic";
import { reviewedIds } from "./reviewed/ids";
import { useId, useRef, useState } from "react";
import { ArrowRight, ArrowUpRight, Check, Download, ArrowCounterClockwise, Columns } from "@phosphor-icons/react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { availableExperienceOptions, type ExperienceEntry } from "@/lib/demo-experience";
import { defaultExperienceChoices, selectExperienceChoice, initialExperienceIndex, experienceArtifact } from "@/lib/demo-presentation";
import { exampleSpec } from "@/lib/live-demo";
import { DemoAppPreview } from "./demo-app-preview";
import { SmartLogo } from "@/components/common/smart-logo";
import { ExperienceArtifact } from "./experience-artifact";
import { downloadDemoText, itemNotes, type ItemDraft } from "@/lib/demo-notes";
import { ExamplePlan } from "./example-plan";
import { PresetComparison } from "./preset-comparison";

const ReviewedPlayer = dynamic(() => import("./reviewed/reviewed-player"));

type PlayerProps = { entry: ExperienceEntry; productId?: string; productName: string; website?: string; logoUrl?: string; secondaryLogoUrl?: string; embedded?: boolean };

export function ExperiencePlayer(props: PlayerProps) {
  const { productId, entry } = props;
  if (productId && reviewedIds.has(String(productId)) && isTextPlan(entry.spec)) {
    return <ReviewedPlayer key={productId} {...props} productId={String(productId)} />;
  }
  return <PresetPlayer {...props} />;
}

function isTextPlan(spec: ExperienceEntry["spec"]) {
  return spec.steps.length > 1 && spec.steps.every(part => !part.app_kind && !part.dial && part.options.every(option => !option.artifact));
}

/** Prepared presets are visible immediately, never recorded as completed user tasks. */
function PresetPlayer({ entry, productName, website, logoUrl, secondaryLogoUrl, embedded = false }: PlayerProps) {
  const { locale, t } = useSiteLocale();
  const lang = locale === "en-US" ? "en" : "zh";
  const { spec } = entry;
  const [index, setIndex] = useState(() => initialExperienceIndex(spec));
  const [choices, setChoices] = useState(() => defaultExperienceChoices(spec));
  const [dials, setDials] = useState<Record<string, number>>({});
  const [revision, setRevision] = useState(0);
  const [hasInteracted, setHasInteracted] = useState(false);
  const [included, setIncluded] = useState<string[]>([]);
  const canBuildPlan = isTextPlan(spec);
  const [drafts, setDrafts] = useState<Record<string, ItemDraft>>({});
  const [comparing, setComparing] = useState(false);
  const id = useId();
  const parts = useRef<HTMLDivElement>(null);
  const step = spec.steps[index];
  const options = availableExperienceOptions(step, choices);
  const selected = options.find(o => o.id === choices[step.id]) ?? options[0];
  const draftKey = JSON.stringify([step.id, selected?.id]);
  const artifact = experienceArtifact(spec, step, selected);
  const dialValue = dials[step.id] ?? step.dial?.initial ?? 0;
  const dependencyId = options.find(o => o.when)?.when?.step_id;
  const dependency = spec.steps.find(s => s.id === dependencyId);

  function choose(stepId: string, optionId: string) {
    if (choices[stepId] === optionId) return;
    setHasInteracted(true);
    const next = selectExperienceChoice(spec, choices, stepId, optionId);
    setChoices(next);
    setIncluded(previous => previous.filter(id => id === stepId || choices[id] === next[id]));
  }
  function move(next: number) {
    setComparing(false);
    setHasInteracted(true);
    setIndex(next);
  }
  function revisitPlanStep(next: number) {
    move(next);
    const picker = parts.current?.querySelector("select");
    const control = picker?.getClientRects().length ? picker : parts.current?.querySelectorAll("button")[next];
    control?.focus({ preventScroll: true });
    parts.current?.scrollIntoView({ block: "start", behavior: "instant" });
  }
  function togglePlanStep(stepId: string) {
    setIncluded(previous => previous.includes(stepId) ? previous.filter(id => id !== stepId) : [...previous, stepId]);
  }
  function download() {
    const lines = [productName + " / DarkHorseRadar", t("独立虚构示例 · 非原厂输出", "Independent fictional example · Not vendor output"),
      t("这是预设示例路径，部分选项可能未经修改。没有运行原厂产品。", "This is a prepared example path; some presets may be unchanged. The vendor product was not run."),
      spec.headline[lang], ...spec.steps.flatMap(s => {
        const option = s.options.find(o => o.id === choices[s.id]);
        const a = option?.artifact;
        const draft = drafts[JSON.stringify([s.id, option?.id])];
        return [s.title[lang], option?.label[lang] ?? "", ...(a ? [a.input_label[lang], a.input[lang], a.output_label[lang], a.output[lang],
          ...(draft?.order ? [t("我的编排", "My sequence")] : []),
          ...(a.items ? itemNotes(a.items, draft?.order ?? a.items.map((_, i) => i), lang) : []),
          ...(a.items && draft?.picked?.length ? [t("我的摘录", "My notes"), ...itemNotes(a.items, draft.picked, lang)] : []), option && option.output[lang] !== a.output[lang] ? option.output[lang] : ""] : [option?.output[lang] ?? ""]),
          s.dial ? (dials[s.id] ?? s.dial.initial) + " × " + s.dial.factor + " = " + (dials[s.id] ?? s.dial.initial) * s.dial.factor + " (" + s.dial.result_label[lang] + "; " + t("示例算式", "illustrative arithmetic") + ")" : ""];
      }), spec.takeaway[lang], ...spec.sources.map(s => s.url)];
    downloadDemoText(lines, "darkhorseradar-example.txt");
  }
  return <div className={`experience-shell experience-focus${embedded ? " experience-focus--embedded" : ""}`}>
    <header className="focus-header">
      {embedded ? <h2 className="focus-promise">{spec.headline[lang]}</h2> : <><div className="focus-product"><SmartLogo className="demo-product-logo" name={productName} logoUrl={logoUrl} secondaryLogoUrl={secondaryLogoUrl} website={website} trustPrimaryLogo size={30} /><h3>{productName}</h3></div><p className="focus-promise">{spec.headline[lang]}</p></>}
    </header>
    <div className="focus-content">
      {spec.steps.length > 1 ? (
        <div ref={parts} className={spec.steps.length > 2 ? "focus-step-nav focus-step-nav--many" : "focus-step-nav"} role="group" aria-label={t("体验环节", "Explore a part")}>
          {spec.steps.length > 2 ? <label className="focus-step-nav__picker">
            {t("体验环节", "Explore a part")}
            <select value={index} onChange={event => move(Number(event.target.value))}>
              {spec.steps.map((part, i) => <option key={part.id} value={i}>{part.title[lang]}</option>)}
            </select>
          </label> : null}
          {spec.steps.map((part, i) => (
            <button key={part.id} type="button" aria-pressed={i === index} onClick={() => move(i)}>{part.title[lang]}</button>
          ))}
        </div>
      ) : <h2>{step.title[lang]}</h2>}
      {dependency ? <div className="focus-context-control"><label htmlFor={id + "-context"}>{dependency.title[lang]}</label><select id={id + "-context"} value={choices[dependency.id]} onChange={e => choose(dependency.id, e.target.value)}>
        {availableExperienceOptions(dependency, choices).map(o => <option key={o.id} value={o.id}>{o.label[lang]}</option>)}
      </select></div> : null}
      {options.length > 1 ? <fieldset className="focus-choices"><legend>{step.instruction[lang]}</legend><div>
        {options.map(option => <button key={option.id} type="button" aria-pressed={selected?.id === option.id} onClick={() => choose(step.id, option.id)}>
          {selected?.id === option.id ? <Check size={16} aria-hidden="true" /> : <ArrowRight size={16} aria-hidden="true" />}<span>{option.label[lang]}</span>
        </button>)}
        {step.widget !== "app" && step.widget !== "dial" ? (
          <button className="focus-compare" type="button" aria-pressed={comparing} aria-controls={id + "-result"} onClick={() => setComparing(value => !value)}>
            <Columns size={16} aria-hidden="true" />{comparing ? t("退出对照", "Close comparison") : t("对照方案", "Compare presets")}
          </button>
        ) : null}
      </div></fieldset> : null}
      <div className="focus-result" id={id + "-result"}>
        {comparing && options.length > 1 && selected ? (
          <PresetComparison options={options} selected={selected} lang={lang} />
        ) : step.widget === "app" && step.app_kind ? (
          <section className="focus-local-app">
            <p className="demo-eyebrow">{t("本地示例应用 · 非原厂界面", "Local sample app · Not the vendor interface")}</p>
            <DemoAppPreview key={revision + step.id} spec={exampleSpec(step.app_kind, lang === "en")} en={lang === "en"} />
            <p className="focus-app-guidance" aria-live="polite">
              <span key={selected?.output[lang]} className={hasInteracted ? "demo-changed-copy" : undefined}>{selected?.output[lang]}</span>
            </p>
          </section>
        ) : (
          <ExperienceArtifact artifact={artifact} lang={lang} animateChange={hasInteracted}
            hideInput={options.length > 1 && artifact.input[lang] === selected?.label[lang]}
            hideRepeatedSummary={Boolean(options.length > 1 && artifact.items?.length && artifact.output[lang] === selected?.label[lang])}
            draft={drafts[draftKey] ?? {}}
            onEdit={draft => setDrafts(previous => ({ ...previous, [draftKey]: draft }))}
            title={productName} sources={spec.sources.map(source => source.url)} />
        )}
      </div>
      {canBuildPlan ? <ExamplePlan spec={spec} choices={choices} included={included} current={step.id}
        toggle={togglePlanStep} goTo={revisitPlanStep} product={productName} lang={lang} /> : null}
      {step.dial ? <section className="experience-dial"><label htmlFor={id + "-dial"}>{step.dial.unit[lang]}<strong>{dialValue}</strong></label>
        <input id={id + "-dial"} type="range" min={step.dial.min} max={step.dial.max} value={dialValue} onChange={e => setDials(old => ({ ...old, [step.id]: Number(e.target.value) }))} />
        <div aria-live="polite">{step.dial.result_label[lang]}<strong>{dialValue * step.dial.factor}</strong></div>
        <small>{t("示例算式，非真实测算：", "Illustrative arithmetic, not a real estimate: ")}{dialValue} × {step.dial.factor} = {dialValue * step.dial.factor}</small></section> : null}
      <details className="focus-details"><summary>{t("示例说明与来源", "About this example & sources")}</summary>
        {options.length < 2 ? <p>{step.instruction[lang]}</p> : null}<p>{spec.scenario[lang]}</p>
        {spec.product_context ? <><p>{spec.product_context.job[lang]}</p><dl><dt>{t("输入", "Input")}</dt><dd>{spec.product_context.input[lang]}</dd><dt>{t("厂商描述的输出", "Vendor-described output")}</dt><dd>{spec.product_context.output[lang]}</dd></dl></> : null}
        <p>{t("交互会切换预先准备的示例，并非实时调用原厂服务。示例不构成真实研究、模型效果或设备性能的证据。", "Interactions switch prepared examples, not live vendor results. They do not establish research findings, model quality, or device performance.")}</p>
        <ul>{spec.sources.map((s, i) => <li key={s.url + i}><a href={s.url} target="_blank" rel="noopener noreferrer">{s.label[lang]} <ArrowUpRight size={13} /></a></li>)}</ul>
        <p>{spec.takeaway[lang]}</p>
        <div className="focus-tools"><button type="button" onClick={download}><Download size={15} />{t("保存这份示例", "Save this example")}</button><button type="button" onClick={() => { setChoices(defaultExperienceChoices(spec)); setDials({}); setDrafts({}); setIncluded([]); setRevision(v => v + 1); move(initialExperienceIndex(spec)); }}><ArrowCounterClockwise size={15} />{t("恢复预设", "Reset presets")}</button></div>
      </details>
    </div>
    {website ? <footer className="focus-footer"><a href={spec.product_context?.trial_url ?? website} target="_blank" rel="noopener noreferrer">{t("前往官方产品", "Visit the official product")} <ArrowUpRight size={16} /></a>{spec.product_context ? <small>{spec.product_context.trial_note[lang]}</small> : null}</footer> : null}
  </div>;
}
