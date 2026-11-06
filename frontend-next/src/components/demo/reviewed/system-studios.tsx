import { useState } from "react";
import { Desk, Metric, Range, Toggle, replaceAt } from "./parts";
import type { Lang } from "./types";

type StudioProps = { title: string; lang: Lang };

export function Logic({ title, lang }: StudioProps) {
  const [pins, setPins] = useState([true, false]);
  return <Desk title={title} controls={pins.map((pin,i) => <Toggle key={i} checked={pin}
    onChange={() => setPins(replaceAt(pins, i, !pin))}>{lang ? "Input" : "输入"} {i ? "B" : "A"} · {Number(pin)}</Toggle>)}>
    <Metric value={Number(pins[0] && pins[1])} caption="OUT = A AND B" />
    <table><thead><tr><th>A</th><th>B</th><th>OUT</th></tr></thead><tbody>{[0,1,2,3].map(i =>
      <tr key={i} data-active={i === Number(pins[0])*2 + Number(pins[1])}><td>{i >> 1}</td><td>{i % 2}</td><td>{Number(i === 3)}</td></tr>)}</tbody></table>
  </Desk>;
}

export function Advance({ title, lang }: StudioProps) {
  const [face, setFace] = useState(5000);
  const [rate, setRate] = useState(3);
  const fee = face * rate / 100;
  return <Desk title={title} controls={<><Range label={lang ? "Invoice face value (€)" : "发票面额（€）"} value={face} max={10000} onChange={setFace} />
    <Range label={lang ? "Example fee (%)" : "假设费用率（%）"} value={rate} max={10} onChange={setRate} /></>}>
    <Metric value={"€" + (face - fee).toFixed(2)} caption={lang ? "Face value less the illustrative fee" : "票面金额减去示例费用"} />
    <p>€{face} − €{fee.toFixed(2)} = €{(face-fee).toFixed(2)}</p>
  </Desk>;
}

export function Mix({ title, lang }: StudioProps) {
  const [suppression, setSuppression] = useState(40);
  const sources = [[lang ? "Foreground voice" : "前方人声", 72], [lang ? "Room noise" : "环境噪声", Math.round(65*(1-suppression/100))]] as const;
  return <Desk title={title} controls={<Range label={lang ? "Background suppression (%)" : "背景抑制（%）"} value={suppression} max={100} onChange={setSuppression} />}>
    {sources.map(([name, level]) => <div className="task-meter" key={name}><label>{name} · {level}<meter min={0} max={100} value={level} /></label></div>)}
    <p>{lang ? "Relative levels in a two-source illustration." : "两个声源的相对电平示意。"}</p>
  </Desk>;
}

export function Redundancy({ title, lang }: StudioProps) {
  const [failed, setFailed] = useState([false, false, false]);
  const names = lang ? ["Sensor A", "Sensor B", "Shared receiver"] : ["传感器 A", "传感器 B", "共用接收器"];
  const links = [!failed[0] && !failed[2], !failed[1] && !failed[2]];
  return <Desk title={title} controls={names.map((name,i) => <Toggle key={i} checked={failed[i]}
    onChange={() => setFailed(replaceAt(failed, i, !failed[i]))}>{name} · {lang ? "inject fault" : "注入故障"}</Toggle>)}>
    <Metric value={links.filter(Boolean).length + " / 2"} caption={lang ? "signal paths available" : "可用信号路径"} />
    {links.map((ok,i) => <div className="task-record" key={i} data-match={ok}><b>{names[i]} → {names[2]}</b><span>{ok ? (lang ? "Connected" : "已连接") : (lang ? "Interrupted" : "已中断")}</span></div>)}
  </Desk>;
}

