// Run on Node 24 before publishing data: use the same schemas as rendering.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { ProductSchema, BlogSchema } from "../src/lib/schemas.ts";

const root = process.argv[2] ? resolve(process.argv[2]) : fileURLToPath(new URL("../../crawler/data/", import.meta.url));
const files = [["products_featured.json", ProductSchema], ["blogs_news.json", BlogSchema]];
const curated = resolve(root, "dark_horses");
if (existsSync(curated)) {
  for (const name of readdirSync(curated).sort()) {
    if (name.endsWith(".json") && name !== "template.json") files.push([`dark_horses/${name}`, ProductSchema]);
  }
}
let checked = 0;
let failures = 0;
for (const [name, schema] of files) {
  try {
    const data = JSON.parse(readFileSync(resolve(root, name), "utf8"));
    const rows = Array.isArray(data) ? data : name.startsWith("dark_horses/") ? [data] : null;
    if (!rows) throw new Error("expected an array");
    for (const [index, row] of rows.entries()) {
      checked++;
      const result = schema.safeParse(row);
      if (!result.success) {
        failures++;
        // Log field paths/types only, never raw provider payloads or secrets.
        console.error(`${name}[${index}]: ${result.error.issues.map(i => `${i.path.join(".")}: ${i.message}`).join("; ")}`);
      }
    }
  } catch (error) {
    failures++;
    console.error(`${name}: ${error.message}`);
  }
}
console.log(`Frontend catalog contract: ${checked} records checked; ${failures} failures.`);
if (failures) process.exitCode = 1;
