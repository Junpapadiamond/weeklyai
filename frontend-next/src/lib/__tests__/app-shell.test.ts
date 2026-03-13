import { describe, expect, it } from "vitest";
import { IOS_APP_SHELL_UA_MARKER, isAppShellUserAgent } from "@/lib/app-shell";

describe("app-shell", () => {
  it("detects iOS app shell marker", () => {
    const ua = `Mozilla/5.0 AppleWebKit/605.1.15 ${IOS_APP_SHELL_UA_MARKER}`;
    expect(isAppShellUserAgent(ua)).toBe(true);
  });

  it("detects iOS app shell version prefix", () => {
    const ua = "Mozilla/5.0 WeeklyAIApp-iOS/2.0";
    expect(isAppShellUserAgent(ua)).toBe(true);
  });

  it("returns false for browser user agents", () => {
    const ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36";
    expect(isAppShellUserAgent(ua)).toBe(false);
  });
});
