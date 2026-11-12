import { z } from "zod";

export type InteractionLanguage = "zh" | "en";
export type InteractionCopy = { zh: string; en: string };
const id = z.string().min(1).max(40).regex(/^[A-Za-z0-9_-]+$/).refine(value => !/[\r\n]/.test(value));
// Mirror the server's representation checks. These are not a fact checker;
// text is still rendered escaped and the local-example disclosure stays visible.
const unsafeCopy = /https?:\/\/|www\.|javascript:|data:|<\s*\/?\s*[a-z][^>]*>|\d+(?:\.\d+)?\s*[%％]|\b(?:accuracy|precision|recall|latency|throughput|speedup|response time)\s*(?:[:=]|of|is)?\s*\d|\b\d+(?:\.\d+)?\s*(?:ms|milliseconds|times faster)\b|Exported:|\b(?:agent deployed|connected (?:to |the )?(?:vendor|account|SEC|data stream)|interviews? (?:completed|conducted)|(?:completed|conducted) interviews?|video (?:generated|rendered)|(?:file|image|video) (?:saved|exported)|saved (?:locally|to (?:your |the )?(?:device|computer))|contract delivered)\b|已(?:部署|连接|开展访谈|完成访谈|导出|保存本地)|文件已保存|视频已生成/i;
const inertGeneric = /\b(?:Array|ReadonlyArray|Promise|Record|Map|Set|Partial|Required|Pick|Omit|Readonly)\s*<\s*[A-Za-z_$][\w.$]*(?:\s*\[\])?(?:\s*[,|]\s*[A-Za-z_$][\w.$]*(?:\s*\[\])?)*\s*>/g;
// Preserve whitespace: review patches must match their source exactly.
const copy = (max: number, inert = false) => {
  const value = z.string().refine(text => text.trim().length > 0 && [...text].length <= max, `Expected nonempty text up to ${max} characters`)
    .refine(text => !unsafeCopy.test(inert ? text.replace(inertGeneric, match => match.replaceAll("<", "(").replaceAll(">", ")")).replace(/(?<=\s)<(?=\s)/g, "less-than") : text), "Unsupported content representation");
  return z.object({ zh: value, en: value }).strict();
};
const option = z.object({ id, label: copy(80) }).strict();
const inputOption = option.extend({ facts: z.array(copy(120)).min(1).max(5).optional() }).strict();
const input = z.object({ id, label: copy(80), options: z.array(inputOption).min(2).max(3) }).strict();
const editorArtifact = z.object({ fields: z.array(z.object({ id, label: copy(80), value: copy(1400) }).strict()).min(2).max(6) }).strict();
const column = z.object({
  id, label: copy(80), type: z.enum(["text", "number", "select"]), unit: copy(80).optional(),
  options: z.array(option).min(2).max(6).optional(),
}).strict();
const calculation = z.discriminatedUnion("op", [
  z.object({ op: z.literal("sum"), column: id, label: copy(80) }).strict(),
  z.object({ op: z.literal("difference"), column: id, left: id, right: id, label: copy(80) }).strict(),
  z.object({ op: z.literal("count"), label: copy(80) }).strict(),
]);
const recordsArtifact = z.object({
  columns: z.array(column).min(2).max(5),
  rows: z.array(z.object({
    id, cells: z.record(id, z.union([copy(1400), z.number().finite(), id])),
    evidence: z.object({ text: copy(1400), quote: copy(1400) }).strict().optional(),
  }).strict()).min(2).max(6),
  view: z.enum(["table", "board"]), group_by: id.optional(), calculation: calculation.optional(),
}).strict();
const formArtifact = z.object({
  title: copy(80), fields: z.array(z.object({ id, label: copy(80), type: z.enum(["text", "email", "number"]), required: z.boolean() }).strict()).min(2).max(5),
  submit_label: copy(80), confirmation: copy(300),
}).strict();
const reviewArtifact = z.object({
  base: copy(1400, true), patches: z.array(z.object({ id, label: copy(80), before: copy(700, true), after: copy(700, true) }).strict()).min(2).max(4),
}).strict();
const base = { input_label: copy(80), output_label: copy(80), inputs: z.array(input).max(2) };
const variant = <T extends z.ZodType>(artifact: T) => z.object({ when: z.record(id, id), brief: copy(300), artifact }).strict();
const interaction = z.discriminatedUnion("kind", [
  z.object({ ...base, kind: z.literal("editor"), variants: z.array(variant(editorArtifact)).min(1).max(4) }).strict(),
  z.object({ ...base, kind: z.literal("records"), variants: z.array(variant(recordsArtifact)).min(1).max(4) }).strict(),
  z.object({ ...base, kind: z.literal("form"), variants: z.array(variant(formArtifact)).min(1).max(4) }).strict(),
  z.object({ ...base, kind: z.literal("review"), variants: z.array(variant(reviewArtifact)).min(1).max(4) }).strict(),
]);

