import { afterEach, expect, it, vi } from "vitest";
import { formatNewsDate } from "../news-date";

afterEach(() => vi.unstubAllEnvs());

it("renders identical dates on UTC servers and New York browsers", () => {
  vi.stubEnv("TZ", "UTC");
  const server = formatNewsDate("2026-10-10T15:53:05Z", "zh-CN");
  vi.stubEnv("TZ", "America/New_York");
  expect(formatNewsDate("2026-10-10T15:53:05Z", "zh-CN")).toBe(server);
  expect(server).toContain("23:53");
  expect(server).toContain("北京时间");
  expect(formatNewsDate("2026-10-10T15:53:05", "zh-CN")).toBe(server);
  expect(formatNewsDate("2026-10-10T15:53:05Z", "en-US")).toContain("UTC");
});

it("handles absent and invalid timestamps without rendering Invalid Date", () => {
  expect(formatNewsDate(undefined, "zh-CN")).toBe("时间待补充");
  expect(formatNewsDate("bad date", "en-US")).toBe("Timestamp unavailable");
});
