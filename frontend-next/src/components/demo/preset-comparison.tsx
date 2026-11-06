import { useId, useState } from "react";
import type { Experience } from "@/lib/demo-experience";
import { isCodeExcerpt } from "@/lib/demo-presentation";

type Option = Experience["steps"][number]["options"][number];
type Lang = "zh" | "en";

function ComparedPreset({ option, lang }: { option: Option; lang: Lang }) {
  const artifact = option.artifact;
  const title = option.label[lang];
  const input = artifact?.input[lang];
  const result = artifact?.output[lang] ?? option.output[lang];
  return <article className="compared-preset">
    <h4>{title}</h4>
    {artifact && input !== title ? <div>
      <h5>{artifact.input_label[lang]}</h5>
      {isCodeExcerpt(artifact, lang) ? <pre><code>{input}</code></pre> : <p>{input}</p>}
    </div> : null}
    <div>
      <h5>{artifact?.output_label[lang] ?? (lang === "en" ? "Prepared outcome" : "预设结果")}</h5>
      <p>{result}</p>
      {artifact?.items ? <ul>{artifact.items.map((item, i) => <li key={i}><strong>{item.label[lang]}</strong> {item.detail[lang]}</li>)}</ul> : null}
    </div>
  </article>;
}

export function PresetComparison({ selected, options, lang }: { selected: Option; options: Option[]; lang: Lang }) {
  const id = useId();
  const others = options.filter(option => option.id !== selected.id);
  const [otherId, setOtherId] = useState(others[0]?.id);
  const other = others.find(option => option.id === otherId) ?? others[0];
  if (!other) return null;
  return <section className="preset-comparison" aria-label={lang === "en" ? "Compare prepared examples" : "预设方案对照"}>
    <div className="preset-comparison__head">
      <p className="experience-artifact__disclosure">{lang === "en" ? "Fictional examples · Not vendor output" : "虚构示例 · 非原厂输出"}</p>
      {others.length > 1 ? <label htmlFor={id}>{lang === "en" ? "Compare with" : "对照方案"}
        <select id={id} value={other.id} onChange={event => setOtherId(event.target.value)}>
          {others.map(option => <option key={option.id} value={option.id}>{option.label[lang]}</option>)}
        </select>
      </label> : null}
    </div>
    <div className="preset-comparison__columns">
      <ComparedPreset option={selected} lang={lang} />
      <ComparedPreset option={other} lang={lang} />
    </div>
  </section>;
}
