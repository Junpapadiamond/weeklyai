import { afterEach, expect, it, vi } from "vitest";
import { readdirSync, readFileSync } from "node:fs";
import { loadProductDemo } from "../demo-loading";

const folder = "../backend/data/demos";
const experience = JSON.parse(readFileSync(`${folder}/${readdirSync(folder).find(f => f.endsWith(".json"))}`, "utf8"));
const controller = () => new AbortController();
const payload = (body: object) => Response.json({ success: true, generation_available: true, quota: null, ...body });
afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers(); });

it("reopens validated experiences without another network request or stale personal quota", async () => {
  const fetcher = vi.fn().mockResolvedValue(payload({ state: "ready", experience, quota: { remaining: 2 } }));
  vi.stubGlobal("fetch", fetcher);
  await loadProductDemo("replay", { signal: controller().signal });
  const replay = await loadProductDemo("replay", { signal: controller().signal });
  expect(replay.experience).toBeTruthy();
  expect(replay.quota).toBeNull();
  expect(fetcher).toHaveBeenCalledTimes(1);
});

it("check again is read-only even when the earlier request did not complete", async () => {
  const fetcher = vi.fn().mockResolvedValue(payload({ state: "not_generated" }));
  vi.stubGlobal("fetch", fetcher);
  await loadProductDemo("check-only", { signal: controller().signal, checkOnly: true });
  expect(fetcher).toHaveBeenCalledTimes(1);
  expect(fetcher.mock.calls[0][0]).toContain("/prepared/");
});

it("joins an existing generation without POST and stops when its lease ends", async () => {
  vi.useFakeTimers();
  const fetcher = vi.fn()
    .mockResolvedValueOnce(payload({ state: "generating" }))
    .mockResolvedValueOnce(payload({ state: "not_generated" }));
  vi.stubGlobal("fetch", fetcher);
  const pending = loadProductDemo("failed-job", { signal: controller().signal });
  await vi.advanceTimersByTimeAsync(2000);
  expect(await pending).toMatchObject({ success: false, error: "GENERATION_FAILED" });
  expect(fetcher).toHaveBeenCalledTimes(2);
  expect(fetcher.mock.calls.every(call => call[1].method !== "POST")).toBe(true);
});

it("does not keep polling an error response", async () => {
  vi.useFakeTimers();
  const fetcher = vi.fn()
    .mockResolvedValueOnce(payload({ state: "not_generated" }))
    .mockResolvedValueOnce(payload({ state: "generating" }))
    .mockResolvedValueOnce(payload({ success: false, error: "STORAGE_UNAVAILABLE" }));
  vi.stubGlobal("fetch", fetcher);
  const pending = loadProductDemo("poll-error", { signal: controller().signal });
  await vi.advanceTimersByTimeAsync(2000);
  expect(await pending).toMatchObject({ success: false, error: "STORAGE_UNAVAILABLE" });
  expect(fetcher).toHaveBeenCalledTimes(3);
  expect(fetcher.mock.calls.filter(call => call[1].method === "POST")).toHaveLength(1);
});

it("cancels polling when the user closes the experience", async () => {
  vi.useFakeTimers();
  const fetcher = vi.fn().mockResolvedValue(payload({ state: "generating" }));
  vi.stubGlobal("fetch", fetcher);
  const abort = controller();
  const pending = loadProductDemo("closed", { signal: abort.signal });
  const result = expect(pending).rejects.toMatchObject({ name: "AbortError" });
  await vi.advanceTimersByTimeAsync(1);
  abort.abort();
  await result;
  await vi.advanceTimersByTimeAsync(10000);
  expect(fetcher).toHaveBeenCalledTimes(1);
});
