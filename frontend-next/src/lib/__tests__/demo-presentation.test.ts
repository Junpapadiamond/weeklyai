import { readdirSync, readFileSync } from "node:fs";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import { ExperienceArtifact } from "../../components/demo/experience-artifact";
import { availableExperienceOptions, ExperienceArtifactSchema, ExperienceSchema, type Experience } from "../demo-experience";
import { artifactInputParts, defaultExperienceChoices, experienceArtifact, initialExperienceIndex, selectExperienceChoice } from "../demo-presentation";

const copy = (text: string) => ({ zh: text, en: text });
const artifact = () => ({
  kind: "excerpt" as const,
  input_label: copy("Example passage"), output_label: copy("Possible interpretation"),
  input: { zh: "我想先了解目标，再选择伙伴。", en: "I want to see the goals before choosing a buddy." },
  output: copy("A goals filter is one hypothesis to test."),
  emphasis: { zh: "先了解目标", en: "see the goals" },
});
const option = (id: string, when?: { step_id: string; option_id: string }) => ({
  id, label: copy(`Choice ${id}`), output: copy(`Complete prepared result ${id}`), ...(when ? { when } : {}),
});
const section = (id: string, options = [option("0"), option("1")]) => ({
  id, widget: "choice", title: copy(id), instruction: copy("Inspect an example."), example_data: true, options,
});
function fixture(): Experience {
  return ExperienceSchema.parse({
    version: 2, tier: "workflow", confidence: "illustrative", headline: copy("A product example"),
    scenario: copy("A concrete input becomes a prepared output."), takeaway: copy("Try the vendor product."),
    steps: [section("root"), section("dependent", [option("0"), option("1"),
      option("2", { step_id: "root", option_id: "0" }), option("3", { step_id: "root", option_id: "1" })]),
    section("chained", ["0", "1", "2", "3"].map(id => option(id, { step_id: "dependent", option_id: id }))),
    section("independent")],
    sources: [{ label: copy("Product source"), url: "https://example.com" }],
  });
}

const directory = "../backend/data/demos";
const cached = readdirSync(directory).filter(file => file.endsWith(".json"))
  .map(file => JSON.parse(readFileSync(`${directory}/${file}`, "utf8")));
const profiles = ["autentic", "higgsfield"].map(name => {
  const raw = JSON.parse(readFileSync(`../backend/data/demo_profiles/${name}.json`, "utf8"));
  return { ...raw, steps: raw.steps.map((step: { options: object[] }) => ({ ...step, example_data: true,
    options: step.options.map((value, index) => ({ ...value, id: String(index) })),
  })) };
});

describe("prepared demo presentation compatibility", () => {
  it("presents every committed entry and both curated profiles without generation or cache mutation", () => {
    expect(cached.length).toBeGreaterThanOrEqual(63);
    const fetcher = vi.fn(() => { throw new Error("Presentation must not fetch"); });
    vi.stubGlobal("fetch", fetcher);
    try {
      for (const raw of [...cached.map(entry => entry.spec), ...profiles]) {
        const original = JSON.stringify(raw);
        const spec = ExperienceSchema.parse(raw);
        const choices = defaultExperienceChoices(spec);
        for (const step of spec.steps) {
          const selected = availableExperienceOptions(step, choices).find(item => item.id === choices[step.id]);
          expect(selected).toBeDefined();
          const view = experienceArtifact(spec, step, selected);
          expect(view.input.en.length).toBeGreaterThan(0);
          expect(view.output.zh.length).toBeGreaterThan(0);
          if (!selected?.artifact) expect(view.output).toEqual(selected?.output);
        }
        expect(initialExperienceIndex(spec)).toBeLessThan(spec.steps.length);
        expect(JSON.stringify(raw)).toBe(original);
      }
      expect(fetcher).not.toHaveBeenCalled();
    } finally { vi.unstubAllGlobals(); }
  });

  it("keeps a long legacy output whole, with no invented media or structured evidence", () => {
    const spec = fixture();
    const selected = { ...spec.steps[0].options[0], output: copy("Full legacy sentence.\n".repeat(25)) };
    const view = experienceArtifact(spec, spec.steps[0], selected);
    expect(view.kind).toBe("text");
    expect(view.input).toEqual(selected.label);
    expect(view.output).toEqual(selected.output);
    expect(view).not.toHaveProperty("items");
    expect(view).not.toHaveProperty("emphasis");
  });

  it("allows a single useful example and honors an explicit focus before artifact or app defaults", () => {
    const spec = fixture();
    expect(initialExperienceIndex(spec)).toBe(0);
    spec.steps[2].options[0].artifact = artifact();
    expect(initialExperienceIndex(spec)).toBe(2);
    spec.steps[1] = { ...spec.steps[1], widget: "app", app_kind: "tasks" };
    expect(initialExperienceIndex(spec)).toBe(1);
    spec.focus_step_id = "independent";
    expect(initialExperienceIndex(spec)).toBe(3);
    expect(ExperienceSchema.safeParse({ ...spec, focus_step_id: "missing" }).success).toBe(false);
    const single = { ...fixture(), steps: [fixture().steps[0]] };
    expect(ExperienceSchema.parse(single).steps).toHaveLength(1);
    expect(ExperienceSchema.safeParse({ ...single, steps: [] }).success).toBe(false);
  });
});

