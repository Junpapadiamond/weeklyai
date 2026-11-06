"use client";

import { Fragment, useRef, useState } from "react";
import { Code, Copy } from "@phosphor-icons/react";
import type { ExperienceArtifactData } from "@/lib/demo-experience";
import { artifactInputParts, isCodeExcerpt } from "@/lib/demo-presentation";
import type { ItemDraft } from "@/lib/demo-notes";
import { ArtifactItems } from "./artifact-items";
import "@/styles/demo-artifact.css";

type Props = { artifact: ExperienceArtifactData; lang: "zh" | "en"; animateChange?: boolean; hideInput?: boolean; hideRepeatedSummary?: boolean;
  draft: ItemDraft; onEdit: (draft: ItemDraft) => void; title?: string; sources?: string[] };

function CodeExcerpt({ artifact, lang }: Pick<Props, "artifact" | "lang">) {
  const source = artifact.input[lang];
  const code = useRef<HTMLElement>(null);
  const [feedback, setFeedback] = useState("");
  async function copy() {
    try {
      await navigator.clipboard.writeText(source);
      setFeedback(lang === "en" ? "Copied" : "已复制");
    } catch {
      const selection = window.getSelection();
      if (selection && code.current) {
        const range = document.createRange();
        range.selectNodeContents(code.current);
        selection.removeAllRanges();
        selection.addRange(range);
      }
      setFeedback(lang === "en" ? "Copy the selected code" : "请复制选中的代码");
    }
  }
  return <div className="artifact-code">
    <div className="artifact-code__bar">
      <h3><Code size={18} aria-hidden="true" />{artifact.input_label[lang]}</h3>
      <button type="button" onClick={copy}><Copy size={15} />{lang === "en" ? "Copy code" : "复制代码"}</button>
    </div>
    <pre tabIndex={0} aria-label={artifact.input_label[lang]}><code ref={code}>{highlightedInput(artifact, lang)}</code></pre>
    <span role="status" className={feedback ? "artifact-code__status" : undefined}>{feedback}</span>
  </div>;
}

function highlightedInput(artifact: ExperienceArtifactData, lang: Props["lang"]) {
  const parts = artifactInputParts(artifact.input[lang], artifact.kind === "excerpt" ? artifact.emphasis?.[lang] : undefined);
  return parts.map((part, index) => part.emphasized ? <mark key={index}>{part.text}</mark> : <Fragment key={index}>{part.text}</Fragment>);
}

export function ExperienceArtifact({ artifact, lang, animateChange = false, hideInput = false, hideRepeatedSummary = false, draft, onEdit, title, sources }: Props) {
  const code = isCodeExcerpt(artifact, lang);
  const structured = Boolean(artifact.items?.length);
  const layout = code ? "code" : structured ? "items" : hideInput ? "result" : artifact.kind;
  const contentKey = JSON.stringify([artifact.output[lang], artifact.output_label[lang], artifact.items]);
  const InputText = artifact.kind === "excerpt" ? "blockquote" : "p";
  return <section className={`experience-artifact experience-artifact--${layout}`}
    aria-label={lang === "en" ? "Example input and result" : "示例输入与结果"}>
    <p className="experience-artifact__disclosure">{lang === "en" ? "Fictional example · Not vendor output" : "虚构示例 · 非原厂输出"}</p>
    {code ? <CodeExcerpt key={artifact.input[lang]} artifact={artifact} lang={lang} /> : !hideInput ? <div className="experience-artifact__input">
      <h3 className="experience-artifact__label">{artifact.input_label[lang]}</h3>
      <InputText className="experience-artifact__text">{highlightedInput(artifact, lang)}</InputText>
    </div> : null}
    <div className="experience-artifact__result">
      <div aria-live="polite" aria-atomic="true">
        <div key={contentKey} className={animateChange ? "demo-changed-copy" : undefined}>
          <h3 className="experience-artifact__label">{artifact.output_label[lang]}</h3>
          {hideRepeatedSummary ? null : <p className="experience-artifact__text">{artifact.output[lang]}</p>}
        </div>
      </div>
      {artifact.items?.length ? <ArtifactItems key={contentKey} draft={draft} onEdit={onEdit} title={title} sources={sources} items={artifact.items} ordered={artifact.kind === "sequence"} lang={lang} label={artifact.output_label[lang]} /> : null}
    </div>
  </section>;
}
