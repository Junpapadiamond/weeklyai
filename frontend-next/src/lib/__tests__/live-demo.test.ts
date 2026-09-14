import { describe, expect, it } from "vitest";
import { DemoSpecSchema, exampleSpec, supportsLiveDemo } from "../live-demo";

describe("interactive demo eligibility and render contract", () => {
  it("enables product workflows and hardware concept experiences for web products", () => {
    expect(supportsLiveDemo({ website: "https://www.lovable.dev/" })).toBe(true);
    for (const website of ["https://lovable.dev@evil.test", "javascript:alert(1)", "invalid"]) {
      expect(supportsLiveDemo({ website })).toBe(false);
    }
    expect(supportsLiveDemo({ website: "https://exa.ai", needs_verification: true })).toBe(true);
    expect(supportsLiveDemo({ website: "https://helixdi.com", is_hardware: true })).toBe(true);
  });
  it("supports every prepared example in both languages", () => {
    for (const en of [true, false]) for (const kind of ["timer", "tasks", "expenses"] as const) {
      expect(DemoSpecSchema.parse(exampleSpec(kind, en)).kind).toBe(kind);
    }
  });
  it("rejects unsupported components and unsafe configuration values", () => {
    const valid = exampleSpec("timer", false);
    for (const change of [{ kind: "iframe" }, { minutes: 0 }, { minutes: true }, { minutes: 999 }, { accent: "url(https://evil.test)" }, { title: "" }, { items: [null] }]) {
      expect(DemoSpecSchema.safeParse({ ...valid, ...change }).success).toBe(false);
    }
    expect(DemoSpecSchema.parse({ ...valid, script: "alert(1)" })).not.toHaveProperty("script");
  });
});