describe("prepared path selection", () => {
  it("resolves defaults in order and skips an unavailable first option", () => {
    const spec = fixture();
    spec.steps[1].options = [spec.steps[1].options[3], spec.steps[1].options[2], spec.steps[1].options[0]];
    const choices = defaultExperienceChoices(spec);
    expect(choices).toEqual({ root: "0", dependent: "2", chained: "2", independent: "0" });
  });

  it("resets the changed dependency and its chain while preserving independent edits", () => {
    const spec = fixture();
    const choices = { root: "0", dependent: "2", chained: "2", independent: "1" };
    const next = selectExperienceChoice(spec, choices, "root", "1");
    expect(next).toEqual({ root: "1", dependent: "0", chained: "0", independent: "1" });
    expect(choices).toEqual({ root: "0", dependent: "2", chained: "2", independent: "1" });
    for (const step of spec.steps) expect(availableExperienceOptions(step, next).some(item => item.id === next[step.id])).toBe(true);
  });

  it("resets a still-available selection when its section's context changed", () => {
    const spec = fixture();
    const choices = { root: "0", dependent: "1", chained: "1", independent: "1" };
    expect(selectExperienceChoice(spec, choices, "root", "1"))
      .toEqual({ root: "1", dependent: "0", chained: "0", independent: "1" });
  });

  it("rejects impossible selections and leaves a repeated choice intact", () => {
    const spec = fixture();
    const choices = defaultExperienceChoices(spec);
    expect(selectExperienceChoice(spec, choices, "root", "0")).toBe(choices);
    expect(selectExperienceChoice(spec, choices, "dependent", "3")).toBe(choices);
    expect(selectExperienceChoice(spec, choices, "missing", "0")).toBe(choices);
    expect(selectExperienceChoice(spec, choices, "root", "missing")).toBe(choices);
  });

  it("repairs a stale branch even when the chosen input is unchanged", () => {
    const spec = fixture();
    const stale = { root: "0", dependent: "3", chained: "3", independent: "1" };
    expect(selectExperienceChoice(spec, stale, "root", "0"))
      .toEqual({ root: "0", dependent: "0", chained: "0", independent: "1" });
  });

  it("keeps all Autentic branches reachable without retaining an impossible insight", () => {
    const spec = ExperienceSchema.parse(profiles[0]);
    let choices = defaultExperienceChoices(spec);
    choices = selectExperienceChoice(spec, choices, "input", "1");
    expect(["2", "3"]).toContain(choices.inspection);
    expect(["2", "3"]).toContain(choices.output);
    choices = selectExperienceChoice(spec, choices, "input", "0");
    expect(["0", "1"]).toContain(choices.inspection);
    expect(["0", "1"]).toContain(choices.output);
  });
});

