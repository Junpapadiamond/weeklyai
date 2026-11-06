import { useState } from "react";
import { Desk, Metric, Toggle, replaceAt } from "./parts";
import type { Props } from "./types";

export function Learning({ task, lang }: Props<"learning">) {
  const [used, setUsed] = useState(task.train.map((_, i) => i < 2));
  const examples = task.train.filter((_, i) => used[i]);
  const predictions = task.tests.map(([value]) => {
    const nearest = examples.reduce<(typeof examples)[number] | undefined>((best, row) =>
      !best || Math.abs(row[0] - value) < Math.abs(best[0] - value) ? row : best, undefined);
    return nearest?.[1];
  });
  return <Desk title={task.result[lang]} controls={<><p>{task.axis[lang]}</p>{task.train.map(([value, group], i) =>
    <Toggle checked={used[i]} key={i} onChange={() => setUsed(replaceAt(used, i, !used[i]))}>{value} → {task.classes[group][lang]}</Toggle>)}</>}>
    <Metric value={predictions.filter((v, i) => v === task.tests[i][1]).length + " / " + task.tests.length} caption={lang ? "correct predictions" : "预测命中"} />
    {task.tests.map(([value, truth], i) => <div className="task-record" key={i}><b>{value} → {task.classes[predictions[i] ?? -1]?.[lang] ?? "—"}</b>
      <span>{lang ? "Label" : "已知标签"} · {task.classes[truth][lang]}</span></div>)}
  </Desk>;
}

export function Patch({ task, lang }: Props<"patch">) {
  const [fixed, setFixed] = useState(false);
  const compute = (input: number) => {
    if (task.variant === "stock") return fixed ? Math.max(0, 5 - input) : 5 - input;
    if (task.variant === "cents") return fixed ? Math.round(input * 100) : Math.trunc(input) * 100;
    return Number(input < (fixed ? 3 : 1));
  };
  const inputLabel = { retry: ["先失败次数", "Transient failures"], cents: ["金额（$）", "Amount ($)"], stock: ["订购数量", "Qty ordered"] }[task.variant][lang];
  return <Desk title={task.result[lang]} controls={<><pre><code>{(fixed ? task.fix : task.original)[lang]}</code></pre>
    <Toggle checked={fixed} onChange={() => setFixed(!fixed)}>{lang ? "Apply patch and rerun" : "应用补丁并重测"}</Toggle></>}>
    <Metric value={task.tests.filter(([input, expected]) => compute(input) === expected).length + " / " + task.tests.length} caption={lang ? "tests passed" : "测试通过"} />
    {task.tests.map(([input, expected]) => <div className="task-record" key={input} data-match={compute(input) === expected}>
      <b>{inputLabel} · {input}</b><span>{compute(input) === expected ? "PASS" : "FAIL"}</span>
      <small>{lang ? "Actual" : "实际"} {compute(input)} · {lang ? "Expected" : "期望"} {expected}</small></div>)}
  </Desk>;
}

const moves = [
  { dx: 0, dy: -1, arrow: "↑", name: ["向上", "Up"] }, { dx: 1, dy: 0, arrow: "→", name: ["向右", "Right"] },
  { dx: 0, dy: 1, arrow: "↓", name: ["向下", "Down"] }, { dx: -1, dy: 0, arrow: "←", name: ["向左", "Left"] },
];
export function MotionPath({ task, lang }: Props<"path">) {
  const [program, setProgram] = useState([1]);
  const visited = [0];
  let blocked = 0;
  for (const op of program) {
    const last = visited[visited.length - 1];
    const x = last % 4 + moves[op].dx;
    const y = Math.floor(last / 4) + moves[op].dy;
    if (x < 0 || x > 3 || y < 0 || y > 3 || task.walls.includes(4 * y + x)) blocked++;
    else visited.push(4 * y + x);
  }
  const at = visited[visited.length - 1];
  return <Desk title={task.result[lang]} controls={<><div className="task-chips">{moves.map((m, i) =>
    <button disabled={program.length >= 24} key={i} onClick={() => setProgram([...program, i])}>{m.arrow} {m.name[lang]}</button>)}</div>
    <p className="task-program">{program.map(i => moves[i].arrow).join(" ") || "—"}</p>
    <button disabled={!program.length} onClick={() => setProgram(program.slice(0, -1))}>{lang ? "Undo last move" : "撤回末步"}</button></>}>
    <div className="task-map" aria-hidden="true">{Array.from({ length: 16 }, (_, i) => <span key={i}
      data-cell={i === at ? "at" : task.walls.includes(i) ? "wall" : i === task.goal ? "goal" : visited.includes(i) ? "trail" : ""}>
      {i === at ? "●" : i === task.goal ? "◎" : task.walls.includes(i) ? "▦" : "·"}</span>)}</div>
    <p>● ({at % 4}, {Math.floor(at / 4)}) · ◎ {task.target[lang]} ({task.goal % 4}, {Math.floor(task.goal / 4)}) · ▦ {task.obstacle[lang]}</p>
    <p role="status">{at === task.goal ? (lang ? "Target reached" : "已到达目标") : (lang ? "Moves blocked: " : "受阻步数：") + blocked}</p>
  </Desk>;
}
