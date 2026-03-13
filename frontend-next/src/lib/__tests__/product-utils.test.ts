import { describe, expect, it } from "vitest";
import {
  collectDirectionOptions,
  filterProducts,
  filterDirectionOptions,
  formatAbsoluteDate,
  formatCategories,
  formatRelativeDate,
  getDirectionLabel,
  getLocalizedBlogDescription,
  getLocalizedBlogName,
  getFreshnessLabel,
  getLocalizedCountryName,
  getLocalizedProductDescription,
  getLocalizedProductLatestNews,
  getLocalizedProductWhyMatters,
  getLogoCandidates,
  getLogoFallbacks,
  getProductDirections,
  getMonogram,
  getTierTone,
  getScoreTone,
  isValidLogoSource,
  normalizeDirectionToken,
  normalizeLogoSource,
  normalizeWebsite,
  resolveProductLogoSources,
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
      "https://example.com/apple-touch-icon.png",
      "https://example.com/favicon.ico",
      "https://www.example.com/apple-touch-icon.png",
      "https://www.example.com/favicon.ico",
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
      "https://example.com/apple-touch-icon.png",
      "https://example.com/favicon.ico",
      "https://www.example.com/apple-touch-icon.png",
      "https://www.example.com/favicon.ico",
    ]);

    const fallbackOnly = getLogoCandidates({
      logoUrl: "not-a-url",
      website: "example.com",
    });
    expect(fallbackOnly[0]).toBe("https://example.com/apple-touch-icon.png");

    const withBingPrimary = getLogoCandidates({
      logoUrl: "https://favicon.bing.com/favicon.ico?url=example.com&size=128",
      website: "example.com",
    });
    expect(withBingPrimary[0]).toBe("https://example.com/apple-touch-icon.png");
    expect(withBingPrimary).not.toContain("https://favicon.bing.com/favicon.ico?url=example.com&size=128");

    const withGooglePrimary = getLogoCandidates({
      logoUrl: "https://www.google.com/s2/favicons?domain=example.com&sz=128",
      website: "example.com",
    });
    expect(withGooglePrimary[0]).toBe("https://example.com/apple-touch-icon.png");
    expect(withGooglePrimary).not.toContain("https://www.google.com/s2/favicons?domain=example.com&sz=128");

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
    expect(rejectSocialLogo[0]).toBe("https://example.com/apple-touch-icon.png");
    expect(rejectSocialLogo).not.toContain("https://www.youtube.com/s/desktop/abc/img/favicon_32x32.png");

    const trustedExplicitLogo = getLogoCandidates({
      logoUrl: "https://framerusercontent.com/images/3S1XMF1Wu7nO2vBUopvF7ajENkY.png",
      website: "https://www.zyg.com/",
      trustPrimaryLogo: true,
    });
    expect(trustedExplicitLogo[0]).toBe("https://framerusercontent.com/images/3S1XMF1Wu7nO2vBUopvF7ajENkY.png");
  });

  it("resolves curated logo sources from the manifest", () => {
    expect(
      resolveProductLogoSources({
        name: "Science Corp.",
        description: "",
        website: "https://science.xyz/",
        logo_url: "",
      })
    ).toEqual({
      logoUrl: "https://science.xyz/favicon.svg",
      secondaryLogoUrl: "",
    });

    expect(
      resolveProductLogoSources({
        name: "ZyG",
        description: "",
        website: "https://www.zyg.com/",
        logo_url: "",
      })
    ).toEqual({
      logoUrl: "https://framerusercontent.com/images/3S1XMF1Wu7nO2vBUopvF7ajENkY.png",
      secondaryLogoUrl: "",
    });
  });

  it("drops generic placeholder and clearbit sources when resolving explicit logos", () => {
    expect(
      resolveProductLogoSources({
        name: "Placeholder Co",
        description: "",
        website: "https://placeholder.example/",
        logo_url: "/logos/custom/default-ai.svg",
        logo: "https://cdn.placeholder.example/logo.png",
      })
    ).toEqual({
      logoUrl: "https://cdn.placeholder.example/logo.png",
      secondaryLogoUrl: "",
    });

    expect(
      resolveProductLogoSources({
        name: "Clearbit Co",
        description: "",
        website: "https://clearbit.example/",
        logo_url: "https://logo.clearbit.com/clearbit.example",
        logo: "https://assets.clearbit.example/logo.svg",
      })
    ).toEqual({
      logoUrl: "https://assets.clearbit.example/logo.svg",
      secondaryLogoUrl: "",
    });
  });

  it("prefers manifest logos over derived website fallbacks", () => {
    expect(
      resolveProductLogoSources({
        name: "ZyG",
        description: "",
        website: "https://zyg.ai/",
        logo_url: "https://zyg.ai/apple-touch-icon.png",
      })
    ).toEqual({
      logoUrl: "https://framerusercontent.com/images/3S1XMF1Wu7nO2vBUopvF7ajENkY.png",
      secondaryLogoUrl: "https://zyg.ai/apple-touch-icon.png",
    });
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

  it("collects and searches grouped direction options", () => {
    const products: Product[] = [
      { name: "A", description: "x", category: "agent", categories: ["healthcare"] },
      { name: "B", description: "x", category: "agent", categories: ["robotics"] },
      { name: "C", description: "x", category: "voice", categories: ["healthcare"] },
    ];

    const options = collectDirectionOptions(products, "en-US");
    expect(options[0]).toMatchObject({ value: "agent", count: 2, label: "Agent" });
    expect(options[1]).toMatchObject({ value: "healthcare", count: 2 });

    const filtered = filterDirectionOptions(options, "health");
    expect(filtered).toHaveLength(1);
    expect(filtered[0]?.value).toBe("healthcare");
  });

  it("localizes product text fields with en-first fallback under en-US", () => {
    const product: Product = {
      name: "Localize",
      description: "中文描述",
      description_en: "English description",
      why_matters: "中文原因",
      why_matters_en: "English rationale",
      latest_news: "中文动态",
      latest_news_en: "English update",
    };

    expect(getLocalizedProductDescription(product, "en-US")).toBe("English description");
    expect(getLocalizedProductWhyMatters(product, "en-US")).toBe("English rationale");
    expect(getLocalizedProductLatestNews(product, "en-US")).toBe("English update");
  });

  it("returns empty localized fields under en-US when *_en fields are missing", () => {
    const product: Product = {
      name: "Fallback",
      description: "中文描述",
      why_matters: "中文原因",
      latest_news: "中文动态",
    };

    expect(getLocalizedProductDescription(product, "en-US")).toBe("");
    expect(getLocalizedProductWhyMatters(product, "en-US")).toBe("");
    expect(getLocalizedProductLatestNews(product, "en-US")).toBe("");
  });

  it("localizes blog text fields by locale with en fallback rules", () => {
    expect(
      getLocalizedBlogName(
        {
          name: "腾讯再推“养虾”新措施",
          name_en: "Tencent launches localized SkillHub",
        },
        "zh-CN"
      )
    ).toBe("腾讯再推“养虾”新措施");
    expect(
      getLocalizedBlogDescription(
        {
          description: "据界面新闻，腾讯发布中国本土优化技能社区。",
          description_en: "Tencent launched a localized AI skills hub.",
        },
        "en-US"
      )
    ).toBe("Tencent launched a localized AI skills hub.");
  });

  it("falls back to primary blog fields when *_en is missing under en-US", () => {
    expect(
      getLocalizedBlogName(
        {
          name: "中国 AI 新动态",
        },
        "en-US"
      )
    ).toBe("中国 AI 新动态");
    expect(
      getLocalizedBlogDescription(
        {
          description: "中文主字段描述",
        },
        "en-US"
      )
    ).toBe("中文主字段描述");
  });

  it("applies curated zh-CN overrides for mixed-language card copy", () => {
    const product: Product = {
      name: "Sakana AI",
      description: "日本発の自然にインスパイアされた基盤モデル開発企業。",
      why_matters: "Transformer論文の著者Llion Jones...",
    };

    expect(getLocalizedProductDescription(product, "zh-CN")).toContain("foundation model");
    expect(getLocalizedProductWhyMatters(product, "zh-CN")).toContain("Sovereign AI");
  });

  it("localizes country metadata labels for zh-CN cards", () => {
    const localized = getLocalizedCountryName(
      {
        code: "US",
        name: "United States",
        flag: "🇺🇸",
        display: "🇺🇸 United States",
        source: "explicit",
        unknown: false,
      },
      "zh-CN"
    );

    expect(localized).toBe("美国");
    expect(
      getLocalizedCountryName(
        {
          code: "UNKNOWN",
          name: "Unknown",
          flag: "",
          display: "Unknown",
          source: "unknown",
          unknown: true,
        },
        "zh-CN"
      )
    ).toBe("地区待补充");
  });

  it("applies curated zh-CN overrides for homepage english-only cards", () => {
    const product: Product = {
      name: "Ivee",
      description: "AI upskilling platform that trains employees on AI tools.",
      why_matters: "Raised $1M seed backed by Steven Bartlett.",
    };

    expect(getLocalizedProductDescription(product, "zh-CN")).toContain("AI upskilling");
    expect(getLocalizedProductWhyMatters(product, "zh-CN")).toContain("英国政府");
  });

  it("formats category labels by locale", () => {
    const product: Product = {
      name: "Category",
      description: "x",
      categories: ["hardware", "ai_chip", "other"],
    };

    expect(formatCategories(product, "zh-CN")).toBe("硬件 · AI芯片");
    expect(formatCategories(product, "en-US")).toBe("Hardware · AI Chips");
  });

  it("generates freshness labels from available dates", () => {
    const now = new Date("2026-02-10T12:00:00.000Z");

    expect(getFreshnessLabel({ name: "A", description: "x", discovered_at: "2026-02-09T12:00:00.000Z" }, now)).toBe("1天前");
    expect(getFreshnessLabel({ name: "B", description: "x", first_seen: "2026-02-10T08:00:00.000Z" }, now)).toBe("4小时前");
    expect(getFreshnessLabel({ name: "C", description: "x", published_at: "2026-02-10T11:30:00.000Z" }, now)).toBe("1小时内");
    expect(getFreshnessLabel({ name: "D", description: "x" }, now)).toBe("时间待补充");
  });

  it("formats relative and absolute dates consistently", () => {
    const now = new Date("2026-03-09T12:00:00.000Z");
    expect(formatRelativeDate("2026-03-08T12:00:00.000Z", "en-US", now)).toBe("1d ago");
    expect(formatRelativeDate("2026-02-28T12:00:00.000Z", "en-US", now)).toBe("1w ago");
    expect(formatAbsoluteDate("2026-03-08T12:00:00.000Z", "en-US")).toContain("2026");
  });

  it("maps score tone into ui tiers", () => {
    expect(getScoreTone(5)).toBe("5");
    expect(getScoreTone(4)).toBe("4");
    expect(getScoreTone(3)).toBe("3");
    expect(getScoreTone(2)).toBe("2");
    expect(getScoreTone(1)).toBe("0");
  });

  it("generates monogram fallback for latin, chinese and empty names", () => {
    expect(getMonogram("Weekly AI")).toBe("W");
    expect(getMonogram("星火助手")).toBe("星");
    expect(getMonogram("  ")).toBe("AI");
    expect(getMonogram(undefined)).toBe("AI");
  });
});
