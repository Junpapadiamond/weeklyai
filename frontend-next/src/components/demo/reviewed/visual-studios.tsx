import { useState } from "react";
import { Desk, Range, Toggle, replaceAt } from "./parts";
import type { Lang } from "./types";

type StudioProps = { title: string; lang: Lang };

export function Slide({ title, lang }: StudioProps) {
  const [headlines, setHeadlines] = useState<Partial<Record<Lang, string>>>({});
  const [points, setPoints] = useState<Partial<Record<Lang, string>>>({});
  const headline = headlines[lang] ?? (lang ? "Night market by the river" : "河畔夜市");
  const point = points[lang] ?? (lang ? "A Friday gathering for neighborhood makers." : "每周五，让街区手作者在河边相聚。");
  const [poster, setPoster] = useState(false);
  return <Desk title={title} controls={<><label className="task-field">{lang ? "Event title" : "活动标题"}
    <input value={headline} maxLength={70} onChange={e => setHeadlines(previous => ({ ...previous, [lang]: e.target.value }))} /></label>
    <label className="task-field">{lang ? "Key message" : "活动要点"}<textarea value={point} maxLength={160} onChange={e => setPoints(previous => ({ ...previous, [lang]: e.target.value }))} /></label>
    <Toggle checked={poster} onChange={() => setPoster(!poster)}>{lang ? "Poster layout" : "海报版式"}</Toggle></>}>
    <article className={"task-slide" + (poster ? " task-slide--poster" : "")}><h4>{headline || "—"}</h4><p>{point}</p></article>
  </Desk>;
}

export function Diagram({ title, lang }: StudioProps) {
  const names = [["配体", "Ligand"], ["膜受体", "Receptor"], ["细胞内信号", "Cell signal"]];
  const [visible, setVisible] = useState([true, true, false]);
  return <Desk title={title} controls={names.map((n, i) => <Toggle key={i} checked={visible[i]}
    onChange={() => setVisible(replaceAt(visible, i, !visible[i]))}>{n[lang]}</Toggle>)}>
    <svg viewBox="0 0 300 165" role="img" aria-label={title} className="task-svg">
      <rect x="0" y="79" width="300" height="13" className="figure-fill" />
      {visible[0] && <g><path d="m86 22 11 6v13l-11 6-11-6V28Z" className="figure-accent" /><text x="111" y="38">{names[0][lang]}</text></g>}
      {visible[1] && <g><path d="M72 56l14 16 14-16M86 72v36" fill="none" stroke="currentColor" strokeWidth="5" /><text x="115" y="72">{names[1][lang]}</text></g>}
      {visible[2] && <g><circle cx="86" cy="136" r="10" className="figure-accent" /><text x="112" y="141">{names[2][lang]}</text></g>}
      {visible[1] && visible[2] && <path d="M86 110v12l-4-4m4 4 4-4" className="figure-line" />}
    </svg><p>{names.filter((_, i) => visible[i]).map(n => n[lang]).join(" → ") || "—"}</p>
  </Desk>;
}

export function Inertial({ title, lang }: StudioProps) {
  const [bias, setBias] = useState(3);
  let x = 25, y = 100;
  const points = [[x,y]];
  for (let tick = 1; tick <= 10; tick++) {
    const angle = bias * tick * Math.PI / 180;
    x += 22 * Math.cos(angle); y -= 22 * Math.sin(angle);
    points.push([x,y]);
  }
  const drift = Math.hypot(245 - x, 100 - y).toFixed(1);
  return <Desk title={title} controls={<Range label={lang ? "Heading bias per step (°)" : "每步航向偏差（°）"} min={-5} max={5} value={bias} onChange={setBias} />}>
    <svg viewBox="0 -10 270 220" role="img" aria-label={title} className="task-svg">
      <path d="M25 100H245" strokeDasharray="4 4" className="figure-line" />
      <polyline points={points.map(p => p.join(",")).join(" ")} className="figure-trace" /><circle cx={x} cy={y} r="5" className="figure-accent" />
    </svg><p>{lang ? "Dashed: straight reference · solid: inertial estimate" : "虚线为直行参考，实线为惯性估计"}</p>
    <strong>{lang ? "Endpoint drift" : "终点偏差"} · {drift} {lang ? "diagram units" : "示意单位"}</strong>
  </Desk>;
}

export function Camera({ title, lang }: StudioProps) {
  const [angle, setAngle] = useState(30);
  const [time, setTime] = useState(25);
  const radians = angle * Math.PI / 180;
  function project(x: number, y: number) {
    return [150 + x * Math.cos(radians) - y * Math.sin(radians), 95 + (x * Math.sin(radians) + y * Math.cos(radians)) * 0.64];
  }
  const corners = [[-100,-55],[100,-55],[100,55],[-100,55]].map(([x,y]) => project(x,y).join(",")).join(" ");
  const ball = project(-64 + time * 1.28, 18 - time * 0.35);
  return <Desk title={title} controls={<><Range label={lang ? "Camera angle (°)" : "观察角度（°）"} value={angle} max={180} onChange={setAngle} />
    <Range label={lang ? "Pass timeline (%)" : "传球进度（%）"} value={time} max={100} onChange={setTime} /></>}>
    <svg viewBox="0 0 300 190" role="img" aria-label={title} className="task-svg">
      <polygon points={corners} className="figure-field" />
      <polyline points={[project(0,-55), project(0,55)].map(p => p.join(",")).join(" ")} className="figure-line" />
      {[[-64,18],[64,-17]].map(([x,y]) => { const [cx,cy] = project(x,y); return <circle key={x} cx={cx} cy={cy} r="7" fill="currentColor" />; })}
      <circle cx={ball[0]} cy={ball[1]-5*Math.sin(time*Math.PI/100)} r="5" className="figure-accent" />
    </svg><p>{angle}° · {time}% · {lang ? "Two players, one pass" : "两名球员，一次传球"}</p>
  </Desk>;
}

export function Damage({ title, lang }: StudioProps) {
  const panels = [["前盖", "Hood"], ["左侧车门", "Left door"], ["右侧车门", "Right door"], ["后盖", "Trunk"]];
  const marks = [["无标记", "Unmarked"], ["划痕", "Scratch"], ["凹陷", "Dent"]];
  const [damage, setDamage] = useState([1,0,0,0]);
  const shapes = ["M104 32Q150 18 196 32L188 59H112Z","M99 69H120V128H99Z","M180 69H201V128H180Z","M110 139H190L195 158Q150 169 105 158Z"];
  return <Desk title={title} controls={panels.map((part,i) => <label key={i} className="task-field">{part[lang]}
    <select value={damage[i]} onChange={e => setDamage(replaceAt(damage, i, Number(e.target.value)))}>
      {marks.map((m,j) => <option key={j} value={j}>{m[lang]}</option>)}</select></label>)}>
    <svg viewBox="65 8 170 172" className="task-svg" role="img" aria-label={title}>
      <rect x="94" y="20" width="112" height="147" rx="32" className="figure-field" />
      <rect x="123" y="65" width="54" height="64" rx="12" className="figure-fill" />
      {shapes.map((d,i) => <path key={d} d={d} className={damage[i] ? "figure-accent" : "figure-fill"} />)}
    </svg>
    {damage.some(Boolean) ? panels.map((part,i) => damage[i] > 0 && <p key={i}>{part[lang]} · {marks[damage[i]][lang]}</p>)
      : <p>{lang ? "No panels marked." : "尚无已标记部位。"}</p>}
  </Desk>;
}
