import { createElement, type ComponentProps } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import fixtures from "../../../../tests/fixtures/demo_interactions.json";
import { LocaleProvider } from "@/components/layout/locale-provider";
import { GeneratedInteraction } from "@/components/demo/generated-interaction";
import {
  InteractionSchema, calculateInteractionRecords, changeInteractionInput, editorOutput, initialInteractionState,
  interactionDraft, interactionVariantIndex, mergeInteractionReview, moveEditorField, selectedInteractionRows, serializeInteraction,
  submitInteractionForm, updateInteractionDraft, updateRecordCell, visibleInteractionRows,
  type EditorDraft, type FormDraft, type Interaction, type RecordsDraft,
} from "@/lib/demo-interaction";

function fixture<K extends Interaction["kind"]>(kind: K) {
  return InteractionSchema.parse(structuredClone(fixtures[kind])) as Extract<Interaction, { kind: K }>;
}
const sources = [{ label: { zh: "官方资料", en: "Official source" }, url: "https://example.com/docs" }];

function factBoundReview() {
  const spec = fixture("review");
  spec.inputs = [{ id: "environment", label: { zh: "环境", en: "Environment" }, options: ["staging", "sandbox"].map(env => ({ id: env, label: { zh: env, en: env }, facts: [{ zh: env, en: env }] })) }];
  spec.variants = ["staging", "sandbox"].map(env => ({
    when: { environment: env }, brief: { zh: "检查当前环境的修改", en: "Review edits for the selected environment" },
    artifact: {
      base: { zh: `Environment: ${env}\nAudit: off\nLimit: 10`, en: `Environment: ${env}\nAudit: off\nLimit: 10` },
      patches: [
        { id: "audit", label: { zh: "开启审计", en: "Enable audit" }, before: { zh: "Audit: off", en: "Audit: off" }, after: { zh: "Audit: on", en: "Audit: on" } },
        { id: "limit", label: { zh: "调整上限", en: "Adjust limit" }, before: { zh: "Limit: 10", en: "Limit: 10" }, after: { zh: "Limit: 20", en: "Limit: 20" } },
      ],
    },
  }));
  return spec;
}