function unique(values: string[]) { return new Set(values).size === values.length; }
function occurrences(text: string, search: string) {
  const positions: number[] = [];
  for (let at = text.indexOf(search); at !== -1; at = text.indexOf(search, at + 1)) positions.push(at);
  return positions;
}
function artifactFingerprint(spec: z.infer<typeof interaction>, index: number, lang: InteractionLanguage): string {
  // Structure IDs and decorative copy cannot disguise an unchanged outcome.
  if (spec.kind === "editor") return JSON.stringify(spec.variants[index].artifact.fields.map(field => field.value[lang]));
  if (spec.kind === "form") return JSON.stringify(spec.variants[index].artifact.fields.map(field => ({ type: field.type, required: field.required })));
  if (spec.kind === "review") {
    const artifact = spec.variants[index].artifact;
    return JSON.stringify({ base: artifact.base[lang], patches: artifact.patches.map(patch => ({ before: patch.before[lang], after: patch.after[lang] })) });
  }
  const artifact = spec.variants[index].artifact;
  const calc = artifact.calculation;
  return JSON.stringify({
    types: artifact.columns.map(col => col.type),
    rows: artifact.rows.map(row => ({ cells: artifact.columns.map(col => {
      const cell = row.cells[col.id];
      return col.type === "select" ? col.options?.findIndex(opt => opt.id === cell) : typeof cell === "object" ? cell[lang] : cell;
    }) })),
    ...(calc ? { calculation: { op: calc.op, ...(calc.op !== "count" ? { columnIndex: artifact.columns.findIndex(col => col.id === calc.column) } : {}), ...(calc.op === "difference" ? { leftRowIndex: artifact.rows.findIndex(row => row.id === calc.left), rightRowIndex: artifact.rows.findIndex(row => row.id === calc.right) } : {}) } } : {}),
  });
}

function artifactFactLeaves(spec: z.infer<typeof interaction>, index: number, lang: InteractionLanguage): string[] {
  if (spec.kind === "editor") return spec.variants[index].artifact.fields.map(field => field.value[lang]);
  if (spec.kind === "form") {
    const artifact = spec.variants[index].artifact;
    return [artifact.title[lang], ...artifact.fields.map(field => field.label[lang])];
  }
  if (spec.kind === "review") {
    // Review facts are validated in every merged state below, not in a union of
    // source/replacement fragments which may never coexist in the actual output.
    return [spec.variants[index].artifact.base[lang]];
  }
  const artifact = spec.variants[index].artifact;
  return artifact.rows.flatMap(row => [
    ...artifact.columns.flatMap(col => {
      const cell = row.cells[col.id];
      if (col.type === "select") return col.options?.find(opt => opt.id === cell)?.label[lang] ?? [];
      if (col.type === "number") return typeof cell === "number" ? String(cell) : [];
      return cell && typeof cell === "object" ? cell[lang] : [];
    }),
    ...(row.evidence ? [row.evidence.text[lang], row.evidence.quote[lang]] : []),
  ]);
}

