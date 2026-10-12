import { readFileSync, readdirSync } from "node:fs";
import { createElement, type ReactElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import { DemoPlayer } from "@/components/demo/demo-player";
import { DemoWidget } from "@/components/demo/demo-widgets";
import { DemoSpecSchema } from "../demo-schema";

const language = vi.hoisted(() => ({ locale: "en-US" }));
vi.mock("@/components/layout/locale-provider", () => ({
  useSiteLocale: () => ({ locale: language.locale, t: (zh: string, en: string) => language.locale === "en-US" ? en : zh }),
}));

const directory = "../backend/data/demos/published";
const specs = readdirSync(directory).filter(name => name.endsWith(".json"))
  .map(name => DemoSpecSchema.parse(JSON.parse(readFileSync(`${directory}/${name}`, "utf8"))));

function render(element: ReactElement, locale: "en-US" | "zh-CN" = "en-US") {
  language.locale = locale;
  return renderToStaticMarkup(element);
}

describe("legacy examples present inspectable content without a wizard", () => {
  it.each(specs.map(spec => [spec.product_name, spec] as const))("opens %s with a visible artifact and optional context", (_, spec) => {
    const html = render(createElement(DemoPlayer, { spec }));
    expect(html).toContain('aria-label="Example sections"');
    expect(html).toContain('aria-pressed="true"');
    expect(html).not.toContain(' disabled=""');
    expect(html).not.toContain('type="checkbox"');
    expect(html).not.toContain("48 hours");
    expect(html).not.toContain('class="demo-badge');
    expect(html).not.toContain(' open=""');
    const artifact = render(createElement(DemoWidget, { widget: spec.steps[0].widget, evidence: spec.evidence }));
    expect(html).toContain(artifact);
    expect(html.indexOf(artifact)).toBeLessThan(html.indexOf("About this example"));
    expect(html).toContain("Sources and provenance");
    for (const source of spec.evidence) expect(html).toContain(source.source_url);
    if (spec.tier === "simulation") expect(html).toContain("Independent fictional example · Not vendor output");
    else if (spec.tier === "concept") expect(html).toContain("Independent concept example · No device operation");
    else expect(html).toContain("Independent prepared example · No live execution");
  });

  it.each(["cached", "live"] as const)("shows the first prepared answer without claiming execution for mode=%s", mode => {
    const widget = specs.flatMap(spec => spec.steps).find(step => step.widget.type === "query_response")?.widget;
    if (!widget || widget.type !== "query_response") throw new Error("Missing query example fixture");
    for (const locale of ["en-US", "zh-CN"] as const) {
      const html = render(createElement(DemoWidget, { widget: { ...widget, mode, endpoint_id: "test-only" }, evidence: [] }), locale);
      const copy = locale === "en-US" ? widget.presets[0].response.en : widget.presets[0].response.zh;
      expect(html).toContain(renderToStaticMarkup(createElement("p", null, copy)));
      expect(html).toContain(locale === "en-US" ? "Prepared response · No query executed" : "预设回答示例 · 未执行查询");
      expect(html).not.toContain("Live result");
      expect(html).not.toContain("实时结果");
      expect(html).not.toContain('role="tab"');
    }
  });

  it("renders every stored widget and keeps sampled dialogue visibly illustrative", () => {
    for (const spec of specs) for (const section of spec.steps) {
      const html = render(createElement(DemoWidget, { widget: section.widget, evidence: spec.evidence }));
      expect(html.length).toBeGreaterThan(100);
      if (section.widget.type === "transcript") {
        expect(html).toContain("Example question");
        expect(html).toContain("Example response");
        expect(html).toContain("Show more dialogue");
      }
      if (section.widget.type === "param_dial") expect(html).toContain("Values below are prepared examples");
    }
  });

  it("does not turn a vendor-supplied key into an execution claim", () => {
    const spec = { ...specs.find(item => item.tier === "sandbox")!, vendor_status: "key_supplied" as const };
    const html = render(createElement(DemoPlayer, { spec }));
    expect(html).toContain("without calling that sandbox");
    expect(html).not.toContain("supplied the sandbox key used here");
  });

  it("shows a screenshot tour with one annotation and named keyboard controls", () => {
    const html = render(createElement(DemoWidget, { evidence: [], widget: {
      type: "hotspot_shot", shot_url: "https://example.com/screenshot.png",
      hotspots: [
        { x: 20, y: 30, note: { zh: "输入研究问题", en: "Enter a research question" } },
        { x: 65, y: 70, note: { zh: "查看参考来源", en: "Inspect supporting sources" } },
      ],
    } }));
    expect(html).toContain('aria-label="Choose an annotation"');
    expect(html).toContain('aria-pressed="true"');
    expect(html).toContain('aria-label="Inspect supporting sources"');
    expect(html).toContain('class="demo-hotspot__note" aria-live="polite">Enter a research question</p>');
  });
});