const stages = [["安装依赖","Install dependencies"],["编译源码","Compile sources"],["运行测试","Run tests"]];
export function BuildCache({ title, lang }: StudioProps) {
  const [source,setSource] = useState(1);
  const [deps,setDeps] = useState(1);
  const [cache,setCache] = useState<string[]>([]);
  const [trace,setTrace] = useState([false,false,false]);
  const [run,setRun] = useState(0);
  function build() {
    const keys = ["deps:" + deps, "src:" + deps + ":" + source, "test:" + deps + ":" + source];
    setTrace(keys.map(k => cache.includes(k)));
    setCache([...new Set([...cache, ...keys])]);
    setRun(run + 1);
  }
  return <Desk title={title} controls={<><div className="task-chips"><button onClick={() => setSource(source + 1)}>{lang ? "Edit source" : "改动源码"} · v{source}</button>
    <button onClick={() => setDeps(deps + 1)}>{lang ? "Edit dependencies" : "改动依赖"} · v{deps}</button></div>
    <button onClick={build}>{lang ? "Run build" : "运行构建"}</button></>}>
    <Metric value={run ? trace.filter(Boolean).length + " / 3" : "0 / 3"} caption={lang ? "cache hits" : "缓存命中"} />
    {stages.map((stage,i) => <div className="task-record" key={i}><b>{stage[lang]}</b><span>{!run ? (lang ? "Queued" : "待运行") : trace[i] ? (lang ? "Reused" : "复用产物") : (lang ? "Executed" : "已执行")}</span></div>)}
    <small>{lang ? "Build" : "构建"} #{run}</small>
  </Desk>;
}

export function DurableOrder({ title, lang }: StudioProps) {
  const [phase, setPhase] = useState<"ready" | "stopped" | "finished">("ready");
  const [journal, setJournal] = useState<string[]>([]);
  const [charges, setCharges] = useState(0);
  const charge = lang ? "Payment captured" : "记入一笔扣款";
  function interrupt() {
    setJournal([charge, lang ? "Worker interrupted before receipt" : "回执前工作进程中断"]);
    setCharges(1); setPhase("stopped");
  }
  function resume(reuse: boolean) {
    setJournal([...journal, reuse ? (lang ? "Replayed payment result from journal" : "从日志读取已有扣款结果") : charge, lang ? "Receipt issued" : "已生成回执"]);
    setCharges(reuse ? 1 : 2); setPhase("finished");
  }
  return <Desk title={title} controls={<><button disabled={phase !== "ready"} onClick={interrupt}>{lang ? "Interrupt after payment" : "在扣款后中断"}</button>
    <button disabled={phase !== "stopped"} onClick={() => resume(true)}>{lang ? "Resume from journal" : "从日志恢复"}</button>
    <button disabled={phase !== "stopped"} onClick={() => resume(false)}>{lang ? "Restart without journal" : "忽略日志重跑"}</button></>}>
    <Metric value={charges} caption={lang ? "sample payment entries" : "示例扣款笔数"} />
    {!journal.length && <p>{lang ? "Order 104 · awaiting payment" : "订单 104 · 等待扣款"}</p>}
    <ol>{journal.map((event,i) => <li key={i}>{event}</li>)}</ol>
  </Desk>;
}

export function Rollout({ title, lang }: StudioProps) {
  const [share, setShare] = useState(20);
  const batch = Array.from({length: 100}, (_,i) => i);
  const failed = batch.filter(i => i < share ? i % 8 === 0 : i % 50 === 0);
  return <Desk title={title} controls={<><Range label={lang ? "Requests to version B (%)" : "分配至 B 版的请求（%）"} value={share} max={100} onChange={setShare} />
    <button disabled={share === 0} onClick={() => setShare(0)}>{lang ? "Roll back to A" : "回退至 A 版"}</button></>}>
    <Metric value={failed.length + " / 100"} caption={lang ? "errors in the fixture batch" : "样本请求中的错误数"} />
    <div className="task-traffic" aria-hidden="true">{batch.map(i => <i key={i} data-b={i < share} data-failed={failed.includes(i)} />)}</div>
    <p>A · {100 - share}　B · {share}</p><small>{lang ? "Red marks failed requests. Outlines mark version B." : "红色表示失败，描边表示 B 版。"}</small>
  </Desk>;
}
