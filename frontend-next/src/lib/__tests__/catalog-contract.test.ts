import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { expect, it } from "vitest";

it("blocks unrenderable published data but accepts numeric funding", () => {
  const dir = mkdtempSync(resolve(tmpdir(), "weeklyai-catalog-"));
  const run = () => spawnSync(process.execPath, ["scripts/verify-catalog.mjs", dir], { encoding: "utf8" });
  try {
    writeFileSync(resolve(dir, "blogs_news.json"), "[]");
    writeFileSync(resolve(dir, "products_featured.json"), JSON.stringify([{ name: "Autoheal", funding_total: 7900000 }]));
    expect(run().status).toBe(0);
    writeFileSync(resolve(dir, "products_featured.json"), JSON.stringify([{ name: "Broken", categories: "not an array" }]));
    const invalid = run();
    expect(invalid.status).toBe(1);
    expect(invalid.stderr).toContain("categories");
  } finally {
    rmSync(dir, { recursive: true });
  }
});
