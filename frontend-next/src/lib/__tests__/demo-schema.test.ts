import { describe, expect, it } from "vitest";
import { DemoSpecSchema, isReconstruction } from "@/lib/demo-schema";
import { demoSlug } from "@/lib/demo-client";

function spec(overrides: Record<string, unknown> = {}) {
  return {
    version: 1,
    product_slug: "acme",
    product_name: "Acme",
    tier: "concept",
    title: { zh: "标题", en: "Title" },
    premise: { zh: "前提", en: "Premise" },
    confidence: "inferred",
    evidence: [{ claim: "Acme raised a round.", source_url: "https://example.com/a" }],
    steps: [0, 1, 2].map((i) => ({
      id: `s${i}`,
      label: { zh: "步骤", en: "Step" },
      narration: { zh: "说明", en: "Narration" },
      widget: {
        type: "pipeline",
        stages: [
          { name: { zh: "一", en: "One" }, input: { zh: "输入", en: "in" }, output: { zh: "输出", en: "out" } },
          { name: { zh: "二", en: "Two" }, input: { zh: "输入", en: "in" }, output: { zh: "输出", en: "out" } },
        ],
      },
    })),
    ...overrides,
  };
}

describe("DemoSpecSchema", () => {
  it("accepts a well-formed spec", () => {
    const parsed = DemoSpecSchema.safeParse(spec());
    expect(parsed.success).toBe(true);
  });

  it("rejects a simulation that claims to be verified", () => {
    const parsed = DemoSpecSchema.safeParse(spec({ tier: "simulation", confidence: "verified" }));
    expect(parsed.success).toBe(false);
  });

  it("accepts a simulation marked illustrative", () => {
    const parsed = DemoSpecSchema.safeParse(spec({ tier: "simulation", confidence: "illustrative" }));
    expect(parsed.success).toBe(true);
  });

  it("rejects fewer than three or more than five steps", () => {
    expect(DemoSpecSchema.safeParse(spec({ steps: [] })).success).toBe(false);
    const many = spec();
    expect(DemoSpecSchema.safeParse(spec({ steps: [...many.steps, ...many.steps] })).success).toBe(false);
  });

  it("rejects an unknown widget type", () => {
    const bad = spec();
    bad.steps[0].widget = { type: "iframe", src: "https://evil.example" } as never;
    expect(DemoSpecSchema.safeParse(bad).success).toBe(false);
  });

  it("requires both locales", () => {
    expect(DemoSpecSchema.safeParse(spec({ title: { zh: "只有中文", en: "" } })).success).toBe(false);
  });

  it("rejects plain-string prose where a locale pair belongs", () => {
    const bad = spec();
    bad.steps[0].widget.stages[0].output = "English only" as never;
    expect(DemoSpecSchema.safeParse(bad).success).toBe(false);
  });

  it("rejects a live query widget with no registered endpoint", () => {
    const bad = spec({ tier: "sandbox", confidence: "verified" });
    bad.steps[0].widget = {
      type: "query_response",
      mode: "live",
      endpoint_id: null,
      allow_free_input: false,
      presets: [{ query: "q", response: { zh: "结果", en: "result" } }],
    } as never;
    expect(DemoSpecSchema.safeParse(bad).success).toBe(false);
  });

  it("rejects a value that is neither sourced nor flagged as an example", () => {
    const bad = spec();
    bad.steps[0].widget = {
      type: "param_dial",
      param: { zh: "参数", en: "Param" },
      min: 0,
      max: 10,
      step: 1,
      unit: "x",
      formula_note: { zh: "说明", en: "Note" },
      outputs: [{ label: { zh: "A", en: "A" }, value: { zh: "42", en: "42" }, evidence_ref: null, is_example: false }],
    } as never;
    expect(DemoSpecSchema.safeParse(bad).success).toBe(false);
  });

  it("accepts a value flagged as an example", () => {
    const ok = spec();
    ok.steps[0].widget = {
      type: "param_dial",
      param: { zh: "参数", en: "Param" },
      min: 0,
      max: 10,
      step: 1,
      unit: "x",
      formula_note: { zh: "说明", en: "Note" },
      outputs: [{ label: { zh: "A", en: "A" }, value: { zh: "42", en: "42" }, evidence_ref: null, is_example: true }],
    } as never;
    expect(DemoSpecSchema.safeParse(ok).success).toBe(true);
  });

  it("defaults vendor_status to none", () => {
    const parsed = DemoSpecSchema.parse(spec());
    expect(parsed.vendor_status).toBe("none");
  });
});

describe("isReconstruction", () => {
  it("is true only for simulations", () => {
    expect(isReconstruction({ tier: "simulation" })).toBe(true);
    expect(isReconstruction({ tier: "sandbox" })).toBe(false);
    expect(isReconstruction({ tier: "concept" })).toBe(false);
    expect(isReconstruction({ tier: "tour" })).toBe(false);
  });
});

describe("demoSlug", () => {
  // Must agree with _slugify in backend/app/services/demo_repository.py, or the
  // picker marks demos as missing that the API can actually serve.
  it("matches the backend slug rules", () => {
    expect(demoSlug("Fireworks AI")).toBe("fireworks-ai");
    expect(demoSlug("  Exa!  ")).toBe("exa");
    expect(demoSlug("Apptronik")).toBe("apptronik");
    expect(demoSlug("A  B---C")).toBe("a-b-c");
    expect(demoSlug("")).toBe("");
  });
});
