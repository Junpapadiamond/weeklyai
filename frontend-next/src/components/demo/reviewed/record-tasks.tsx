import { useState } from "react";
import { Desk, Empty, Toggle, replaceAt } from "./parts";
import type { Props } from "./types";

export function Evidence({ task, lang }: Props<"evidence">) {
  const [included, setIncluded] = useState(task.rows.map((_, i) => i === 0));
  const [drafts, setDrafts] = useState(task.rows.map(row => row[2][lang]));
  return <Desk title={task.result[lang]} controls={task.rows.map(([quote], i) =>
    <Toggle key={i} checked={included[i]} onChange={() => setIncluded(replaceAt(included, i, !included[i]))}>
      <small>{lang ? "Source" : "原文"} {i + 1}</small>{quote[lang]}
    </Toggle>)}>
    {task.rows.map(([, field], i) => included[i] && <label className="task-field" key={i}>
      <span>{field[lang]} <small>〔{i + 1}〕</small></span>
      <textarea maxLength={500} value={drafts[i]} onChange={e => setDrafts(replaceAt(drafts, i, e.target.value))} />
    </label>)}
    {!included.some(Boolean) && <p>{lang ? "Choose a source to add a field to the draft." : "选取一条原文，即可在底稿中加入对应字段。"}</p>}
  </Desk>;
}

export function SearchPassages({ task, lang }: Props<"search">) {
  const [query, setQuery] = useState(task.query?.[lang] ?? "");
  const words = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const hits = task.rows.map(([name, body, tags]) => {
    const haystack = [name, body, tags].map(field => field[lang]).join(" ").toLowerCase();
    return { name, body, score: words.filter(word => haystack.includes(word)).length };
  }).filter(hit => !words.length || hit.score).sort((a, b) => b.score - a.score);
  return <Desk title={task.result[lang]} controls={<label className="task-field">{lang ? "Search the sample collection" : "搜索示例资料"}
    <input type="search" value={query} maxLength={150} onChange={e => setQuery(e.target.value)} /></label>}>
    {hits.length ? hits.map(({ name, body }, i) => <details key={name[1]} open={i === 0} className="task-passage">
      <summary>{name[lang]}</summary><p>{body[lang]}</p></details>) : <Empty lang={lang} />}
  </Desk>;
}

export function Recall({ task, lang }: Props<"quiz">) {
  const [queue, setQueue] = useState(task.rows.map((_, i) => i));
  const [started, setStarted] = useState(false);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState("");
  const card = task.rows[queue[0]];
  function grade(e: React.FormEvent) {
    e.preventDefault();
    if (!answer.trim() || !card) return;
    const correct = answer.trim().toLowerCase() === card[2][lang].toLowerCase();
    setQueue(correct ? queue.slice(1) : [...queue.slice(1), queue[0]]);
    setFeedback(correct ? (lang ? "Correct." : "答对了。") : (lang ? "Review again: " : "稍后再练：") + card[2][lang]);
    setAnswer("");
  }
  return <Desk title={task.result[lang]} controls={<><p>{lang ? "Course notes" : "课程笔记"}</p>{!started
    ? task.rows.map(([note]) => <p key={note[1]}>{note[lang]}</p>)
    : <details><summary>{lang ? "Consult notes" : "查阅笔记"}</summary>{task.rows.map(([note]) => <p key={note[1]}>{note[lang]}</p>)}</details>}</>}>
    <strong>{task.rows.length - queue.length} / {task.rows.length}</strong>
    {!started ? <><p>{card[1][lang]}</p><button onClick={() => setStarted(true)}>{lang ? "Start recall" : "开始回忆练习"}</button></>
    : card ? <form onSubmit={grade}><label className="task-field">{card[1][lang]}<input value={answer} maxLength={100} onChange={e => setAnswer(e.target.value)} /></label>
      <button disabled={!answer.trim()}>{lang ? "Check answer" : "核对答案"}</button></form>
    : <p>{lang ? "All cards recalled." : "已答对全部复习卡。"}</p>}
    <p role="status">{feedback}</p>
  </Desk>;
}
