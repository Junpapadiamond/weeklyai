import { describe, expect, it } from "vitest";
import { readdirSync, readFileSync } from "node:fs";
import { demoErrorMessage, ExperienceSchema, readDemo } from "../demo-experience";

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