describe("shared generated interaction contract", () => {
  it.each(["editor", "records", "form", "review"] as const)("accepts the unchanged Python/TypeScript %s golden", kind => {
    expect(InteractionSchema.parse(fixtures[kind])).toEqual(fixtures[kind]);
  });

  it("requires complete two-input coverage, without accepting an unreachable fifth variant", () => {
    const spec = fixture("editor");
    spec.inputs.push({ id: "tone", label: { zh: "语气", en: "Tone" }, options: [{ id: "short", label: { zh: "简短", en: "Short" } }, { id: "long", label: { zh: "展开", en: "Expanded" } }] });
    spec.variants = spec.variants.flatMap(variant => ["short", "long"].map(tone => ({ ...structuredClone(variant), when: { ...variant.when, tone }, artifact: { fields: variant.artifact.fields.map(field => ({ ...field, value: { zh: `${field.value.zh} ${tone}`, en: `${field.value.en} ${tone}` } })) } })));
    expect(InteractionSchema.safeParse(spec).success).toBe(true);
    const missing = structuredClone(spec); missing.variants.pop();
    expect(InteractionSchema.safeParse(missing).success).toBe(false);
    spec.variants.push(structuredClone(spec.variants[0]));
    expect(InteractionSchema.safeParse(spec).success).toBe(false);
  });

  it("rejects duplicate options, missing/extra when keys, and unknown executable fields", () => {
    const duplicate = fixture("editor"); duplicate.inputs[0].options[1].id = duplicate.inputs[0].options[0].id;
    const missing = fixture("editor"); missing.variants[0].when = {};
    const extra = fixture("editor"); extra.variants[0].when.other = "value";
    expect([duplicate, missing, extra, { ...fixture("form"), onSubmit: "fetch('/api')" }].map(value => InteractionSchema.safeParse(value).success)).toEqual([false, false, false, false]);
  });

  it("rejects an identifier ending in a newline, matching Python's exact identifier boundary", () => {
    const spec = fixture("editor"); spec.variants[0].artifact.fields[0].id = "headline\n";
    expect(InteractionSchema.safeParse(spec).success).toBe(false);
  });

  it("does not count changed IDs, labels, or briefs as a changed artifact", () => {
    const spec = fixture("editor");
    spec.variants[1].artifact = structuredClone(spec.variants[0].artifact);
    spec.variants[1].artifact.fields.forEach(field => { field.id += "_new"; field.label = { zh: "新名字", en: "New name" }; });
    expect(InteractionSchema.safeParse(spec).success).toBe(false);
  });

  it("requires an actual consequence in both languages", () => {
    const spec = fixture("editor");
    spec.variants[1].artifact.fields.forEach((field, index) => { field.value.en = spec.variants[0].artifact.fields[index].value.en; });
    expect(InteractionSchema.safeParse(spec).success).toBe(false);
  });

  it("does not count hidden evidence alone as a visible records consequence", () => {
    const spec = fixture("records");
    spec.inputs = [{ id: "audience", label: { zh: "受众", en: "Audience" }, options: [{ id: "a", label: { zh: "创业者", en: "Founders" } }, { id: "b", label: { zh: "学生", en: "Students" } }] }];
    spec.variants[0].when = { audience: "a" };
    spec.variants.push({ ...structuredClone(spec.variants[0]), when: { audience: "b" } });
    spec.variants[1].artifact.rows[0].evidence = { text: { zh: "学生希望更容易找到价格页。", en: "Students want to find pricing more easily." }, quote: { zh: "找到价格页", en: "find pricing" } };
    expect(InteractionSchema.safeParse(spec).success).toBe(false);
    spec.variants[1].artifact.rows[0].cells.title = { zh: "整理学生价格信息", en: "Organize student pricing" };
    expect(InteractionSchema.safeParse(spec).success).toBe(true);
  });

  it("binds selected facts to substantive values, rejecting cross-product leakage and brief-only mentions", () => {
    const missing = fixture("editor");
    missing.variants[0].artifact.fields[1].value.en = "Daily speaking practice for travelers";
    missing.variants[0].brief.en += " Speaking Partner";
    expect(InteractionSchema.safeParse(missing).success).toBe(false);
    const leaked = fixture("editor");
    leaked.variants[0].artifact.fields[1].value.en += " Also enjoy a green-tea break.";
    expect(InteractionSchema.safeParse(leaked).success).toBe(false);
    const split = fixture("editor");
    split.variants[0].artifact.fields[0].value.en = "Speaking ";
    split.variants[0].artifact.fields[1].value.en = "Partner offers daily speaking practice.";
    expect(InteractionSchema.safeParse(split).success).toBe(false);
  });

  it("allows facts shared by options, without using decorative labels as evidence", () => {
    const spec = fixture("editor");
    spec.inputs[0].options.forEach(opt => opt.facts!.push({ zh: "通勤场景", en: "commuting scenario" }));
    spec.variants.forEach(variant => {
      variant.artifact.fields[1].value.zh += " 适合通勤场景。";
      variant.artifact.fields[1].value.en += " Use in a commuting scenario.";
    });
    expect(InteractionSchema.safeParse(spec).success).toBe(true);
    spec.variants[0].artifact.fields[1].value.en = spec.variants[0].artifact.fields[1].value.en.replace("Speaking Partner", "This app");
    spec.variants[0].artifact.fields[1].label.en = "Speaking Partner";
    expect(InteractionSchema.safeParse(spec).success).toBe(false);
  });

  it("requires fact-bound identity options in a two-input editor, but forbids facts on record status options", () => {
    const spec = fixture("editor");
    spec.inputs[0].options.forEach(opt => { delete opt.facts; });
    spec.inputs.push({ id: "tone", label: { zh: "语气", en: "Tone" }, options: [{ id: "a", label: { zh: "甲", en: "A" } }, { id: "b", label: { zh: "乙", en: "B" } }] });
    spec.variants = spec.variants.flatMap(variant => ["a", "b"].map(tone => ({ ...structuredClone(variant), when: { ...variant.when, tone }, artifact: { fields: variant.artifact.fields.map(field => ({ ...field, value: { zh: `${field.value.zh} ${tone}`, en: `${field.value.en} ${tone}` } })) } })));
    expect(InteractionSchema.safeParse(spec).success).toBe(false);
    const records = fixture("records");
    Object.assign(records.variants[0].artifact.columns[2].options![0], { facts: [{ zh: "待处理", en: "To do" }] });
    expect(InteractionSchema.safeParse(records).success).toBe(false);
  });

  it("requires review facts in the base and in every reachable patch combination", () => {
    expect(InteractionSchema.safeParse(factBoundReview()).success).toBe(true);
    const deleted = factBoundReview();
    for (const variant of deleted.variants) {
      const env = variant.when.environment;
      variant.artifact.patches[0].before = { zh: `Environment: ${env}`, en: `Environment: ${env}` };
      variant.artifact.patches[0].after = { zh: "Environment: default", en: "Environment: default" };
    }
    expect(InteractionSchema.safeParse(deleted).success).toBe(false);
    const onlyAfter = factBoundReview();
    for (const variant of onlyAfter.variants) {
      const env = variant.when.environment;
      variant.artifact.base = { zh: "Environment: default\nAudit: off\nLimit: 10", en: "Environment: default\nAudit: off\nLimit: 10" };
      variant.artifact.patches[0].before = { zh: "Environment: default", en: "Environment: default" };
      variant.artifact.patches[0].after = { zh: `Environment: ${env}`, en: `Environment: ${env}` };
    }
    expect(InteractionSchema.safeParse(onlyAfter).success).toBe(false);
  });

  it("rejects a selected fact lost only when two individually safe patches are combined", () => {
    const spec = factBoundReview();
    for (const variant of spec.variants) {
      const env = variant.when.environment;
      variant.artifact.base = { zh: `Primary: ${env}\nBackup: ${env}`, en: `Primary: ${env}\nBackup: ${env}` };
      variant.artifact.patches = variant.artifact.patches.map((patch, index) => {
        const key = index === 0 ? "Primary" : "Backup";
        return { ...patch, before: { zh: `${key}: ${env}`, en: `${key}: ${env}` }, after: { zh: `${key}: default`, en: `${key}: default` } };
      });
      for (const patch of variant.artifact.patches) expect(mergeInteractionReview(variant.artifact, { kind: "review", accepted: [patch.id] }, "en")).toContain(env);
    }
    expect(InteractionSchema.safeParse(spec).success).toBe(false);
  });

  it("rejects an unselected fact composed across two replacement boundaries", () => {
    const spec = factBoundReview();
    for (const variant of spec.variants) {
      const env = variant.when.environment;
      const parts = env === "staging" ? ["sand", "box"] : ["stag", "ing"];
      variant.artifact.base = { zh: `Environment: ${env}\nTarget: left right`, en: `Environment: ${env}\nTarget: left right` };
      variant.artifact.patches = variant.artifact.patches.map((patch, index) => ({ ...patch, before: { zh: index === 0 ? "left " : "right", en: index === 0 ? "left " : "right" }, after: { zh: parts[index], en: parts[index] } }));
      for (const patch of variant.artifact.patches) expect(mergeInteractionReview(variant.artifact, { kind: "review", accepted: [patch.id] }, "en")).not.toContain(parts.join(""));
    }
    expect(InteractionSchema.safeParse(spec).success).toBe(false);
  });

  it("checks the last of all sixteen states for a four-patch review", () => {
    const spec = factBoundReview();
    for (const variant of spec.variants) {
      const env = variant.when.environment;
      const content = Array.from({ length: 4 }, (_, index) => `Slot ${index}: ${env}`).join("\n");
      variant.artifact.base = { zh: content, en: content };
      variant.artifact.patches = Array.from({ length: 4 }, (_, index) => ({ id: `slot_${index}`, label: { zh: `修改 ${index}`, en: `Edit ${index}` }, before: { zh: `Slot ${index}: ${env}`, en: `Slot ${index}: ${env}` }, after: { zh: `Slot ${index}: default`, en: `Slot ${index}: default` } }));
      for (let mask = 0; mask < 15; mask++) {
        const accepted = variant.artifact.patches.filter((_, index) => mask & (1 << index)).map(patch => patch.id);
        expect(mergeInteractionReview(variant.artifact, { kind: "review", accepted }, "en")).toContain(env);
      }
    }
    expect(InteractionSchema.safeParse(spec).success).toBe(false);
  });

  it("rejects a form variant that merely renames the same fields", () => {
    const spec = fixture("form");
    spec.inputs = [{ id: "mode", label: { zh: "模式", en: "Mode" }, options: [{ id: "a", label: { zh: "甲", en: "A" } }, { id: "b", label: { zh: "乙", en: "B" } }] }];
    spec.variants[0].when = { mode: "a" };
    spec.variants.push({ ...structuredClone(spec.variants[0]), when: { mode: "b" } });
    spec.variants[1].artifact.title = { zh: "不同的表单", en: "Different form" };
    expect(InteractionSchema.safeParse(spec).success).toBe(false);
    spec.variants[1].artifact.fields[1].required = true;
    expect(InteractionSchema.safeParse(spec).success).toBe(true);
  });

  it("rejects unknown/missing cells, string numbers, invalid groups, absent units and unmatched quotes", () => {
    const values: unknown[] = [];
    const missing = fixture("records"); delete missing.variants[0].artifact.rows[0].cells.hours; values.push(missing);
    const extra = fixture("records"); extra.variants[0].artifact.rows[0].cells.hidden = 2; values.push(extra);
    const numeric = fixture("records"); numeric.variants[0].artifact.rows[0].cells.hours = "6"; values.push(numeric);
    const group = fixture("records"); group.variants[0].artifact.group_by = "hours"; values.push(group);
    const unit = fixture("records"); delete unit.variants[0].artifact.columns[1].unit; values.push(unit);
    const quote = fixture("records"); quote.variants[0].artifact.rows[0].evidence!.quote.en = "not in the source"; values.push(quote);
    const boolean = fixture("records"); Object.assign(boolean.variants[0].artifact.rows[0].cells, { hours: true }); values.push(boolean);
    const infinity = fixture("records"); infinity.variants[0].artifact.rows[0].cells.hours = Infinity; values.push(infinity);
    expect(values.map(value => InteractionSchema.safeParse(value).success)).toEqual(values.map(() => false));
  });

  it("checks calculation row and column references", () => {
    const spec = fixture("records");
    const calc = spec.variants[0].artifact.calculation;
    if (calc?.op !== "difference") throw new Error("Expected difference golden");
    calc.right = calc.left;
    expect(InteractionSchema.safeParse(spec).success).toBe(false);
    calc.right = "copy"; calc.column = "title";
    expect(InteractionSchema.safeParse(spec).success).toBe(false);
  });

  it("rejects repeated, overlapping and no-op patches", () => {
    const repeated = fixture("review"); repeated.variants[0].artifact.base.en += "\nlimit = 10";
    const overlap = fixture("review"); overlap.variants[0].artifact.patches[1].before = { zh: "value.strip", en: "value.strip" };
    const noop = fixture("review"); noop.variants[0].artifact.patches[1].after = noop.variants[0].artifact.patches[1].before;
    expect([repeated, overlap, noop].map(value => InteractionSchema.safeParse(value).success)).toEqual([false, false, false]);
  });

  it("preserves code whitespace and inert generics but rejects markup, links and fake execution", () => {
    const spec = fixture("review");
    spec.variants[0].artifact.base.en = `  const values: Array<string> = [];\nconst inside = x < y && y > 0;\n${spec.variants[0].artifact.base.en}\n`;
    expect(InteractionSchema.parse(spec).variants[0].artifact).toEqual(spec.variants[0].artifact);
    for (const unsafe of ["<script>alert(1)</script>", "https://example.com", "agent deployed", "accuracy: 99", "视频已生成"]) {
      const rejected = fixture("editor"); rejected.variants[0].artifact.fields[0].value.en = unsafe;
      expect(InteractionSchema.safeParse(rejected).success).toBe(false);
    }
  });
});

