import { describe, expect, it } from "vitest";
import {
  filterProducts,
  getDirectionLabel,
  getFreshnessLabel,
  getLogoCandidates,
  getLogoFallbacks,
  getProductDirections,
  getMonogram,
  getTierTone,
  isValidLogoSource,
  normalizeDirectionToken,
  normalizeLogoSource,
  normalizeWebsite,
  shouldRenderLogoImage,
  parseFundingAmount,
  sortProducts,
  tierOf,
} from "@/lib/product-utils";
import type { Product } from "@/types/api";

describe("product-utils", () => {
  it("normalizes website and rejects placeholder values", () => {
    expect(normalizeWebsite("example.com")).toBe("https://example.com");
    expect(normalizeWebsite("unknown")).toBe("");
  });

  it("normalizes logo source for relative and absolute urls", () => {
    expect(normalizeLogoSource("/logos/a.png")).toBe("/logos/a.png");
    expect(normalizeLogoSource("logo.clearbit.com/a.com")).toBe("https://logo.clearbit.com/a.com");
    expect(normalizeLogoSource("https://a.com/logo.png")).toBe("https://a.com/logo.png");
    expect(normalizeLogoSource("https:///logos/dark-horses/skild-ai.ico")).toBe("/logos/dark-horses/skild-ai.ico");
    expect(normalizeLogoSource("not-a-url")).toBe("");
    expect(isValidLogoSource("/logos/a.png")).toBe(true);
    expect(isValidLogoSource("https://a.com/logo.png")).toBe(true);
    expect(isValidLogoSource("not-a-url")).toBe(false);
    expect(shouldRenderLogoImage("/logos/a.png")).toBe(true);
    expect(shouldRenderLogoImage("https://a.com/logo.png")).toBe(false);
    expect(shouldRenderLogoImage("https://logo.clearbit.com/a.com")).toBe(false);
  });

  it("builds logo fallback chain in expected order", () => {
    const fallbacks = getLogoFallbacks("https://www.example.com");
    expect(fallbacks).toEqual([
      "https://www.google.com/s2/favicons?domain=example.com&sz=128",
      "https://icons.duckduckgo.com/ip3/example.com.ico",
      "https://icon.horse/icon/example.com",
      "https://example.com/favicon.ico",
      "https://www.example.com/favicon.ico",
      "https://logo.clearbit.com/example.com",
    ]);
  });

  it("combines trusted logos with fallback chain and removes untrusted provider logos", () => {
    const candidates = getLogoCandidates({
      logoUrl: "https://logo.clearbit.com/example.com",
      secondaryLogoUrl: "/logos/custom/example.png",
      website: "https://example.com",
    });

    expect(candidates[0]).toBe("/logos/custom/example.png");
    expect(candidates).toEqual([
      "/logos/custom/example.png",
      "https://www.google.com/s2/favicons?domain=example.com&sz=128",
      "https://icons.duckduckgo.com/ip3/example.com.ico",
      "https://icon.horse/icon/example.com",
      "https://example.com/favicon.ico",
      "https://www.example.com/favicon.ico",
      "https://logo.clearbit.com/example.com",
    ]);

    const fallbackOnly = getLogoCandidates({
      logoUrl: "not-a-url",
      website: "example.com",
    });
    expect(fallbackOnly[0]).toBe("https://www.google.com/s2/favicons?domain=example.com&sz=128");

    const withBingPrimary = getLogoCandidates({
      logoUrl: "https://favicon.bing.com/favicon.ico?url=example.com&size=128",
      website: "example.com",
    });
    expect(withBingPrimary[0]).toBe("https://www.google.com/s2/favicons?domain=example.com&sz=128");
    expect(withBingPrimary[withBingPrimary.length - 1]).toBe("https://favicon.bing.com/favicon.ico?url=example.com&size=128");

    const derivedFromLogoSource = getLogoCandidates({
      logoUrl: "https://logo.clearbit.com/example.com",
      website: "unknown",
      sourceUrl: "",
    });
    expect(derivedFromLogoSource).toEqual([]);

    const rejectSocialLogo = getLogoCandidates({
      logoUrl: "https://www.youtube.com/s/desktop/abc/img/favicon_32x32.png",
      website: "https://example.com",
    });
    expect(rejectSocialLogo[0]).toBe("https://www.google.com/s2/favicons?domain=example.com&sz=128");
    expect(rejectSocialLogo).not.toContain("https://www.youtube.com/s/desktop/abc/img/favicon_32x32.png");
  });

  it("parses funding amounts with units", () => {
    expect(parseFundingAmount("$35M")).toBe(35);
    expect(parseFundingAmount("$1.2B")).toBe(1200);
    expect(parseFundingAmount("¥3亿")).toBe(300);
  });

  it("computes tier correctly", () => {
    expect(tierOf({ name: "A", description: "x", dark_horse_index: 4 })).toBe("darkhorse");
    expect(tierOf({ name: "B", description: "x", dark_horse_index: 3 })).toBe("rising");
    expect(tierOf({ name: "C", description: "x", dark_horse_index: 1 })).toBe("other");
    expect(getTierTone({ name: "A", description: "x", dark_horse_index: 4 })).toBe("darkhorse");
    expect(getTierTone({ name: "B", description: "x", dark_horse_index: 2 })).toBe("rising");
    expect(getTierTone({ name: "C", description: "x", dark_horse_index: 1 })).toBe("watch");
  });

  it("filters and sorts products", () => {
    const now = Date.now();
    const products: Product[] = [
      {
        name: "HotOld",
        description: "a",
        dark_horse_index: 5,
        hot_score: 98,
        final_score: 95,
        category: "coding",
        funding_total: "$1M",
        discovered_at: new Date(now - 120 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        name: "FreshBalanced",
        description: "b",
        dark_horse_index: 3,
        hot_score: 72,
        category: "hardware",
        is_hardware: true,
        funding_total: "$20M",
        discovered_at: new Date(now - 2 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        name: "FreshLowHeatRich",
        description: "c",
        dark_horse_index: 2,
        hot_score: 40,
        category: "agent",
        funding_total: "$1.2B",
        discovered_at: new Date(now - 2 * 60 * 60 * 1000).toISOString(),
      },
    ];

    const filtered = filterProducts(products, { tier: "rising", type: "hardware" });
    expect(filtered).toHaveLength(1);
    expect(filtered[0]?.name).toBe("FreshBalanced");

    const trendingSorted = sortProducts(products, "trending");
    const recencySorted = sortProducts(products, "recency");
    const compositeSorted = sortProducts(products, "composite");
    const fundingSorted = sortProducts(products, "funding");
    const legacyScoreSorted = sortProducts(products, "score");
    const legacyDateSorted = sortProducts(products, "date");

    expect(trendingSorted[0]?.name).toBe("HotOld");
    expect(recencySorted[0]?.name).toBe("FreshLowHeatRich");
    expect(compositeSorted[0]?.name).toBe("FreshBalanced");
    expect(fundingSorted[0]?.name).toBe("FreshLowHeatRich");
    expect(legacyScoreSorted[0]?.name).toBe("HotOld");
    expect(legacyDateSorted[0]?.name).toBe("FreshLowHeatRich");
  });

  it("normalizes product directions for second-level filtering", () => {
    expect(normalizeDirectionToken("AI voice assistant")).toBe("voice");
    expect(normalizeDirectionToken("智能驾驶")).toBe("driving");
    expect(getDirectionLabel("ai_chip")).toBe("AI芯片");

    const directions = getProductDirections({
      name: "Test",
      description: "x",
      category: "agent",
      categories: ["voice", "hardware"],
      hardware_category: "robotics",
      use_case: "智能驾驶",
    });

    expect(directions).toContain("agent");
    expect(directions).toContain("voice");
    expect(directions).toContain("robotics");
    expect(directions).toContain("driving");
    expect(directions).not.toContain("hardware");
  });

  it("generates freshness labels from available dates", () => {
    const now = new Date("2026-02-10T12:00:00.000Z");

    expect(getFreshnessLabel({ name: "A", description: "x", discovered_at: "2026-02-09T12:00:00.000Z" }, now)).toBe("1天前");
    expect(getFreshnessLabel({ name: "B", description: "x", first_seen: "2026-02-10T08:00:00.000Z" }, now)).toBe("4小时前");
    expect(getFreshnessLabel({ name: "C", description: "x", published_at: "2026-02-10T11:30:00.000Z" }, now)).toBe("1小时内");
    expect(getFreshnessLabel({ name: "D", description: "x" }, now)).toBe("时间待补充");
  });

  it("generates monogram fallback for latin, chinese and empty names", () => {
    expect(getMonogram("Weekly AI")).toBe("W");
    expect(getMonogram("星火助手")).toBe("星");
    expect(getMonogram("  ")).toBe("AI");
    expect(getMonogram(undefined)).toBe("AI");
  });
});