export const InteractionSchema = interaction.superRefine((value, context) => {
  const fail = (message: string) => context.addIssue({ code: "custom", message });
  if (value.kind === "editor" && value.inputs.length === 2 && !value.inputs.some(control => control.options.every(opt => !!opt.facts?.length))) fail("Two-input editors need fact-bound options on at least one input");
  if (!unique(value.inputs.map(item => item.id))) fail("Duplicate input IDs");
  for (const item of value.inputs) if (!unique(item.options.map(opt => opt.id))) fail("Duplicate input option IDs");
  const combinations = value.inputs.reduce<Record<string, string>[]>((all, item) => all.flatMap(previous => item.options.map(opt => ({ ...previous, [item.id]: opt.id }))), [{}]);
  if (combinations.length > 4 || value.variants.length !== combinations.length) fail("Variants must cover the complete input product, at most four");
  for (const item of value.variants) {
    if (Object.keys(item.when).length !== value.inputs.length || value.inputs.some(control => !control.options.some(opt => Object.hasOwn(item.when, control.id) && item.when[control.id] === opt.id))) fail("Invalid variant input reference");
  }
  for (const combination of combinations) {
    if (value.variants.filter(item => Object.keys(item.when).length === Object.keys(combination).length && Object.keys(combination).every(key => item.when[key] === combination[key])).length !== 1) fail("Missing or duplicate variant");
  }
  // Every single-input change must have a visible artifact consequence in BOTH locales.
  for (let a = 0; a < value.variants.length; a++) for (let b = a + 1; b < value.variants.length; b++) {
    if (value.inputs.filter(control => value.variants[a].when[control.id] !== value.variants[b].when[control.id]).length === 1) {
      for (const lang of ["zh", "en"] as const) if (artifactFingerprint(value, a, lang) === artifactFingerprint(value, b, lang)) fail(`Input change has no ${lang} artifact consequence`);
    }
  }
  if (value.kind === "editor" || value.kind === "form") {
    for (const item of value.variants) if (!unique(item.artifact.fields.map(field => field.id))) fail("Duplicate field IDs");
  }
  if (value.kind === "records") for (const { artifact } of value.variants) {
    if (!unique(artifact.columns.map(item => item.id)) || !unique(artifact.rows.map(item => item.id))) fail("Duplicate record IDs");
    for (const col of artifact.columns) {
      if (col.type === "number" && !col.unit) fail("Numeric columns need explicit units");
      if (col.type !== "number" && col.unit) fail("Only numeric columns have units");
      if (col.type === "select" && (!col.options || !unique(col.options.map(opt => opt.id)))) fail("Select columns need distinct options");
      if (col.type !== "select" && col.options) fail("Only select columns have options");
    }
    if ((artifact.view === "board" || artifact.group_by !== undefined) && !artifact.columns.some(col => col.id === artifact.group_by && col.type === "select")) fail("Board grouping must reference a select column");
    for (const row of artifact.rows) {
      if (Object.keys(row.cells).length !== artifact.columns.length) fail("Missing or extra cells");
      for (const col of artifact.columns) {
        const cell = row.cells[col.id];
        if (!Object.hasOwn(row.cells, col.id) || (col.type === "number" ? typeof cell !== "number" : col.type === "text" ? !cell || typeof cell !== "object" : typeof cell !== "string" || !col.options?.some(opt => opt.id === cell))) fail("Cell does not match its column type");
      }
      if (row.evidence && (["zh", "en"] as const).some(lang => !row.evidence!.text[lang].includes(row.evidence!.quote[lang]))) fail("Evidence quote must occur in its text");
    }
    const calc = artifact.calculation;
    if (calc && calc.op !== "count") {
      if (!artifact.columns.some(col => col.id === calc.column && col.type === "number")) fail("Calculation must reference a numeric column");
      if (calc.op === "difference" && (calc.left === calc.right || !artifact.rows.some(row => row.id === calc.left) || !artifact.rows.some(row => row.id === calc.right))) fail("Difference must reference two distinct rows");
    }
  }
  if (value.kind === "review") for (const { artifact } of value.variants) {
    if (!unique(artifact.patches.map(patch => patch.id))) fail("Duplicate patch IDs");
    for (const lang of ["zh", "en"] as const) {
      const ranges: { start: number; end: number }[] = [];
      for (const patch of artifact.patches) {
        const positions = occurrences(artifact.base[lang], patch.before[lang]);
        if (positions.length !== 1) fail("Patch before must occur exactly once");
        if (patch.before[lang] === patch.after[lang]) fail("Patch must change the text");
        if (positions.length === 1) ranges.push({ start: positions[0], end: positions[0] + patch.before[lang].length });
      }
      ranges.sort((a, b) => a.start - b.start);
      if (ranges.some((range, index) => index > 0 && range.start < ranges[index - 1].end)) fail("Patches must not overlap");
    }
  }
  for (let index = 0; index < value.variants.length; index++) {
    const selected = value.inputs.flatMap(control => control.options.find(opt => opt.id === value.variants[index].when[control.id])?.facts ?? []);
    const unselected = value.inputs.flatMap(control => control.options.filter(opt => opt.id !== value.variants[index].when[control.id]).flatMap(opt => opt.facts ?? []));
    for (const lang of ["zh", "en"] as const) {
      const selectedText = selected.map(fact => fact[lang]);
      const contexts = value.kind === "review" ? Array.from({ length: 1 << value.variants[index].artifact.patches.length }, (_, mask) => {
        const artifact = value.variants[index].artifact;
        const accepted = artifact.patches.filter((_, bit) => mask & (1 << bit)).map(patch => patch.id);
        return [mergeInteractionReview(artifact, { kind: "review", accepted }, lang)];
      }) : [artifactFactLeaves(value, index, lang)];
      if (contexts.some(leaves => selectedText.some(fact => !leaves.some(leaf => leaf.includes(fact))))) fail(`Selected ${lang} input fact is missing from a reachable artifact state`);
      if (contexts.some(leaves => unselected.some(fact => !selectedText.includes(fact[lang]) && leaves.some(leaf => leaf.includes(fact[lang]))))) fail(`A reachable artifact state contains an unselected ${lang} input fact`);
    }
  }
});

