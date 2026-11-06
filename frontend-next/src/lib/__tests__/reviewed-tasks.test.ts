import { describe, expect, it } from "vitest";
import { reviewedTasks } from "@/components/demo/reviewed/catalog";
import { reviewedIds } from "@/components/demo/reviewed/ids";
import { ProductSchema } from "@/lib/schemas";

describe("reviewed prepared examples", () => {
  it("loads a bilingual, sourced activity for every reviewed product ID", () => {
    expect(Object.keys(reviewedTasks).sort()).toEqual([...reviewedIds].sort());
    expect(reviewedIds.size).toBe(72);
    for (const task of Object.values(reviewedTasks)) {
      for (const copy of [task.title, task.instruction, task.result]) {
        expect(copy.every(value => value.trim().length > 0)).toBe(true);
      }
      expect(["https:", "http:"]).toContain(new URL(task.source).protocol);
      if (task.kind === "policy") {
        for (const [, indices] of task.rows) expect(indices.every(i => task.rules[i])).toBe(true);
      }
      if (task.kind === "slots") {
        expect(task.times.some((_, i) => task.rows.every(([, slots]) => slots.includes(i)))).toBe(true);
      }
      if (task.kind === "threshold") {
        const included = task.rows.filter(([, a, b]) => [a,b].every((v, i) =>
          task.axes[i][1] === "max" ? v <= task.axes[i][2] : v >= task.axes[i][2]));
        expect(included.length).toBeGreaterThan(0);
        expect(included.length).toBeLessThan(task.rows.length);
      }
    }
  });

  it("corrects the two stale domains without overriding a newer address", () => {
    const address = (id: string, website: string) => ProductSchema.parse({ _id: id, name: "Example", website }).website;
    expect(address("766", "https://fini.ai/")).toBe("https://www.usefini.com/");
    expect(address("p_bd97057d7bb7aa84", "https://www.instinctdogtraining.com/")).toBe("https://instinct.com/");
    expect(address("766", "https://future.example")).toBe("https://future.example");
    expect(address("other", "https://fini.ai/")).toBe("https://fini.ai/");
  });
});