describe("observable local consequences", () => {
  it("keeps independent variant and locale drafts and resets only on an explicit reset", () => {
    const spec = fixture("editor");
    let state = initialInteractionState(spec);
    const zh = interactionDraft(spec, state, "zh") as EditorDraft;
    zh.fields[0].value = "我编辑的标题";
    state = updateInteractionDraft(spec, state, "zh", zh);
    expect((interactionDraft(spec, state, "en") as EditorDraft).fields[0].value).toBe(fixtures.editor.variants[0].artifact.fields[0].value.en);
    const en = interactionDraft(spec, state, "en") as EditorDraft; en.fields[0].value = "My edited title";
    state = updateInteractionDraft(spec, state, "en", en);
    state = changeInteractionInput(spec, state, "product", "tea");
    expect(interactionVariantIndex(spec, state.inputs)).toBe(1);
    expect((interactionDraft(spec, state, "zh") as EditorDraft).fields[0].value).toBe(fixtures.editor.variants[1].artifact.fields[0].value.zh);
    state = changeInteractionInput(spec, state, "product", "app");
    expect((interactionDraft(spec, state, "zh") as EditorDraft).fields[0].value).toBe("我编辑的标题");
    expect((interactionDraft(spec, state, "en") as EditorDraft).fields[0].value).toBe("My edited title");
    expect(changeInteractionInput(spec, state, "product", "unknown")).toBe(state);
    expect((interactionDraft(spec, initialInteractionState(spec), "zh") as EditorDraft).fields[0].value).toBe(fixtures.editor.variants[0].artifact.fields[0].value.zh);
  });

  it("edits, reorders and excludes editor fields in the actual output", () => {
    const spec = fixture("editor");
    const initial = interactionDraft(spec, initialInteractionState(spec), "en") as EditorDraft;
    const moved = moveEditorField(initial, "body", -1);
    moved.fields = moved.fields.map(field => field.id === "headline" ? { ...field, included: false } : { ...field, value: "A completely edited body" });
    expect(editorOutput(moved)).toBe("Body\nA completely edited body");
    expect(initial.fields[0].id).toBe("headline");
    expect(moveEditorField(initial, "headline", -1)).toBe(initial);
  });

  it("numeric edits change differences, sums and blank-value results, independent of search", () => {
    const spec = fixture("records"), artifact = spec.variants[0].artifact;
    let draft = interactionDraft(spec, initialInteractionState(spec), "en") as RecordsDraft;
    expect(calculateInteractionRecords(artifact, draft)).toBe(3.5);
    draft = updateRecordCell(artifact, draft, "navigation", "hours", 9);
    expect(calculateInteractionRecords(artifact, draft)).toBe(6.5);
    expect(calculateInteractionRecords(artifact, { ...draft, query: "no match", selected: [] })).toBe(6.5);
    const sum = { ...artifact, calculation: { op: "sum" as const, column: "hours", label: { zh: "总和", en: "Sum" } } };
    expect(calculateInteractionRecords(sum, draft)).toBe(11.5);
    expect(calculateInteractionRecords(sum, updateRecordCell(artifact, draft, "navigation", "hours", ""))).toBeNull();
    expect(updateRecordCell(artifact, draft, "navigation", "hours", Infinity)).toBe(draft);
    expect(updateRecordCell(artifact, draft, "navigation", "title", "injected text")).toBe(draft);
  });

  it("handles held-out renamed IDs and reordered records without changing the calculation semantics", () => {
    const spec = fixture("records"), artifact = spec.variants[0].artifact;
    const rename = (value: string) => `heldout_${value}`;
    artifact.columns = artifact.columns.map(col => ({ ...col, id: rename(col.id), ...(col.options ? { options: col.options.map(opt => ({ ...opt, id: rename(opt.id) })) } : {}) })).reverse();
    artifact.rows = artifact.rows.map(row => ({ ...row, id: rename(row.id), cells: Object.fromEntries(Object.entries(row.cells).map(([key, value]) => [rename(key), key === "status" ? rename(String(value)) : value])) })).reverse();
    artifact.group_by = rename(artifact.group_by!);
    const calc = artifact.calculation;
    if (calc?.op !== "difference") throw new Error("Expected difference golden");
    calc.column = rename(calc.column); calc.left = rename(calc.left); calc.right = rename(calc.right);
    expect(InteractionSchema.safeParse(spec).success).toBe(true);
    const draft = interactionDraft(spec, initialInteractionState(spec), "en") as RecordsDraft;
    expect(calculateInteractionRecords(artifact, draft)).toBe(3.5);
    expect(calculateInteractionRecords(artifact, updateRecordCell(artifact, draft, "heldout_copy", "heldout_hours", 5))).toBe(1);
    expect(visibleInteractionRows(artifact, { ...draft, query: "pricing" }, "en")).toHaveLength(1);
    expect(visibleInteractionRows(artifact, { ...draft, query: "navigation" }, "en")).toHaveLength(1);
  });

  it("status edits move records, and sorting and selection change the saved output", () => {
    const spec = fixture("records"), artifact = spec.variants[0].artifact;
    let draft = interactionDraft(spec, initialInteractionState(spec), "en") as RecordsDraft;
    draft = updateRecordCell(artifact, draft, "navigation", "status", "ready");
    expect(draft.rows.filter(row => row.cells.status === "ready")).toHaveLength(2);
    expect(visibleInteractionRows(artifact, { ...draft, query: "for review" }, "en")).toHaveLength(2);
    expect(visibleInteractionRows(artifact, { ...draft, sort: { column: "hours", direction: "asc" } }, "en").map(row => row.id)).toEqual(["copy", "navigation"]);
    const count = { ...artifact, calculation: { op: "count" as const, label: { zh: "数量", en: "Count" } } };
    expect(calculateInteractionRecords(count, { ...draft, selected: ["copy"], query: "no match" })).toBe(1);
    const state = updateInteractionDraft(spec, initialInteractionState(spec), "en", { ...draft, selected: ["copy"] });
    const saved = serializeInteraction(spec, state, "en", "Held-out product", sources).join("\n");
    expect(saved).toContain("Revise button copy");
    expect(saved).not.toContain("Request: Organize navigation");
  });

  it("finds source-only terms from the real provider regression in the current locale", () => {
    const spec = fixture("records"), artifact = spec.variants[0].artifact;
    // Unchanged passage from runs/20261112T084722809080Z/exa.json: neither
    // sparse nor 稀疏 appears in that record's title or relevance cells.
    artifact.rows[0].evidence = {
      text: { zh: "多头注意力通过并行计算不同子空间的注意力权重。研究表明稀疏模式可降低计算开销同时保持性能。在长序列任务中，局部窗口注意力是实用的优化方向。", en: "Multi-head attention computes attention weights in different subspaces in parallel. Research shows sparse patterns reduce computational cost while maintaining performance. Local window attention is a practical optimization for long-sequence tasks." },
      quote: { zh: "稀疏模式可降低计算开销同时保持性能", en: "sparse patterns reduce computational cost while maintaining performance" },
    };
    const state = initialInteractionState(spec);
    const en = interactionDraft(spec, state, "en") as RecordsDraft;
    const zh = interactionDraft(spec, state, "zh") as RecordsDraft;
    expect(visibleInteractionRows(artifact, { ...en, query: "  SPARSE  " }, "en").map(row => row.id)).toEqual(["navigation"]);
    expect(visibleInteractionRows(artifact, { ...zh, query: "稀疏" }, "zh").map(row => row.id)).toEqual(["navigation"]);
    expect(visibleInteractionRows(artifact, { ...en, query: "Local window" }, "en")).toHaveLength(1);
    expect(visibleInteractionRows(artifact, { ...zh, query: "局部窗口" }, "zh")).toHaveLength(1);
    expect(visibleInteractionRows(artifact, { ...zh, query: "sparse" }, "zh")).toHaveLength(0);
    expect(visibleInteractionRows(artifact, { ...en, query: "稀疏" }, "en")).toHaveLength(0);
    expect(visibleInteractionRows(artifact, { ...en, query: "absent research term" }, "en")).toHaveLength(0);
  });

  it("keeps selected summary, count and export consistent when search hides every selected row", () => {
    const spec = fixture("records"), artifact = spec.variants[0].artifact;
    artifact.calculation = { op: "count", label: { zh: "已选记录数", en: "Selected records" } };
    const draft = { ...interactionDraft(spec, initialInteractionState(spec), "en") as RecordsDraft, query: "no matching source", sort: { column: "hours", direction: "asc" as const } };
    expect(visibleInteractionRows(artifact, draft, "en")).toHaveLength(0);
    expect(selectedInteractionRows(artifact, draft, "en").map(row => row.id)).toEqual(["copy", "navigation"]);
    expect(calculateInteractionRecords(artifact, draft)).toBe(2);
    const state = updateInteractionDraft(spec, initialInteractionState(spec), "en", draft);
    const saved = serializeInteraction(spec, state, "en", "Unseen product", sources).join("\n");
    expect(saved).toContain("Request: Organize navigation");
    expect(saved).toContain("Request: Revise button copy");
    expect(saved.indexOf("Request: Revise button copy")).toBeLessThan(saved.indexOf("Request: Organize navigation"));
    expect(saved).toContain("Selected records: 2");
    const removed = { ...draft, selected: ["navigation"] };
    expect(selectedInteractionRows(artifact, removed, "en").map(row => row.id)).toEqual(["navigation"]);
    expect(calculateInteractionRecords(artifact, removed)).toBe(1);
    expect(serializeInteraction(spec, updateInteractionDraft(spec, state, "en", removed), "en", "Unseen product", sources).join("\n")).not.toContain("Request: Revise button copy");
  });

  it("accept/reject affects only its original text range, even if replacement mentions another patch", () => {
    const spec = fixture("review"), artifact = spec.variants[0].artifact;
    expect(mergeInteractionReview(artifact, { kind: "review", accepted: [] }, "en")).toBe(artifact.base.en);
    expect(mergeInteractionReview(artifact, { kind: "review", accepted: ["limit"] }, "en")).toContain("limit = 20");
    expect(mergeInteractionReview(artifact, { kind: "review", accepted: ["limit"] }, "en")).not.toContain(".lower()");
    artifact.patches[0].after.en = "value.strip()\nlimit = 10";
    expect(mergeInteractionReview(artifact, { kind: "review", accepted: ["limit", "lowercase"] }, "en")).toBe("def normalize(value):\n    return value.strip()\nlimit = 10\n\nlimit = 20");
  });

  it("form inclusion, required state and values determine the local submission", () => {
    const spec = fixture("form");
    let draft = interactionDraft(spec, initialInteractionState(spec), "en") as FormDraft;
    expect(submitInteractionForm(draft).submission).toBeNull();
    draft = { ...draft, fields: draft.fields.map(field => ({ ...field, value: field.id === "name" ? "Sample visitor" : "invalid-email" })) };
    expect(submitInteractionForm(draft).submission).toBeNull();
    draft = { ...draft, fields: draft.fields.map(field => field.id === "email" ? { ...field, included: false } : field) };
    expect(submitInteractionForm(draft).submission).toEqual([{ label: "Name", value: "Sample visitor" }]);
    draft = { ...draft, fields: draft.fields.map(field => ({ ...field, value: "", required: false })) };
    expect(submitInteractionForm(draft).submission).toEqual([{ label: "Name", value: "" }]);
    expect(submitInteractionForm({ ...draft, fields: draft.fields.map(field => ({ ...field, included: false })) }).submission).toBeNull();
  });

  it("saved text contains selected context, edited artifact, disclosure and sources", () => {
    const spec = fixture("editor");
    let state = changeInteractionInput(spec, initialInteractionState(spec), "product", "tea");
    const draft = interactionDraft(spec, state, "en") as EditorDraft; draft.fields[0].value = "My tea draft";
    state = updateInteractionDraft(spec, state, "en", draft);
    const saved = serializeInteraction(spec, state, "en", "Unseen product name", sources).join("\n");
    expect(saved).toContain("Product: Green tea");
    expect(saved).toContain("Input fact: green-tea");
    expect(saved).toContain("My tea draft");
    expect(saved).toContain("Fictional data");
    expect(saved).toContain("https://example.com/docs");
    expect(saved).not.toContain(fixtures.editor.variants[0].artifact.fields[0].value.en);
  });
});

