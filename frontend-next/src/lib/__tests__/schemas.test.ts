import { describe, expect, it } from "vitest";
import { listEnvelope, ProductSchema } from "@/lib/schemas";

describe("schemas", () => {
  it("parses product list envelope safely", () => {
    const schema = listEnvelope(ProductSchema);
    const result = schema.safeParse({
      success: true,
      data: [
        {
          _id: 1,
          name: "Dash0",
          description: "AI observability platform",
          website: "https://dash0.com",
          dark_horse_index: "4",
          screenshot_worthy: true,
          hook: "quiet_real_problem",
          pick_reason: "Solves a concrete workflow.",
          v2_score: "42.5",
          v2_signals: ["real problem"],
          criteria_met: ["legacy_signal"],
        },
      ],
    });

    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.data[0]?._id).toBe("1");
      expect(result.data.data[0]?.dark_horse_index).toBe(4);
      expect(result.data.data[0]?.screenshot_worthy).toBe(true);
      expect(result.data.data[0]?.hook).toBe("quiet_real_problem");
      expect(result.data.data[0]?.pick_reason).toBe("Solves a concrete workflow.");
      expect(result.data.data[0]?.v2_score).toBe(42.5);
      expect(result.data.data[0]?.v2_signals).toEqual(["real problem"]);
    }
  });
});
