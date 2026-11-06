import type { ReactNode } from "react";
import type { Lang } from "./types";

export function Desk({ controls, children, title }: { controls: ReactNode; children: ReactNode; title: string }) {
  return <div className="task-desk">
    <div className="task-controls">{controls}</div>
    <section className="task-output" data-work-result><h3>{title}</h3>{children}</section>
  </div>;
}

export function Range({ label, value, max, min = 0, onChange }: {
  label: string; value: number; max: number; min?: number; onChange: (value: number) => void;
}) {
  return <label className="task-range"><span>{label}<b>{value}</b></span>
    <input type="range" min={min} max={max} value={value} onChange={e => onChange(Number(e.target.value))} />
  </label>;
}

export function Toggle({ checked, onChange, children }: { checked: boolean; onChange: () => void; children: ReactNode }) {
  return <label className="task-toggle"><input type="checkbox" checked={checked} onChange={onChange} /><span>{children}</span></label>;
}

export function Metric({ value, caption }: { value: ReactNode; caption: string }) {
  return <div className="task-metric"><strong>{value}</strong><small>{caption}</small></div>;
}

export function Empty({ lang }: { lang: Lang }) {
  return <p role="status">{lang ? "No matches. Try changing the inputs." : "暂无匹配，可以调整输入再试。"}</p>;
}

export function replaceAt<T>(items: T[], index: number, value: T) {
  return items.map((item, i) => i === index ? value : item);
}
