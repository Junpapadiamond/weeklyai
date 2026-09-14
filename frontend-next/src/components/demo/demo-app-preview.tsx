"use client";

import { useEffect, useId, useRef, useState } from "react";
import type { CSSProperties, FormEvent } from "react";
import type { DemoSpec } from "@/lib/live-demo";

type PreviewProps = { spec: DemoSpec; en: boolean };

function FocusTimer({ spec, en }: PreviewProps) {
  const [duration, setDuration] = useState(spec.minutes);
  const [seconds, setSeconds] = useState(spec.minutes * 60);
  const [running, setRunning] = useState(false);
  const deadline = useRef(0);

  useEffect(() => {
    if (!running) return;
    const interval = window.setInterval(() => {
      const remaining = Math.max(0, Math.ceil((deadline.current - Date.now()) / 1000));
      setSeconds(remaining);
      if (remaining === 0) setRunning(false);
    }, 200);
    return () => window.clearInterval(interval);
  }, [running]);

  function reset(minutes = duration) {
    setRunning(false);
    setDuration(minutes);
    setSeconds(minutes * 60);
  }

  function toggle() {
    if (running) {
      setSeconds(Math.max(0, Math.ceil((deadline.current - Date.now()) / 1000)));
      setRunning(false);
    } else {
      const next = seconds || duration * 60;
      deadline.current = Date.now() + next * 1000;
      setSeconds(next);
      setRunning(true);
    }
  }

  return <>
    <div className="demo-timer-modes" aria-label={en ? "Timer duration" : "计时时长"}>
      {[...new Set([spec.minutes, 5, 15])].map(minutes => <button type="button" key={minutes}
        aria-pressed={duration === minutes} onClick={() => reset(minutes)}>
        {minutes} {en ? "min" : "分钟"}
      </button>)}
    </div>
    <div className="demo-clock" style={{ "--demo-progress": `${(1 - seconds / (duration * 60)) * 100}%` } as CSSProperties}>
      <div className="demo-clock-inner">
        <span className="demo-clock-label">{running ? (en ? "IN YOUR OWN TIME" : "专注正在发生") : (en ? "A FRESH START" : "从这一刻开始")}</span>
        <span className="demo-clock-digits" role="timer" aria-label={en ? "Time remaining" : "剩余时间"}>
          {String(Math.floor(seconds / 60)).padStart(2, "0")}<span>:</span>{String(seconds % 60).padStart(2, "0")}
        </span>
        <span className="demo-clock-caption">{seconds === 0 ? (en ? "Well done. Take a breath." : "完成了，休息一下吧。")
          : (en ? "One thing at a time." : "一次，只做一件事。")}</span>
      </div>
    </div>
    <div className="demo-app-actions">
      <button type="button" className="demo-app-primary" onClick={toggle}>{running ? (en ? "Pause" : "暂停") : (en ? "Start focusing" : "开始专注")}</button>
      <button type="button" className="demo-app-secondary" onClick={() => reset()}>{en ? "Reset" : "重置"}</button>
    </div>
  </>;
}

function TaskList({ spec, en }: PreviewProps) {
  const [tasks, setTasks] = useState(() => spec.items.map((text, id) => ({ id, text, done: false })));
  const nextId = useRef(spec.items.length);
  const [draft, setDraft] = useState("");
  const id = useId();
  const completed = tasks.filter(task => task.done).length;

  function add(event: FormEvent) {
    event.preventDefault();
    if (!draft.trim() || tasks.length >= 30) return;
    setTasks([...tasks, { id: nextId.current++, text: draft.trim(), done: false }]);
    setDraft("");
  }

  return <div className="demo-tasks">
    <div className="demo-task-progress"><span>{en ? "Your progress" : "今天的进度"}</span><strong>{completed} / {tasks.length}</strong></div>
    <progress value={completed} max={Math.max(tasks.length, 1)} aria-label={en ? "Completed tasks" : "已完成任务"} />
    <ul className="demo-task-list">
      {tasks.map(task => <li key={task.id} className={task.done ? "is-done" : ""}>
        <label><input type="checkbox" checked={task.done} onChange={() => setTasks(tasks.map(item => item.id === task.id ? { ...item, done: !item.done } : item))} /><span>{task.text}</span></label>
        <button type="button" className="demo-remove" onClick={() => setTasks(tasks.filter(item => item.id !== task.id))} aria-label={`${en ? "Delete" : "删除"} ${task.text}`}>×</button>
      </li>)}
    </ul>
    {tasks.length === 0 ? <p className="demo-app-empty">{en ? "A clear page. Add your first small step." : "清单空了。添加你想完成的第一件小事吧。"}</p> : null}
    <form className="demo-task-form" onSubmit={add}>
      <label htmlFor={id}>{en ? "What is your next small step?" : "下一件想做的小事"}</label>
      <div><input id={id} value={draft} maxLength={80} onChange={event => setDraft(event.target.value)} placeholder={en ? "e.g. Try an AI product" : "例如：试用一个 AI 产品"} required />
        <button className="demo-app-primary" disabled={!draft.trim() || tasks.length >= 30}>{en ? "Add" : "添加"}</button></div>
      {tasks.length >= 30 ? <p role="status">{en ? "This demo holds up to 30 tasks." : "这个演示最多保留 30 个任务。"}</p> : null}
    </form>
  </div>;
}

