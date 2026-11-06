import { BookmarkSimple, Download, X } from "@phosphor-icons/react";
import type { Experience } from "@/lib/demo-experience";
import { downloadDemoText } from "@/lib/demo-notes";

type Props = {
  spec: Experience;
  choices: Record<string, string>;
  included: string[];
  current: string;
  toggle: (id: string) => void;
  goTo: (index: number) => void;
  product: string;
  lang: "zh" | "en";
};

export function ExamplePlan({ spec, choices, included, current, toggle, goTo, product, lang }: Props) {
  const english = lang === "en";
  const rows = spec.steps.flatMap((step, index) => {
    const option = step.options.find(entry => entry.id === choices[step.id]);
    return included.includes(step.id) && option ? [{ step, option, index }] : [];
  });
  const active = included.includes(current);
  const title = english ? "My plan" : "我的方案";
  function save() {
    downloadDemoText([product, title, english ? "Independent fictional example · Not vendor output" : "独立虚构示例 · 非原厂输出",
      ...rows.flatMap(({ step, option }) => [step.title[lang], option.label[lang], option.output[lang]]),
      ...spec.sources.map(source => source.url)], "darkhorseradar-plan.txt");
  }

  return <section className="example-plan" aria-label={title}>
    <header><h3>{title}</h3>
      <button type="button" aria-pressed={active} onClick={() => toggle(current)}>
        <BookmarkSimple size={16} weight={active ? "fill" : "regular"} />
        {active ? (english ? "Remove this choice" : "移出当前选择") : (english ? "Add this choice" : "加入当前选择")}
      </button>
    </header>
    {rows.length ? <ul>
      {rows.map(({ step, option, index }) => <li key={step.id}>
        <button type="button" className="example-plan__jump" onClick={() => goTo(index)}>
          <span>{step.title[lang]}</span><strong>{option.label[lang]}</strong>
        </button>
        <button type="button" aria-label={(english ? "Remove " : "移除") + option.label[lang]} onClick={() => toggle(step.id)}><X size={15} /></button>
      </li>)}
    </ul> : <p>{english ? "Add the choices you want to keep." : "把想保留的选择加入方案。"}</p>}
    {rows.length ? <button type="button" className="example-plan__save" onClick={save}><Download size={16} />{english ? "Save my plan" : "保存我的方案"} ({rows.length})</button> : null}
  </section>;
}
