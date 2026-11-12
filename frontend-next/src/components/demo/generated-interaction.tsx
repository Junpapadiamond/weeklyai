"use client";

import { useId, useState } from "react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { downloadDemoText } from "@/lib/demo-notes";
import {
  calculateInteractionRecords, changeInteractionInput, editorOutput, initialInteractionState, interactionDisclosure,
  interactionDraft, interactionVariantIndex, mergeInteractionReview, moveEditorField, recordCellText,
  selectedInteractionFacts, selectedInteractionRows, serializeInteraction, submitInteractionForm, updateInteractionDraft, updateRecordCell, visibleInteractionRows,
  type EditorDraft, type FormArtifact, type FormDraft, type Interaction, type InteractionDraft,
  type InteractionLanguage, type InteractionSource, type RecordsArtifact, type RecordsDraft, type ReviewArtifact, type ReviewDraft,
} from "@/lib/demo-interaction";
import "@/styles/demo-interaction.css";

type Shared = { lang: InteractionLanguage; outputLabel: string };
const text = (lang: InteractionLanguage, zh: string, en: string) => lang === "zh" ? zh : en;

function Editor({ draft, onChange, lang, outputLabel }: Shared & { draft: EditorDraft; onChange: (draft: EditorDraft) => void }) {
  const update = (fieldId: string, change: Partial<EditorDraft["fields"][number]>) => onChange({ ...draft, fields: draft.fields.map(field => field.id === fieldId ? { ...field, ...change } : field) });
  const output = editorOutput(draft);
  return <div className="gi-split">
    <section className="gi-edit"><h4>{text(lang, "编辑草稿", "Edit draft")}</h4>
      {draft.fields.map((field, index) => <fieldset key={field.id} className="gi-field-editor">
        <legend className="gi-sr-only">{field.label}</legend>
        <div className="gi-field-tools">
          <label className="gi-check"><input type="checkbox" checked={field.included} onChange={event => update(field.id, { included: event.target.checked })} />{text(lang, "保留", "Include")}</label>
          <div className="gi-order">
            <button type="button" disabled={index === 0} aria-label={`${text(lang, "上移", "Move up")}: ${field.label}`} onClick={() => onChange(moveEditorField(draft, field.id, -1))}>{text(lang, "上移", "Up")}</button>
            <button type="button" disabled={index === draft.fields.length - 1} aria-label={`${text(lang, "下移", "Move down")}: ${field.label}`} onClick={() => onChange(moveEditorField(draft, field.id, 1))}>{text(lang, "下移", "Down")}</button>
          </div>
        </div>
        <input aria-label={`${text(lang, "字段名称", "Field label")} ${index + 1}`} maxLength={80} value={field.label} onChange={event => update(field.id, { label: event.target.value })} />
        <textarea aria-label={field.label || text(lang, "字段内容", "Field content")} rows={4} maxLength={1400} value={field.value} onChange={event => update(field.id, { value: event.target.value })} />
      </fieldset>)}
    </section>
    <section className="gi-output"><h4>{outputLabel}</h4>{output ? <pre className="gi-prose">{output}</pre> : <p className="gi-empty">{text(lang, "选择要保留的字段", "Include a field to build your draft")}</p>}</section>
  </div>;
}

function Evidence({ text: content, quote, lang }: { text: string; quote: string; lang: InteractionLanguage }) {
  const at = content.indexOf(quote);
  return <details className="gi-evidence"><summary>{text(lang, "查看虚构原文", "Fictional source text")}</summary><blockquote>{at < 0 ? content : <>{content.slice(0, at)}<mark>{quote}</mark>{content.slice(at + quote.length)}</>}</blockquote></details>;
}

