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

  it("tolerates empty or invalid logo metadata without dropping the list", () => {
    const schema = listEnvelope(ProductSchema);
    const result = schema.safeParse({
      success: true,
      data: [
        {
          _id: "a",
          name: "Bad Logo Source Product",
          description: "Test item",
          website: "https://example.com",
          logo_status: "FAILED",
          logo_source: "",
        },
        {
          _id: "b",
          name: "Unknown Logo Source Product",
          description: "Test item",
          website: "https://example.org",
          logo_status: "ok",
          logo_source: "unknown_source",
        },
      ],
    });

    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.data).toHaveLength(2);
      expect(result.data.data[0]?.logo_status).toBe("failed");
      expect(result.data.data[0]?.logo_source).toBeUndefined();
      expect(result.data.data[1]?.logo_status).toBe("ok");
      expect(result.data.data[1]?.logo_source).toBeUndefined();
    }
  });
});
