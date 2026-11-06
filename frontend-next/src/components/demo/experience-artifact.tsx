"use client";

import * as React from "react";
import type { ExperienceArtifactData } from "@/lib/demo-experience";
import { artifactInputParts } from "@/lib/demo-presentation";
import "@/styles/demo-artifact.css";

export function ExperienceArtifact({ artifact, lang, animateChange = false }: { artifact: ExperienceArtifactData; lang: "zh" | "en"; animateChange?: boolean }) {
  const input = artifactInputParts(artifact.input[lang], artifact.kind === "excerpt" ? artifact.emphasis?.[lang] : undefined);
  const List = artifact.kind === "sequence" ? "ol" : "ul";
  return <section className={`experience-artifact experience-artifact--${artifact.kind}`}
    aria-label={lang === "en" ? "Example input and result" : "示例输入与结果"}>
    <p className="experience-artifact__disclosure">{lang === "en" ? "Fictional example · Not vendor output" : "虚构示例 · 非原厂输出"}</p>
    <div className="experience-artifact__input">
      <h3 className="experience-artifact__label">{artifact.input_label[lang]}</h3>
      <p className="experience-artifact__text">{input.map((part, index) => part.emphasized
        ? <mark key={index}>{part.text}</mark> : <React.Fragment key={index}>{part.text}</React.Fragment>)}</p>
    </div>
    <div className="experience-artifact__result" aria-live="polite" aria-atomic="true">
      <div key={JSON.stringify([artifact.output_label[lang], artifact.output[lang], artifact.items?.map(item => [item.label[lang], item.detail[lang]])])}
        className={animateChange ? "demo-changed-copy" : undefined}>
        <h3 className="experience-artifact__label">{artifact.output_label[lang]}</h3>
        <p className="experience-artifact__text">{artifact.output[lang]}</p>
        {artifact.items && (artifact.kind === "sequence" || artifact.kind === "list") ? <List className="experience-artifact__items">
          {artifact.items.map((item, index) => <li key={index}>
            {artifact.kind === "sequence" ? <span className="experience-artifact__number" aria-hidden="true">{String(index + 1).padStart(2, "0")}</span> : null}
            <div><h4>{item.label[lang]}</h4><p>{item.detail[lang]}</p></div>
          </li>)}
        </List> : null}
      </div>
    </div>
  </section>;
}