function Records({ artifact, draft, onChange, lang, outputLabel }: Shared & { artifact: RecordsArtifact; draft: RecordsDraft; onChange: (draft: RecordsDraft) => void }) {
  const id = useId();
  const rows = visibleInteractionRows(artifact, draft, lang);
  const selected = selectedInteractionRows(artifact, draft, lang);
  const primary = artifact.columns.find(col => col.type === "text") ?? artifact.columns[0];
  const rowName = (row: RecordsDraft["rows"][number]) => recordCellText(artifact, row, primary.id, lang);
  const selectRow = (rowId: string, checked: boolean) => onChange({ ...draft, selected: checked ? [...new Set([...draft.selected, rowId])] : draft.selected.filter(item => item !== rowId) });
  const cell = (row: RecordsDraft["rows"][number], col: RecordsArtifact["columns"][number]) => {
    const label = `${rowName(row)}: ${col.label[lang]}${col.unit ? ` (${col.unit[lang]})` : ""}`;
    if (col.type === "number") return <input type="number" step="any" required value={row.cells[col.id]} aria-label={label} onChange={event => onChange(updateRecordCell(artifact, draft, row.id, col.id, event.target.value === "" ? "" : event.target.valueAsNumber))} />;
    if (col.type === "select") return <select value={String(row.cells[col.id])} aria-label={label} onChange={event => onChange(updateRecordCell(artifact, draft, row.id, col.id, event.target.value))}>{col.options!.map(opt => <option key={opt.id} value={opt.id}>{opt.label[lang]}</option>)}</select>;
    return <span>{String(row.cells[col.id])}</span>;
  };
  const evidence = (row: RecordsDraft["rows"][number]) => {
    const original = artifact.rows.find(item => item.id === row.id)?.evidence;
    return original && <Evidence text={original.text[lang]} quote={original.quote[lang]} lang={lang} />;
  };
  const calc = artifact.calculation;
  const total = calculateInteractionRecords(artifact, draft);
  const numericColumn = calc && calc.op !== "count" ? artifact.columns.find(col => col.id === calc.column) : undefined;
  const groupColumn = artifact.columns.find(col => col.id === artifact.group_by);
  return <section className="gi-records">
    <div className="gi-record-controls">
      <label htmlFor={id + "-search"}>{text(lang, "搜索记录", "Search records")}<input id={id + "-search"} type="search" value={draft.query} onChange={event => onChange({ ...draft, query: event.target.value })} /></label>
      <label htmlFor={id + "-sort"}>{text(lang, "排序", "Sort")}<select id={id + "-sort"} value={draft.sort ? `${draft.sort.column}:${draft.sort.direction}` : ""} onChange={event => {
        const [column, direction] = event.target.value.split(":");
        onChange({ ...draft, sort: column ? { column, direction: direction === "desc" ? "desc" : "asc" } : null });
      }}><option value="">{text(lang, "原始顺序", "Original order")}</option>{artifact.columns.flatMap(col => (["asc", "desc"] as const).map(direction => <option key={`${col.id}:${direction}`} value={`${col.id}:${direction}`}>{col.label[lang]} · {direction === "asc" ? text(lang, "升序", "ascending") : text(lang, "降序", "descending")}</option>))}</select></label>
    </div>
    <h4>{outputLabel}</h4>
    {artifact.view === "board" && groupColumn ? <div className="gi-board" style={{ "--gi-columns": Math.min(groupColumn.options!.length, 3) } as React.CSSProperties}>
      {groupColumn.options!.map(group => <section className="gi-board-column" key={group.id}><h5>{group.label[lang]} <span>{rows.filter(row => row.cells[groupColumn.id] === group.id).length}</span></h5>
        {rows.filter(row => row.cells[groupColumn.id] === group.id).map(row => <article className="gi-record-card" key={row.id} data-selected={draft.selected.includes(row.id)}>
          <label className="gi-check"><input type="checkbox" checked={draft.selected.includes(row.id)} onChange={event => selectRow(row.id, event.target.checked)} /><strong>{rowName(row)}</strong></label>
          {artifact.columns.filter(col => col.id !== primary.id || primary.type !== "text").map(col => <div key={col.id} className="gi-card-cell"><span>{col.label[lang]}{col.unit ? ` (${col.unit[lang]})` : ""}</span>{cell(row, col)}</div>)}
          {evidence(row)}
        </article>)}
      </section>)}
    </div> : <div className="gi-table-scroll"><table><thead><tr><th scope="col">{text(lang, "选择", "Include")}</th>{artifact.columns.map(col => <th scope="col" key={col.id}>{col.label[lang]}{col.unit && <span className="gi-unit"> ({col.unit[lang]})</span>}</th>)}</tr></thead><tbody>
      {rows.map(row => <tr key={row.id} data-selected={draft.selected.includes(row.id)}><td><input type="checkbox" aria-label={`${text(lang, "选择", "Include")}: ${rowName(row)}`} checked={draft.selected.includes(row.id)} onChange={event => selectRow(row.id, event.target.checked)} /></td>{artifact.columns.map(col => <td key={col.id}>{cell(row, col)}{col.id === primary.id && evidence(row)}</td>)}</tr>)}
    </tbody></table></div>}
    {!rows.length && <p className="gi-empty" role="status">{text(lang, "没有匹配的记录", "No matching records")}</p>}
    {calc && <div className="gi-calculation"><span>{calc.label[lang]}</span><output>{total === null ? "—" : total.toLocaleString(lang, { maximumFractionDigits: 6 })} {numericColumn?.unit?.[lang]}</output>
      <small>{calc.op === "count" ? text(lang, "按所有已选记录计算；搜索不改变选择", "Counts all selected records; search does not change selection") : calc.op === "sum" ? text(lang, "使用所有行的当前数值；搜索和选择不改变总和", "Uses current values from all rows; search and selection do not change the sum") : `${rowName(draft.rows.find(row => row.id === calc.left)!)} − ${rowName(draft.rows.find(row => row.id === calc.right)!)}`}</small>
      {total === null && <small role="status">{text(lang, "请补全数字后查看结果", "Complete the numeric values to see the result")}</small>}
    </div>}
    <details className="gi-selected" open><summary>{text(lang, "保存的记录", "Records to save")} ({selected.length})</summary>
      {selected.length ? <ul>{selected.map(row => <li key={row.id}>{artifact.columns.map(col => `${recordCellText(artifact, row, col.id, lang)}${col.unit ? ` ${col.unit[lang]}` : ""}`).join(" · ")}</li>)}</ul> : <p className="gi-empty">{text(lang, "没有已选记录", "No records selected")}</p>}
    </details>
  </section>;
}

