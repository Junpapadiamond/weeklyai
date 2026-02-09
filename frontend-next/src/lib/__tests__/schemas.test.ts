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
        },
      ],
    });

    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.data[0]?._id).toBe("1");
      expect(result.data.data[0]?.dark_horse_index).toBe(4);
    }
  });
});
