"use client";

import { useRef, useState } from "react";
import { ArrowCounterClockwise, ArrowUpRight, DownloadSimple } from "@phosphor-icons/react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { SmartLogo } from "@/components/common/smart-logo";
import { downloadDemoText } from "@/lib/demo-notes";
import { isValidWebsite, normalizeWebsite } from "@/lib/product-utils";
import { reviewedWebsite } from "@/lib/schemas";
import { exampleSpec } from "@/lib/live-demo";
import { DemoAppPreview } from "../demo-app-preview";
import { reviewedTasks } from "./catalog";
import { Evidence, Recall, SearchPassages } from "./record-tasks";
import { Availability, Policies, Quantities, Routing, Thresholds } from "./operation-tasks";
import { Learning, MotionPath, Patch } from "./lab-tasks";
import { Camera, Damage, Diagram, Inertial, Slide } from "./visual-studios";
import { Advance, BuildCache, DurableOrder, Logic, Mix, Redundancy, Rollout } from "./system-studios";
import { Desk } from "./parts";
import type { Lang, Task } from "./types";
import "@/styles/reviewed-tasks.css";

function Builder({ title, lang }: { title: string; lang: Lang }) {
  const spec = exampleSpec("tasks", Boolean(lang));
  const [name, setName] = useState(spec.title);
  return <Desk title={title} controls={<label className="task-field">{lang ? "Checklist app title" : "清单应用名称"}
    <input value={name} maxLength={64} onChange={e => setName(e.target.value)} /></label>}>
    <DemoAppPreview spec={{ ...spec, title: name || spec.title }} en={Boolean(lang)} />
  </Desk>;
}

function Activity({ task, lang }: { task: Task; lang: Lang }) {
  switch (task.kind) {
    case "evidence": return <Evidence task={task} lang={lang} />;
    case "search": return <SearchPassages task={task} lang={lang} />;
    case "quiz": return <Recall task={task} lang={lang} />;
    case "threshold": return <Thresholds task={task} lang={lang} />;
    case "policy": return <Policies task={task} lang={lang} />;
    case "slots": return <Availability task={task} lang={lang} />;
    case "routing": return <Routing task={task} lang={lang} />;
    case "budget": case "ledger": return <Quantities task={task} lang={lang} />;
    case "learning": return <Learning task={task} lang={lang} />;
    case "path": return <MotionPath task={task} lang={lang} />;
    case "patch": return <Patch task={task} lang={lang} />;
    default: {
      const studios = { slides: Slide, diagram: Diagram, damage: Damage, inertial: Inertial, camera: Camera, builder: Builder,
        advance: Advance, logic: Logic, mix: Mix, cache: BuildCache, replay: DurableOrder, redundancy: Redundancy, rollout: Rollout };
      const Studio = studios[task.kind];
      return <Studio title={task.result[lang]} lang={lang} />;
    }
  }
}

/** Preserve form edits and control states in the local text export. */
function snapshot(node: Node): string {
  if (!(node instanceof Element)) return node.textContent ?? "";
  if (node instanceof HTMLTextAreaElement) return node.value;
  if (node instanceof HTMLSelectElement) return node.selectedOptions[0]?.text ?? "";
  if (node instanceof HTMLInputElement) return node.type === "checkbox" ? (node.checked ? "[x] " : "[ ] ") : node.value;
  if (node instanceof SVGElement || node.getAttribute("aria-hidden") === "true") return "";
  if (node instanceof HTMLButtonElement && !node.hasAttribute("aria-pressed")) return "";
  const content = [...node.childNodes].map(snapshot).join("");
  if (node instanceof HTMLButtonElement) return (node.getAttribute("aria-pressed") === "true" ? "[x] " : "[ ] ") + content + " ";
  return ["SPAN","SMALL","B","STRONG","TD","TH"].includes(node.tagName) ? content + " " : content + "\n";
}

export default function ReviewedPlayer({ productId, productName, website, logoUrl, secondaryLogoUrl, embedded }: {
  productId: string; productName: string; website?: string; logoUrl?: string; secondaryLogoUrl?: string; embedded?: boolean;
}) {
  const { locale, t } = useSiteLocale();
  const lang: Lang = locale === "en-US" ? 1 : 0;
  const task = reviewedTasks[productId];
  const [revision, setRevision] = useState(0);
  const desk = useRef<HTMLDivElement>(null);
  const disclosure = task.concept ? t("简化概念实验 · 非设备实测", "Illustrative concept · No hardware or vendor measurements")
    : t("虚构数据 · 本地独立示例", "Fictional data · Independent local example");
  const sourceHost = new URL(task.source).hostname.replace(/^www\./, "");
  const productUrl = normalizeWebsite(reviewedWebsite(productId, website));
  function save() {
    if (!desk.current) return;
    downloadDemoText([productName + " / DarkHorseRadar", task.title[lang], disclosure,
      snapshot(desk.current).replace(/\n{3,}/g, "\n\n"), task.source], "darkhorseradar-" + productId + ".txt");
  }
  return <div className={"experience-shell experience-focus reviewed-task" + (embedded ? " experience-focus--embedded" : "")} data-activity={task.kind}>
    <header className="focus-header">
      {!embedded && <div className="focus-product"><SmartLogo className="demo-product-logo" name={productName}
        website={website} logoUrl={logoUrl} secondaryLogoUrl={secondaryLogoUrl} trustPrimaryLogo size={30} /><h3>{productName}</h3></div>}
      <h2 className="focus-promise">{task.title[lang]}</h2>
      <p className="task-instruction">{task.instruction[lang]}</p>
    </header>
    <small className="task-disclosure">{disclosure}</small>
    <div ref={desk}><Activity key={productId + "/" + lang + "/" + revision} task={task} lang={lang} /></div>
    <footer className="task-footer"><div><a href={task.source} target="_blank" rel="noopener noreferrer">{t("产品资料", "Product source")} · {sourceHost} <ArrowUpRight size={14} /></a>
      {isValidWebsite(productUrl) && productUrl !== task.source && <a href={productUrl} target="_blank" rel="noopener noreferrer">{t("前往官网", "Visit product")} <ArrowUpRight size={14} /></a>}</div>
      <div><button type="button" onClick={() => setRevision(v => v + 1)}><ArrowCounterClockwise size={15} />{t("重置", "Reset")}</button>
        <button type="button" onClick={save}><DownloadSimple size={15} />{t("保存本次结果", "Save result")}</button></div>
    </footer>
  </div>;
}
