import { describe, expect, it } from "vitest";
import { listEnvelope, ProductSchema } from "@/lib/schemas";

describe("schemas", () => {
  it("keeps a product list renderable when funding is a numeric amount", () => {
    const result = listEnvelope(ProductSchema).parse({
      success: true,
      data: [
        { name: "Autoheal", funding_total: 7900000 },
        { name: "Formatted funding", funding_total: "$7.9M" },
        { name: "No funding", funding_total: 0 },
        { name: "Undisclosed funding" },
      ],
    });

    expect(result.data.map((product) => product.funding_total)).toEqual([
      "7900000", "$7.9M", "0", undefined,
    ]);
  });

  it.each([{ funding_total: true }, { funding_total: {} }, { funding_total: [] }])("rejects a malformed funding amount: $funding_total", ({ funding_total }) => {
    expect(ProductSchema.safeParse({ name: "Invalid product", funding_total }).success).toBe(false);
  });

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