describe("artifact contract and safe highlighting", () => {
  it("accepts each supported kind and strips unrecognized executable or media fields", () => {
    for (const kind of ["excerpt", "sequence", "comparison", "list", "text"] as const) {
      const result = ExperienceArtifactSchema.parse({ ...artifact(), kind, script: "alert(1)", url: "https://example.com/image.png" });
      expect(result.kind).toBe(kind);
      expect(result).not.toHaveProperty("script");
      expect(result).not.toHaveProperty("url");
    }
    expect(ExperienceArtifactSchema.safeParse({ ...artifact(), kind: "iframe" }).success).toBe(false);
    const spec = fixture();
    expect(ExperienceSchema.safeParse({ ...spec, steps: [{ ...spec.steps[0], options: [{ ...spec.steps[0].options[0], artifact: { ...artifact(), kind: "image" } }] }] }).success).toBe(false);
  });

  it("bounds every supplied artifact field and permits items only on sequences and lists", () => {
    const items = [{ label: copy("First"), detail: copy("An existing prepared detail.") }, { label: copy("Second"), detail: copy("Another prepared detail.") }];
    for (const kind of ["sequence", "list"] as const) expect(ExperienceArtifactSchema.parse({ ...artifact(), kind, items }).items).toHaveLength(2);
    expect(ExperienceArtifactSchema.safeParse({ ...artifact(), items }).success).toBe(false);
    expect(ExperienceArtifactSchema.safeParse({ ...artifact(), kind: "list", items: items.slice(0, 1) }).success).toBe(false);
    expect(ExperienceArtifactSchema.safeParse({ ...artifact(), kind: "sequence", items: [...items, ...items, items[0]] }).success).toBe(false);
    for (const [field, length] of [["input_label", 41], ["output_label", 41], ["input", 221], ["output", 221], ["emphasis", 101]] as const)
      expect(ExperienceArtifactSchema.safeParse({ ...artifact(), [field]: copy("x".repeat(length)) }).success).toBe(false);
    expect(ExperienceArtifactSchema.safeParse({ ...artifact(), kind: "list", items: [{ ...items[0], label: copy("x".repeat(61)) }, items[1]] }).success).toBe(false);
    expect(ExperienceArtifactSchema.safeParse({ ...artifact(), kind: "list", items: [{ ...items[0], detail: copy("x".repeat(161)) }, items[1]] }).success).toBe(false);
  });

  it("requires emphasis to exist verbatim in each language, without accepting blank emphasis", () => {
    expect(ExperienceArtifactSchema.parse(artifact()).emphasis?.en).toBe("see the goals");
    expect(ExperienceArtifactSchema.safeParse({ ...artifact(), emphasis: { zh: "未出现", en: "see the goals" } }).success).toBe(false);
    expect(ExperienceArtifactSchema.safeParse({ ...artifact(), emphasis: { zh: "先了解目标", en: "See the goals" } }).success).toBe(false);
    expect(ExperienceArtifactSchema.safeParse({ ...artifact(), emphasis: copy(" ") }).success).toBe(false);
  });

  it("highlights literal punctuation once and reconstructs the complete original input", () => {
    const original = "Before <b>[a.*]</b> and <b>[a.*]</b> after.";
    const parts = artifactInputParts(original, "<b>[a.*]</b>");
    expect(parts.map(part => part.text).join("")).toBe(original);
    expect(parts.filter(part => part.emphasized)).toEqual([{ text: "<b>[a.*]</b>", emphasized: true }]);
    expect(artifactInputParts(original, "missing")).toEqual([{ text: original, emphasized: false }]);
    expect(artifactInputParts(original, "")).toEqual([{ text: original, emphasized: false }]);
  });

  it("renders actual mark text and escapes supplied markup instead of executing it", () => {
    const view = ExperienceArtifactSchema.parse({ ...artifact(), input: copy("Before <script>alert(1)</script> after"), emphasis: copy("<script>alert(1)</script>") });
    const html = renderToStaticMarkup(createElement(ExperienceArtifact, { artifact: view, lang: "en" }));
    expect(html).toContain("<mark>&lt;script&gt;alert(1)&lt;/script&gt;</mark>");
    expect(html).not.toContain("<script>");
    expect(html).toContain("Fictional example · Not vendor output");
    expect(html).not.toContain("<iframe");
    expect(html).not.toContain("<img");
    expect(html).not.toContain("<video");
  });

  it("renders ordered sequences and unordered lists using their actual item text", () => {
    for (const kind of ["sequence", "list"] as const) {
      const view = ExperienceArtifactSchema.parse({ ...artifact(), kind, items: [
        { label: copy("Existing first item"), detail: copy("First prepared detail") },
        { label: copy("Existing second item"), detail: copy("Second prepared detail") },
      ] });
      const html = renderToStaticMarkup(createElement(ExperienceArtifact, { artifact: view, lang: "en" }));
      expect(html).toContain(kind === "sequence" ? '<ol class="experience-artifact__items">' : '<ul class="experience-artifact__items">');
      expect(html).toContain("Existing first item");
      expect(html).toContain("Second prepared detail");
      expect(html).not.toContain("<mark>");
    }
  });
});
