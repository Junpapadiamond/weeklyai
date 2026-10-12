"use client";

import { useEffect, useState } from "react";
import { FileText, Image as ImageIcon, Stack, Monitor, Pause, Play, MagnifyingGlass, DeviceMobile } from "@phosphor-icons/react";
import type { Experience } from "@/lib/demo-experience";

type Props = {
  spec: Experience; lang: "zh" | "en"; choices: Record<string, string>; brief: string;
  onBriefChange: (value: string) => void; ratio: "9:16" | "16:9"; onRatioChange: (value: "9:16" | "16:9") => void;
};

/** Fixed, local UI: model output is text data, never HTML, code or external media. */
export function ExperienceWorkspace({ spec, lang, choices, brief, onBriefChange, ratio, onRatioChange }: Props) {
  const en = lang === "en";
  const kind = spec.workspace?.kind ?? "document";
  const [shot, setShot] = useState(0);
  const [playing, setPlaying] = useState(false);
  const chosen = spec.steps.map(step => step.options.find(option => option.id === choices[step.id]));
  const frames = en ? ["The hook", "The benefit", "The next action"] : ["抓住注意", "展示卖点", "引导行动"];
  const active = chosen[Math.min(shot + 1, chosen.length - 1)];
  const visual = kind === "video" || kind === "image";
  const direction = choices[spec.steps[1]?.id] ?? "0";
  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => setShot(current => (current + 1) % 3), 1600);
    return () => window.clearInterval(timer);
  }, [playing]);

  return <section className="workflow-workspace" aria-label={en ? "Interactive workspace" : "可交互工作区"}>
    <div className="workspace-topbar"><span><i /><i /><i /></span><strong>{en ? "EXAMPLE DECISION SUMMARY" : "示例决策摘要"}</strong><small>{en ? "Simulation" : "模拟"}</small></div>
    <div className="workspace-content">
      {spec.product_context ? (visual ? <p className="workspace-note">{brief}</p> : null) : <label className="workspace-brief">{spec.workspace?.label[lang] ?? (en ? "Your brief" : "描述你的需求")}
        <textarea maxLength={200} value={brief} onChange={event => onBriefChange(event.target.value)} rows={3} />
      </label>}
      {visual ? <>
        <div className="workspace-toolbar"><span>{kind === "video" ? (en ? "Storyboard" : "分镜预览") : (en ? "Composition" : "构图预览")}</span><div role="group" aria-label={en ? "Aspect ratio" : "画幅"}>
          <button type="button" aria-pressed={ratio === "9:16"} onClick={() => onRatioChange("9:16")}><DeviceMobile size={13} />9:16</button>
          <button type="button" aria-pressed={ratio === "16:9"} onClick={() => onRatioChange("16:9")}><Monitor size={13} />16:9</button>
        </div></div>
        <div className={"workspace-canvas " + (ratio === "9:16" ? "is-portrait" : "is-landscape")} data-direction={direction} data-shot={shot}>
          <span className="workspace-frame-label">{en ? "CONCEPT PREVIEW" : "创意示意"} / 0{shot + 1}</span>
          <div className="workspace-composition" aria-hidden="true"><div /><div /><div /></div>
          <div className="workspace-caption"><small>{frames[shot]}</small><strong>{brief || (en ? "Add your product brief" : "添加商品卖点")}</strong></div>
          <span className="workspace-safe-area" aria-hidden="true" />
        </div>
        <div className="workspace-transport"><button type="button" aria-pressed={playing} onClick={() => setPlaying(value => !value)}>{playing ? <Pause size={15} /> : <Play size={15} />}{playing ? (en ? "Pause" : "暂停") : (en ? "Play storyboard" : "播放分镜")}</button><span>{en ? "Local storyboard · no AI video rendered" : "本地分镜示意 · 非 AI 视频成片"}</span></div>
        <div className="workspace-timeline" role="group" aria-label={en ? "Storyboard shots" : "分镜"}>{frames.map((frame, i) => <button key={frame} type="button" aria-pressed={shot === i} onClick={() => { setShot(i); setPlaying(false); }}><span>0{i + 1}</span>{frame}</button>)}</div>
        <p className="workspace-note" aria-live="polite">{active?.output[lang] ?? (en ? "Your choices shape the creative plan here." : "选择左侧的方案，在这里查看创意变化。")}</p>
      </> : <div className={"workspace-artifact workspace-artifact--" + kind}>
        <div className="workspace-artifact-header">{kind === "search" ? <MagnifyingGlass size={17} /> : kind === "board" ? <Stack size={17} /> : <FileText size={17} />}<strong>{brief || spec.headline[lang]}</strong></div>
        {!chosen.some(Boolean) ? <p>{en ? "Make your first choice to add an example here." : "完成第一个选择，在这里查看示例摘要。"}</p> : null}
        {spec.steps.map((step, i) => chosen[i] ? <article key={step.id} data-ready><span>{String(i + 1).padStart(2, "0")} · {step.title[lang]}</span><h4>{chosen[i]?.label[lang]}</h4><p>{chosen[i]?.output[lang]}</p></article> : null)}
      </div>}
      <div className="workspace-bottom"><ImageIcon size={13} />{spec.product_context ? (en ? "Prepared fictional examples · no vendor execution" : "预先编写的虚构示例 · 未运行原厂产品") : (en ? "Prepared examples, not live output. Editing the brief changes this summary only." : "预先编写的示例，非实时输出。编辑简报只会修改此摘要。")}</div>
    </div>
  </section>;
}