describe("static renderer coverage (not browser or human comprehension)", () => {
  it.each(["editor", "records", "form", "review"] as const)("renders %s without product-ID routing in both languages", kind => {
    for (const locale of ["zh-CN", "en-US"] as const) {
      const html = renderToStaticMarkup(createElement(LocaleProvider, { initialLocale: locale } as ComponentProps<typeof LocaleProvider>, createElement(GeneratedInteraction, { interaction: fixture(kind), productName: "Renamed held-out product", sources, embedded: true })));
      expect(html).toContain(`data-interaction-kind="${kind}"`);
      expect(html).toContain(locale === "en-US" ? "Fictional data" : "虚构数据");
      expect(html).toContain("https://example.com/docs");
      expect(html).not.toContain("<script");
      if (kind === "records") expect(html).toContain(locale === "en-US" ? "<mark>cannot find pricing</mark>" : "<mark>找不到价格页</mark>");
      if (kind === "form") {
        expect(html).toContain('type="email"'); expect(html).toContain("required=");
        expect(html).toContain(locale === "en-US" ? "<h4>Field configuration</h4>" : "<h4>字段配置</h4>");
        expect(html).not.toContain(`<h4>${fixtures.form.input_label[locale === "en-US" ? "en" : "zh"]}</h4>`);
      }
      if (kind === "review") expect(html).toContain(locale === "en-US" ? "no code or tests executed" : "未执行代码或测试");
    }
  });
});
