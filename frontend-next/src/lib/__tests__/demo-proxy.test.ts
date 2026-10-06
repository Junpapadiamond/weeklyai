import { afterEach, expect, it, vi } from "vitest";
import { GET, POST } from "../../app/api/v1/[...path]/route";

afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });
const context = (path: string[]) => ({ params: Promise.resolve(path ? { path } : { path: [] }) });

it("allows CDN caching only for anonymous prepared playback", async () => {
  vi.stubEnv("API_BASE_URL_SERVER", "https://backend.example/api/v1");
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(Response.json({ success: true }, {
    headers: { "Cache-Control": "public, max-age=0" },
  })));
  const response = await GET(new Request("https://site.example/api/v1/demos/prepared/exa"), context(["demos", "prepared", "exa"]));
  expect(response.headers.get("Cache-Control")).toContain("s-maxage=300");
  expect(response.headers.has("Set-Cookie")).toBe(false);
});

it.each([["demos", "catalog"], ["demos", "product", "exa"], ["demos", "prepared", "exa"]])("never caches visitor cookies for %j", async (...path) => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(Response.json({ success: true }, {
    headers: { "Cache-Control": "public, max-age=0", "Set-Cookie": "weeklyai_demo_visitor=private; HttpOnly" },
  })));
  const response = await GET(new Request("https://site.example/api/v1/" + path.join("/")), context(path));
  expect(response.headers.get("Cache-Control")).toBe("no-store");
});

it("never caches POST generation responses", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(Response.json({ success: true }, {
    headers: { "Cache-Control": "public, max-age=0" },
  })));
  const response = await POST(new Request("https://site.example/api/v1/demos/generate", { method: "POST", body: "{}" }), context(["demos", "generate"]));
  expect(response.headers.get("Cache-Control")).toBe("no-store");
});
