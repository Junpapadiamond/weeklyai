import { describe, expect, it } from "vitest";
import { readdirSync, readFileSync } from "node:fs";
import { availableExperienceOptions, demoErrorMessage, ExperienceSchema, readDemo, updateExperienceChoice } from "../demo-experience";

describe("data-only workflow renderer", () => {
  const folder = "../backend/data/demos";
  const specs = readdirSync(folder).filter(f => f.endsWith(".json")).map(f => JSON.parse(readFileSync(folder + "/" + f, "utf8")).spec);
  it("accepts every published bilingual workflow", () => {
    expect(specs.length).toBeGreaterThanOrEqual(5);
    specs.forEach(spec => expect(ExperienceSchema.safeParse(spec).success).toBe(true));
  });
  it("accepts the reviewed Higgsfield profile and rejects executable workspace kinds", () => {
    const profile = JSON.parse(readFileSync("../backend/data/demo_profiles/higgsfield.json", "utf8"));
    // Python supplies deterministic option IDs and example_data before serving.
    const spec = { ...profile, steps: profile.steps.map((s: { options: object[] }) => ({ ...s, example_data: true, options: s.options.map((o, i) => ({ ...o, id: String(i) })) })) };
    expect(ExperienceSchema.parse(spec).workspace?.kind).toBe("video");
    expect(ExperienceSchema.safeParse({ ...spec, workspace: { ...spec.workspace, kind: "iframe" } }).success).toBe(false);
    expect(ExperienceSchema.parse({ ...spec, workspace: { ...spec.workspace, script: "alert(1)" } }).workspace).not.toHaveProperty("script");
  });
  it("changes Autentic insights and decisions with the research focus, clearing stale choices", () => {
    const profile = JSON.parse(readFileSync("../backend/data/demo_profiles/autentic.json", "utf8"));
    const spec = ExperienceSchema.parse({ ...profile, steps: profile.steps.map((s: { options: object[] }) => ({
      ...s, example_data: true, options: s.options.map((o, i) => ({ ...o, id: String(i) })),
    })) });
    const barriers = { setup: "0", input: "1", inspection: "3", output: "2" };
    expect(availableExperienceOptions(spec.steps[2], barriers).map(o => o.id)).toEqual(["2", "3"]);
    expect(updateExperienceChoice(spec, barriers, "input", "1")).toEqual(barriers);
    const adoption = updateExperienceChoice(spec, barriers, "input", "0");
    expect(adoption).toEqual({ setup: "0", input: "0" });
    expect(availableExperienceOptions(spec.steps[2], adoption).map(o => o.id)).toEqual(["0", "1"]);
    expect(availableExperienceOptions(spec.steps[3], adoption).map(o => o.id)).toEqual(["0", "1"]);
    expect(updateExperienceChoice(spec, adoption, "inspection", "3")).toEqual(adoption);
    expect(spec.product_context?.trial_url).toBe("https://www.autentic.ai/try-interviewer");
    expect(ExperienceSchema.safeParse({ ...spec, product_context: { ...spec.product_context, trial_url: "https://uncited.example" } }).success).toBe(false);
    const broken = structuredClone(spec);
    broken.steps[2].options[0].when = { step_id: "output", option_id: "0" };
    expect(ExperienceSchema.safeParse(broken).success).toBe(false);
  });
  it("rejects executable widgets and forged evidence links", () => {
    const spec = specs[0];
    expect(ExperienceSchema.safeParse({ ...spec, steps: [{ ...spec.steps[0], widget: "iframe" }, ...spec.steps.slice(1)] }).success).toBe(false);
    expect(ExperienceSchema.safeParse({ ...spec, sources: [{ label: { zh: "来源", en: "Source" }, url: "javascript:alert(1)" }] }).success).toBe(false);
    expect(ExperienceSchema.parse({ ...spec, script: "alert(1)" })).not.toHaveProperty("script");
  });
  it("handles non-JSON gateway failures without exposing parser errors", async () => {
    await expect(readDemo(new Response("Gateway timeout", { status: 504 }))).rejects.toThrow("SERVICE_UNAVAILABLE");
    await expect(readDemo(Response.json(null))).rejects.toThrow("SERVICE_UNAVAILABLE");
  });
  it("retains safe backend errors and refunded credits", async () => {
    const body = { success: false, error: "GENERATION_TIMEOUT", quota: { remaining: 3, limit: 3 }, generation_available: true };
    await expect(readDemo(Response.json(body, { status: 503 }))).resolves.toEqual(body);
    expect(demoErrorMessage(body.error)[0]).toContain("超时");
    expect(demoErrorMessage("GENERATION_INVALID_RESPONSE")[0]).toContain("重新生成");
    expect(demoErrorMessage("GENERATOR_BUSY")[0]).toContain("繁忙");
  });
  it("rejects invalid cached experiences with a readable error code", async () => {
    await expect(readDemo(Response.json({ success: true, experience: { spec: {} } }))).rejects.toThrow("GENERATION_INVALID_RESPONSE");
  });
});
