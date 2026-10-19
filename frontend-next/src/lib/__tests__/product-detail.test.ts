import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { expect, it, vi } from "vitest";
import { detailDate, detailValue } from "../product-detail";
import type { Product } from "@/types/api";

const language = vi.hoisted(() => ({ value: "zh-CN" }));
vi.mock("@/components/layout/locale-provider", () => ({ useSiteLocale: () => ({
  locale: language.value, t: (zh: string, en: string) => language.value === "en-US" ? en : zh,
}) }));
vi.mock("@/components/product/product-detail-example", () => ({ ProductDetailExample: () => createElement("div", { "data-example": "read-only" }) }));
vi.mock("@/components/common/smart-logo", () => ({ SmartLogo: () => null }));
vi.mock("@/components/product/product-card", () => ({ ProductCard: () => null }));
import { ProductDetail } from "@/components/product/product-detail";

const product: Product = { name: "pib.rocks", website: "https://pib.rocks", description: "可3D打印的开源人形机器人平台，提供完整构建计划。", description_en: "An open-source humanoid robotics platform with build plans.",
  is_hardware: true, dark_horse_index: 3, funding_total: "-", valuation: "unknown", discovered_at: "invalid", source_url: "https://example.org/report" };
const render = (data = product) => renderToStaticMarkup(createElement(ProductDetail, { product: data, related: [] }));

it("does not dedicate financing, valuation, or date slots to absent records", () => {
  language.value = "zh-CN";
  const html = render();
  expect(html).not.toContain("融资记录");
  expect(html).not.toContain("估值记录");
  expect(html).not.toContain("收录日期");
  expect(html).not.toContain("已记录动态");
  expect(html).toContain("查看原始来源");
  expect(html).toContain('data-example="read-only"');
});

it("withholds automatic examples and official links for unverified identities", () => {
  const html = render({ ...product, needs_verification: true });
  expect(html).toContain("尚待核实");
  expect(html).toContain("查找官网");
  expect(html).not.toContain('href="https://pib.rocks');
  expect(html).not.toContain("data-example");
  expect(html).toContain('href="https://example.org/report"');
});

it("renders detail labels and product copy from the current language together", () => {
  language.value = "en-US";
  const html = render({ ...product, funding_total: "$3M", discovered_at: "2026-10-15T23:00:00-04:00" });
  expect(html).toContain("Visit website");
  expect(html).toContain("Reported funding");
  expect(html).toContain("An open-source humanoid");
  expect(html).toContain("2026-10-16");
  expect(html).not.toContain("产品档案");
  language.value = "zh-CN";
});

it("keeps UTC record dates and suppresses placeholders without discarding known zero values", () => {
  expect(detailDate("not-a-date")).toBeNull();
  expect(detailValue(" — ")).toBeNull();
  expect(detailValue("N/A")).toBeNull();
  expect(detailValue("0")).toBe("0");
  expect(detailValue("  $38 million  ")).toBe("$38 million");
});