function Expenses({ en }: PreviewProps) {
  const [entries, setEntries] = useState<{ id: number; label: string; cents: number }[]>([]);
  const [label, setLabel] = useState("");
  const [amount, setAmount] = useState("");
  const [error, setError] = useState("");
  const nextId = useRef(0);
  const id = useId();
  const total = entries.reduce((sum, entry) => sum + entry.cents, 0);
  const currency = en ? "$" : "¥";

  function add(event: FormEvent) {
    event.preventDefault();
    const cents = Math.round(Number(amount) * 100);
    if (!label.trim() || !Number.isFinite(cents) || cents <= 0 || cents > 10000000) {
      setError(en ? "Enter a label and an amount between 0.01 and 100,000." : "请填写名称和 0.01–100,000 之间的金额。");
      return;
    }
    if (entries.length >= 50) { setError(en ? "This demo holds up to 50 entries." : "这个演示最多保留 50 条记录。"); return; }
    setEntries([...entries, { id: nextId.current++, label: label.trim(), cents }]);
    setLabel(""); setAmount(""); setError("");
  }

  return <div className="demo-expenses">
    <div className="demo-expense-total"><span>{en ? "TOTAL SPENT" : "本次记录总额"}</span><strong><small>{currency}</small>{(total / 100).toFixed(2)}</strong>
      <span>{entries.length} {en ? "entries · try adding one below" : "笔记录 · 在下面记一笔试试"}</span></div>
    <form className="demo-expense-form" onSubmit={add}>
      <label htmlFor={`${id}-label`}>{en ? "What was it for?" : "花在了哪里"}<input id={`${id}-label`} value={label} onChange={event => setLabel(event.target.value)} maxLength={60} placeholder={en ? "A coffee with a friend" : "和朋友喝一杯咖啡"} required /></label>
      <label htmlFor={`${id}-amount`}>{en ? "Amount" : "金额"}<input id={`${id}-amount`} type="number" inputMode="decimal" min="0.01" max="100000" step="0.01" value={amount} onChange={event => setAmount(event.target.value)} placeholder="0.00" required /></label>
      <button className="demo-app-primary">{en ? "Add expense" : "记一笔"}</button>
    </form>
    {error ? <p className="demo-inline-error" role="alert">{error}</p> : null}
    <ul className="demo-expense-list">{entries.map(entry => <li key={entry.id}><span>{entry.label}</span><strong>{currency}{(entry.cents / 100).toFixed(2)}</strong><button type="button" className="demo-remove" onClick={() => setEntries(entries.filter(item => item.id !== entry.id))} aria-label={`${en ? "Delete" : "删除"} ${entry.label}`}>×</button></li>)}</ul>
    {entries.length === 0 ? <p className="demo-app-empty">{en ? "Your first entry will appear here." : "第一笔记录会出现在这里。"}</p> : null}
  </div>;
}

export function DemoAppPreview({ spec, en }: PreviewProps) {
  return <div className="demo-mini-app" data-accent={spec.accent}>
    <div className="demo-mini-brand"><span className="demo-mini-mark" aria-hidden="true" />{spec.kind === "timer" ? "little focus" : spec.kind === "tasks" ? "small steps" : "daily ledger"}<span className="demo-mini-edition">01 / PERSONAL SPACE</span></div>
    <header className="demo-mini-header"><h4>{spec.title}</h4><p>{spec.description}</p></header>
    {spec.kind === "timer" ? <FocusTimer spec={spec} en={en} /> : spec.kind === "tasks" ? <TaskList spec={spec} en={en} /> : <Expenses spec={spec} en={en} />}
    <footer className="demo-mini-footer">{en ? "Made to be tried. Go ahead, click something." : "这是一个可以操作的小作品。动手试试。"}</footer>
  </div>;
}