function Form({ artifact, draft, onChange, lang, outputLabel }: Shared & { artifact: FormArtifact; draft: FormDraft; onChange: (draft: FormDraft) => void }) {
  const id = useId();
  const update = (fieldId: string, change: Partial<FormDraft["fields"][number]>) => onChange({ ...draft, submission: null, fields: draft.fields.map(field => field.id === fieldId ? { ...field, ...change } : field) });
  const included = draft.fields.filter(field => field.included);
  return <div className="gi-split">
    <section className="gi-edit"><h4>{text(lang, "字段配置", "Field configuration")}</h4>
      <label className="gi-label" htmlFor={id + "-title"}>{text(lang, "表单标题", "Form title")}<input id={id + "-title"} maxLength={80} value={draft.title} onChange={event => onChange({ ...draft, title: event.target.value, submission: null })} /></label>
      {draft.fields.map((field, index) => <fieldset className="gi-field-editor" key={field.id}><legend className="gi-sr-only">{field.label}</legend>
        <input aria-label={`${text(lang, "字段名称", "Field label")} ${index + 1}`} maxLength={80} value={field.label} onChange={event => update(field.id, { label: event.target.value })} />
        <div className="gi-field-tools"><label className="gi-check"><input type="checkbox" checked={field.included} onChange={event => update(field.id, { included: event.target.checked })} />{text(lang, "包含", "Include")}</label>
          <label className="gi-check"><input type="checkbox" disabled={!field.included} checked={field.required} onChange={event => update(field.id, { required: event.target.checked })} />{text(lang, "必填", "Required")}</label></div>
      </fieldset>)}
    </section>
    <section className="gi-output"><h4>{outputLabel}</h4><form className="gi-preview-form" onSubmit={event => { event.preventDefault(); onChange(submitInteractionForm(draft)); }}>
      <h5>{draft.title}</h5>
      {included.map(field => <label className="gi-label" htmlFor={`${id}-preview-${field.id}`} key={field.id}>{field.label}{field.required && <span aria-hidden="true"> *</span>}
        <input id={`${id}-preview-${field.id}`} aria-label={field.label || text(lang, "未命名字段", "Untitled field")} type={field.type} required={field.required} pattern={field.type === "text" && field.required ? ".*\\S.*" : undefined} step={field.type === "number" ? "any" : undefined} value={field.value} maxLength={field.type !== "number" ? 300 : undefined} autoComplete="off" onChange={event => update(field.id, { value: event.target.value })} />
      </label>)}
      {!included.length && <p className="gi-empty">{text(lang, "先添加一个字段", "Include a field first")}</p>}
      <button className="gi-primary" type="submit" disabled={!included.length}>{artifact.submit_label[lang]}</button>
      <p className="gi-local-note">{text(lang, "仅在当前页面验证，不发送内容", "Validated on this page; nothing is sent")}</p>
      {draft.submission && <div className="gi-submission" role="status"><strong>{artifact.confirmation[lang]}</strong><dl>{draft.submission.map((field, index) => <div key={index}><dt>{field.label}</dt><dd>{field.value || "—"}</dd></div>)}</dl></div>}
    </form></section>
  </div>;
}