export type Interaction = z.infer<typeof InteractionSchema>;
export type EditorArtifact = z.infer<typeof editorArtifact>;
export type RecordsArtifact = z.infer<typeof recordsArtifact>;
export type FormArtifact = z.infer<typeof formArtifact>;
export type ReviewArtifact = z.infer<typeof reviewArtifact>;
export type InteractionSource = { label: InteractionCopy; url: string };
export type EditorDraft = { kind: "editor"; fields: { id: string; label: string; value: string; included: boolean }[] };
export type RecordsDraft = { kind: "records"; rows: { id: string; cells: Record<string, string | number> }[]; selected: string[]; query: string; sort: { column: string; direction: "asc" | "desc" } | null };
export type FormDraft = { kind: "form"; title: string; fields: { id: string; label: string; type: "text" | "email" | "number"; required: boolean; included: boolean; value: string }[]; submission: { label: string; value: string }[] | null };
export type ReviewDraft = { kind: "review"; accepted: string[] };
export type InteractionDraft = EditorDraft | RecordsDraft | FormDraft | ReviewDraft;
export type InteractionState = { inputs: Record<string, string>; drafts: Record<string, InteractionDraft> };

export function initialInteractionState(spec: Interaction): InteractionState {
  return { inputs: Object.fromEntries(spec.inputs.map(item => [item.id, item.options[0].id])), drafts: {} };
}
export function selectedInteractionFacts(spec: Interaction, inputs: Record<string, string>): InteractionCopy[] {
  return spec.inputs.flatMap(control => control.options.find(opt => opt.id === inputs[control.id])?.facts ?? []);
}
export function interactionVariantIndex(spec: Interaction, inputs: Record<string, string>) {
  return spec.variants.findIndex(item => spec.inputs.every(control => item.when[control.id] === inputs[control.id]));
}
export function changeInteractionInput(spec: Interaction, state: InteractionState, inputId: string, optionId: string): InteractionState {
  if (!spec.inputs.some(item => item.id === inputId && item.options.some(opt => opt.id === optionId))) return state;
  return { ...state, inputs: { ...state.inputs, [inputId]: optionId } };
}
export function initialInteractionDraft(spec: Interaction, index: number, lang: InteractionLanguage): InteractionDraft {
  if (spec.kind === "editor") return { kind: "editor", fields: spec.variants[index].artifact.fields.map(field => ({ id: field.id, label: field.label[lang], value: field.value[lang], included: true })) };
  if (spec.kind === "records") return {
    kind: "records", rows: spec.variants[index].artifact.rows.map(row => ({ id: row.id, cells: Object.fromEntries(Object.entries(row.cells).map(([key, cell]) => [key, typeof cell === "object" ? cell[lang] : cell])) })),
    selected: spec.variants[index].artifact.rows.map(row => row.id), query: "", sort: null,
  };
  if (spec.kind === "form") return {
    kind: "form", title: spec.variants[index].artifact.title[lang], fields: spec.variants[index].artifact.fields.map(field => ({ id: field.id, label: field.label[lang], type: field.type, required: field.required, included: true, value: "" })), submission: null,
  };
  return { kind: "review", accepted: [] };
}
export function interactionDraft(spec: Interaction, state: InteractionState, lang: InteractionLanguage): InteractionDraft {
  const index = interactionVariantIndex(spec, state.inputs);
  return state.drafts[`${index}:${lang}`] ?? initialInteractionDraft(spec, index, lang);
}
export function updateInteractionDraft(spec: Interaction, state: InteractionState, lang: InteractionLanguage, draft: InteractionDraft): InteractionState {
  const index = interactionVariantIndex(spec, state.inputs);
  if (draft.kind !== spec.kind) return state;
  return { ...state, drafts: { ...state.drafts, [`${index}:${lang}`]: draft } };
}
export function moveEditorField(draft: EditorDraft, fieldId: string, direction: -1 | 1): EditorDraft {
  const index = draft.fields.findIndex(field => field.id === fieldId);
  const next = index + direction;
  if (index < 0 || next < 0 || next >= draft.fields.length) return draft;
  const fields = [...draft.fields];
  [fields[index], fields[next]] = [fields[next], fields[index]];
  return { ...draft, fields };
}
export function editorOutput(draft: EditorDraft) {
  return draft.fields.filter(field => field.included).map(field => `${field.label}\n${field.value}`).join("\n\n");
}
export function updateRecordCell(artifact: RecordsArtifact, draft: RecordsDraft, rowId: string, columnId: string, value: string | number): RecordsDraft {
  const col = artifact.columns.find(item => item.id === columnId);
  if (!col || (col.type === "number" ? value !== "" && (typeof value !== "number" || !Number.isFinite(value)) : col.type !== "select" || !col.options?.some(opt => opt.id === value))) return draft;
  return { ...draft, rows: draft.rows.map(row => row.id === rowId ? { ...row, cells: { ...row.cells, [columnId]: value } } : row) };
}
export function recordCellText(artifact: RecordsArtifact, row: RecordsDraft["rows"][number], columnId: string, lang: InteractionLanguage) {
  const col = artifact.columns.find(item => item.id === columnId);
  const value = row.cells[columnId];
  return col?.type === "select" ? col.options?.find(opt => opt.id === value)?.label[lang] ?? String(value) : String(value);
}
export function visibleInteractionRows(artifact: RecordsArtifact, draft: RecordsDraft, lang: InteractionLanguage) {
  const query = draft.query.trim().toLocaleLowerCase(lang);
  const rows = draft.rows.filter(row => {
    if (!query) return true;
    const evidence = artifact.rows.find(source => source.id === row.id)?.evidence;
    const values = [...artifact.columns.map(col => recordCellText(artifact, row, col.id, lang)), ...(evidence ? [evidence.text[lang], evidence.quote[lang]] : [])];
    return values.some(value => value.toLocaleLowerCase(lang).includes(query));
  });
  if (!draft.sort) return rows;
  const { column: col, direction } = draft.sort;
  return [...rows].sort((a, b) => {
    const left = a.cells[col], right = b.cells[col];
    const result = typeof left === "number" && typeof right === "number" ? left - right : recordCellText(artifact, a, col, lang).localeCompare(recordCellText(artifact, b, col, lang), lang);
    return direction === "asc" ? result : -result;
  });
}
export function selectedInteractionRows(artifact: RecordsArtifact, draft: RecordsDraft, lang: InteractionLanguage) {
  // Search changes what is browsed, never the set explicitly selected to save.
  return visibleInteractionRows(artifact, { ...draft, query: "" }, lang).filter(row => draft.selected.includes(row.id));
}
export function calculateInteractionRecords(artifact: RecordsArtifact, draft: RecordsDraft): number | null {
  const calc = artifact.calculation;
  if (!calc) return null;
  if (calc.op === "count") return draft.rows.filter(row => draft.selected.includes(row.id)).length;
  const relevant = calc.op === "difference" ? draft.rows.filter(row => row.id === calc.left || row.id === calc.right) : draft.rows;
  if (relevant.some(row => typeof row.cells[calc.column] !== "number")) return null;
  const value = (rowId: string) => Number(draft.rows.find(row => row.id === rowId)?.cells[calc.column] ?? 0);
  const result = calc.op === "difference" ? value(calc.left) - value(calc.right) : draft.rows.reduce((total, row) => total + Number(row.cells[calc.column]), 0);
  return Number.isFinite(result) ? result : null;
}
export function mergeInteractionReview(artifact: ReviewArtifact, draft: ReviewDraft, lang: InteractionLanguage) {
  // Apply against original positions from right to left; replacement text cannot accidentally match another patch.
  const patches = artifact.patches.filter(patch => draft.accepted.includes(patch.id)).map(patch => ({ ...patch, at: artifact.base[lang].indexOf(patch.before[lang]) })).sort((a, b) => b.at - a.at);
  return patches.reduce((text, patch) => text.slice(0, patch.at) + patch.after[lang] + text.slice(patch.at + patch.before[lang].length), artifact.base[lang]);
}
export function submitInteractionForm(draft: FormDraft): FormDraft {
  const fields = draft.fields.filter(field => field.included);
  if (!fields.length || fields.some(field => field.required && !field.value.trim() || field.value && field.type === "email" && !/^[^\s@]+@[^\s@]+$/.test(field.value) || field.value && field.type === "number" && !Number.isFinite(Number(field.value)))) return { ...draft, submission: null };
  return { ...draft, submission: fields.map(field => ({ label: field.label, value: field.value })) };
}
export function interactionDisclosure(lang: InteractionLanguage) {
  return lang === "zh" ? "独立本地示例 · 虚构数据 · 未调用产品服务" : "Independent local example · Fictional data · No product service connected";
}
export function serializeInteraction(spec: Interaction, state: InteractionState, lang: InteractionLanguage, productName: string, sources: InteractionSource[]): string[] {
  const index = interactionVariantIndex(spec, state.inputs);
  const draft = interactionDraft(spec, state, lang);
  const facts = [...new Set(selectedInteractionFacts(spec, state.inputs).map(fact => fact[lang]))];
  const lines = [productName, interactionDisclosure(lang), ...spec.inputs.map(control => `${control.label[lang]}: ${control.options.find(opt => opt.id === state.inputs[control.id])!.label[lang]}`), ...facts.map(fact => `${lang === "zh" ? "输入事实" : "Input fact"}: ${fact}`), spec.variants[index].brief[lang], spec.output_label[lang]];
  if (draft.kind === "editor") lines.push(editorOutput(draft));
  if (draft.kind === "records" && spec.kind === "records") {
    const artifact = spec.variants[index].artifact;
    if (draft.query) lines.push(`${lang === "zh" ? "搜索" : "Search"}: ${draft.query}`);
    lines.push(...selectedInteractionRows(artifact, draft, lang).map(row => {
      const evidence = artifact.rows.find(item => item.id === row.id)?.evidence;
      return [artifact.columns.map(col => `${col.label[lang]}: ${recordCellText(artifact, row, col.id, lang)}${col.unit ? ` ${col.unit[lang]}` : ""}`).join(" | "), ...(evidence ? [`${lang === "zh" ? "虚构原文" : "Fictional source text"}: ${evidence.text[lang]}`, `${lang === "zh" ? "引用" : "Quote"}: ${evidence.quote[lang]}`] : [])].join("\n");
    }));
    const calc = artifact.calculation;
    if (calc) {
      const col = calc.op === "count" ? undefined : artifact.columns.find(item => item.id === calc.column);
      lines.push(`${calc.label[lang]}: ${calculateInteractionRecords(artifact, draft) ?? "—"}${col?.unit ? ` ${col.unit[lang]}` : ""}`);
      if (calc.op === "count") lines.push(lang === "zh" ? "数量包含所有已选记录，搜索不改变选择。" : "Count includes all selected records; search does not change selection.");
      else {
        const numbers = (calc.op === "sum" ? draft.rows : [draft.rows.find(row => row.id === calc.left)!, draft.rows.find(row => row.id === calc.right)!]).map(row => String(row.cells[calc.column]));
        lines.push(`${lang === "zh" ? "使用当前值" : "Using current values"}: ${numbers.join(calc.op === "sum" ? " + " : " − ")}`);
      }
    }
  }
  if (draft.kind === "form") lines.push(draft.title, ...draft.fields.filter(field => field.included).map(field => `${field.label}${field.required ? " *" : ""}: ${field.value}`), ...(draft.submission ? [lang === "zh" ? "仅保存在本地的提交结果" : "Local sample submission", ...draft.submission.map(field => `${field.label}: ${field.value}`)] : []));
  if (draft.kind === "review" && spec.kind === "review") lines.push(mergeInteractionReview(spec.variants[index].artifact, draft, lang));
  lines.push(lang === "zh" ? "产品资料（不证明虚构数据或结果）" : "Product sources (not evidence for sample data or results)", ...sources.map(source => `${source.label[lang]}: ${source.url}`));
  return lines;
}
