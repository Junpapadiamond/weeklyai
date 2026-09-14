import { describe, expect, it } from "vitest";
import { readdirSync, readFileSync } from "node:fs";
import { ExperienceSchema } from "../demo-experience";

describe("data-only workflow renderer", () => {
  const folder = "../backend/data/demos";
  const specs = readdirSync(folder).filter(f => f.endsWith(".json")).map(f => JSON.parse(readFileSync(folder + "/" + f, "utf8")).spec);
  it("accepts every published bilingual workflow", () => {
    expect(specs.length).toBeGreaterThanOrEqual(5);
    specs.forEach(spec => expect(ExperienceSchema.safeParse(spec).success).toBe(true));
  });
  it("rejects executable widgets and forged evidence links", () => {
    const spec = specs[0];
    expect(ExperienceSchema.safeParse({ ...spec, steps: [{ ...spec.steps[0], widget: "iframe" }, ...spec.steps.slice(1)] }).success).toBe(false);
    expect(ExperienceSchema.safeParse({ ...spec, sources: [{ label: { zh: "来源", en: "Source" }, url: "javascript:alert(1)" }] }).success).toBe(false);
    expect(ExperienceSchema.parse({ ...spec, script: "alert(1)" })).not.toHaveProperty("script");
  });
});