function Review({ artifact, draft, onChange, lang, outputLabel }: Shared & { artifact: ReviewArtifact; draft: ReviewDraft; onChange: (draft: ReviewDraft) => void }) {
  return <div className="gi-split">
    <section className="gi-edit"><h4>{text(lang, "选择修改", "Choose edits")}</h4>
      <details className="gi-original"><summary>{text(lang, "原始内容", "Original text")}</summary><pre>{artifact.base[lang]}</pre></details>
      {artifact.patches.map(patch => <fieldset className="gi-patch" key={patch.id}><legend>{patch.label[lang]}</legend>
        <pre className="gi-before"><span className="gi-diff-label">− {text(lang, "原文", "Before")}</span>{patch.before[lang]}</pre>
        <pre className="gi-after"><span className="gi-diff-label">+ {text(lang, "修改后", "After")}</span>{patch.after[lang]}</pre>
        <label className="gi-check"><input type="checkbox" checked={draft.accepted.includes(patch.id)} onChange={event => onChange({ ...draft, accepted: event.target.checked ? [...draft.accepted, patch.id] : draft.accepted.filter(item => item !== patch.id) })} />{text(lang, "采用这处修改", "Apply this edit")}</label>
      </fieldset>)}
    </section>
    <section className="gi-output"><h4>{outputLabel}</h4><pre className="gi-code">{mergeInteractionReview(artifact, draft, lang)}</pre><p className="gi-local-note">{text(lang, "仅合并文本；未执行代码或测试", "Text merge only; no code or tests executed")}</p></section>
  </div>;
}

export type GeneratedInteractionProps = { interaction: Interaction; productName: string; sources: InteractionSource[]; embedded?: boolean };

export function GeneratedInteraction({ interaction, productName, sources, embedded }: GeneratedInteractionProps) {
  const { locale, t } = useSiteLocale();
  const lang: InteractionLanguage = locale === "en-US" ? "en" : "zh";
  const id = useId();
  const [state, setState] = useState(() => initialInteractionState(interaction));
  const [notice, setNotice] = useState<"saved" | "reset" | null>(null);
  const index = interactionVariantIndex(interaction, state.inputs);
  const variant = interaction.variants[index];
  const facts = [...new Set(selectedInteractionFacts(interaction, state.inputs).map(fact => fact[lang]))].filter(fact => !variant.brief[lang].includes(fact));
  const draft = interactionDraft(interaction, state, lang);
  const update = (next: InteractionDraft) => { setState(previous => updateInteractionDraft(interaction, previous, lang, next)); setNotice(null); };
  const shared = { lang, outputLabel: interaction.output_label[lang] };

  return <div className={`generated-interaction${embedded ? " generated-interaction--embedded" : ""}`} data-interaction-kind={interaction.kind}>
    {!!interaction.inputs.length && <div className="gi-inputs">{interaction.inputs.map(control => <fieldset key={control.id}><legend>{control.label[lang]}</legend><div>
      {control.options.map(opt => <label key={opt.id} data-selected={state.inputs[control.id] === opt.id}><input type="radio" name={`${id}-${control.id}`} value={opt.id} checked={state.inputs[control.id] === opt.id} onChange={() => { setState(previous => changeInteractionInput(interaction, previous, control.id, opt.id)); setNotice(null); }} /><span>{opt.label[lang]}</span></label>)}
    </div></fieldset>)}</div>}
    <p className="gi-brief">{variant.brief[lang]}</p>
    <p className="gi-disclosure">{interactionDisclosure(lang)}</p>
    {!!facts.length && <details className="gi-facts"><summary>{t("示例输入事实", "Sample input facts")}</summary><ul>{facts.map(fact => <li key={fact}>{fact}</li>)}</ul></details>}
    {interaction.kind === "editor" && draft.kind === "editor" && <Editor {...shared} draft={draft} onChange={update} />}
    {interaction.kind === "records" && draft.kind === "records" && <Records {...shared} artifact={interaction.variants[index].artifact} draft={draft} onChange={update} />}
    {interaction.kind === "form" && draft.kind === "form" && <Form {...shared} artifact={interaction.variants[index].artifact} draft={draft} onChange={update} />}
    {interaction.kind === "review" && draft.kind === "review" && <Review {...shared} artifact={interaction.variants[index].artifact} draft={draft} onChange={update} />}
    <footer className="gi-footer">
      <div className="gi-actions"><button type="button" onClick={() => { downloadDemoText(serializeInteraction(interaction, state, lang, productName, sources), "darkhorse-example.txt"); setNotice("saved"); }}>{t("保存当前结果", "Save current result")}</button>
        <button type="button" onClick={() => { setState(initialInteractionState(interaction)); setNotice("reset"); }}>{t("重置全部编辑", "Reset all edits")}</button>
        <span className="gi-notice" role="status">{notice === "saved" ? t("已下载文本", "Text downloaded") : notice === "reset" ? t("已恢复初始示例", "Original example restored") : ""}</span>
      </div>
      <details className="gi-sources"><summary>{t("产品资料与示例边界", "Product sources & example limits")}</summary>
        <p>{t("资料用于了解产品方向，不证明这里的虚构数据或结果。实际能力请以官方产品为准。", "These sources explain the product, not the fictional data or results here. Check the official product for actual capabilities.")}</p>
        <ul>{sources.map(source => <li key={source.url}><a href={source.url} target="_blank" rel="noopener noreferrer">{source.label[lang]}</a></li>)}</ul>
      </details>
    </footer>
  </div>;
}
