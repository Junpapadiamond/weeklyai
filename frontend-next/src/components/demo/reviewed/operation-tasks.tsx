import { useState } from "react";
import { Desk, Empty, Metric, Range, Toggle, replaceAt } from "./parts";
import type { Props } from "./types";

export function Thresholds({ task, lang }: Props<"threshold">) {
  const [limits, setLimits] = useState(task.axes.map(axis => axis[2]));
  const matches = task.rows.filter(([, a, b]) => [a, b].every((value, i) =>
    task.axes[i][1] === "max" ? value <= limits[i] : value >= limits[i]));
  return <Desk title={task.result[lang]} controls={task.axes.map(([label], i) =>
    <Range key={i} label={label[lang]} value={limits[i]} max={Math.ceil(Math.max(...task.rows.map(r => i ? r[2] : r[1])) * 1.2)}
      onChange={value => setLimits(replaceAt(limits, i, value))} />)}>
    <Metric value={matches.length + " / " + task.rows.length} caption={lang ? "meet both limits" : "满足两项条件"} />
    {task.rows.map(row => <div className="task-record" key={row[0][1]} data-match={matches.includes(row)}>
      <b>{row[0][lang]}</b><span>{matches.includes(row) ? (lang ? "Included" : "已入选") : (lang ? "Outside limits" : "超出条件")}</span>
      <small>{task.axes[0][0][lang]} · {row[1]}　{task.axes[1][0][lang]} · {row[2]}</small>
    </div>)}
  </Desk>;
}

export function Policies({ task, lang }: Props<"policy">) {
  const [enabled, setEnabled] = useState(task.rules.map((_, i) => i === 0));
  return <Desk title={task.result[lang]} controls={task.rules.map((rule, i) =>
    <Toggle key={i} checked={enabled[i]} onChange={() => setEnabled(replaceAt(enabled, i, !enabled[i]))}>{rule[lang]}</Toggle>)}>
    {task.rows.map(([action, violations]) => {
      const triggered = violations.filter(i => enabled[i]);
      return <div key={action[1]} className="task-record" data-match={!triggered.length}>
        <b>{action[lang]}</b><span>{triggered.length ? (lang ? "Held" : "已拦截") : (lang ? "Allowed" : "已放行")}</span>
        {triggered.length > 0 && <small>{triggered.map(i => task.rules[i][lang]).join(" · ")}</small>}
      </div>;
    })}
  </Desk>;
}

export function Availability({ task, lang }: Props<"slots">) {
  const [free, setFree] = useState(task.rows.map(([, slots]) => task.times.map((_, j) => slots.includes(j))));
  const overlap = task.times.filter((_, j) => free.every(row => row[j]));
  return <Desk title={task.result[lang]} controls={task.rows.map(([person], i) => <fieldset key={i}><legend>{person[lang]}</legend>
    <div className="task-chips">{task.times.map((time, j) => <button key={j} aria-pressed={free[i][j]} onClick={() =>
      setFree(replaceAt(free, i, replaceAt(free[i], j, !free[i][j])))}>{time[lang]}</button>)}</div></fieldset>)}>
    {overlap.length ? overlap.map(time => <p className="task-choice-result" key={time[1]}>{time[lang]}</p>) : <Empty lang={lang} />}
  </Desk>;
}

export function Routing({ task, lang }: Props<"routing">) {
  const [routes, setRoutes] = useState(task.rows.map(row => row[2]));
  return <Desk title={task.result[lang]} controls={task.rows.map(([intent], i) => <label className="task-field" key={i}>{intent[lang]}
    <select value={routes[i]} onChange={e => setRoutes(replaceAt(routes, i, Number(e.target.value)))}>
      {task.queues.map((queue, j) => <option key={j} value={j}>{queue[lang]}</option>)}</select></label>)}>
    {task.queues.map((queue, j) => <div className="task-queue" key={j}><h4>{queue[lang]} <small>{routes.filter(r => r === j).length}</small></h4>
      {task.rows.map(([, event], i) => routes[i] === j && <p key={i}>{event[lang]}</p>)}</div>)}
  </Desk>;
}

export function Quantities({ task, lang }: Props<"budget" | "ledger">) {
  const [counts, setCounts] = useState<number[]>(task.rows.map((_, i) => i === 0 ? 1 : 0));
  const lines = task.kind === "budget"
    ? task.rows.map(([name, price], i) => ({ name: name[lang], group: "", price, count: counts[i] }))
    : task.rows.map(([name, group, price], i) => ({ name: name[lang], group: group[lang], price, count: counts[i] }));
  const total = lines.reduce((sum, line) => sum + line.price * line.count, 0);
  const groups = [...new Set(lines.map(line => line.group))];
  return <Desk title={task.result[lang]} controls={lines.map((line, i) =>
    <Range key={i} label={line.name + " · " + line.price + " " + task.unit[lang]} value={counts[i]} max={10}
      onChange={value => setCounts(replaceAt(counts, i, value))} />)}>
    <Metric value={(task.kind === "budget" ? task.capacity - total : total) + " " + task.unit[lang]}
      caption={task.kind === "budget" ? (lang ? "Capacity: " : "总容量 ") + task.capacity + " " + task.unit[lang] : (lang ? "Total" : "合计")} />
    {task.kind === "budget" && total > task.capacity && <p role="status">{lang ? "Over capacity. Reduce the quantities." : "已超出容量，请减少数量。"}</p>}
    {groups.map(group => <div key={group} className="task-queue">{group && <h4>{group} · {lines.filter(l => l.group === group).reduce((a, l) => a + l.count * l.price, 0)} {task.unit[lang]}</h4>}
      {lines.filter(line => line.group === group && line.count > 0).map(line => <p key={line.name}>{line.name} · {line.count} × {line.price} = {line.count * line.price}</p>)}</div>)}
  </Desk>;
}
