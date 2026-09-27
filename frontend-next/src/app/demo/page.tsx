import type { Metadata } from "next";
import { DemoGallery } from "@/components/demo/demo-gallery";
import { pickLocaleText } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";

export async function generateMetadata(): Promise<Metadata> {
  const locale = await getRequestLocale();
  return {
    title: pickLocaleText(locale, { zh: "产品演示", en: "Product demos" }),
    description: pickLocaleText(locale, {
      zh: "用交互示例了解 AI 产品的使用流程。演示根据公开资料制作，实际功能以官网为准。",
      en: "Explore illustrative AI product workflows based on public information. Check official product sites for actual functionality.",
    }),
  };
}

export default async function DemoPage({ searchParams }: { searchParams: Promise<{ filter?: string }> }) {
  const filter = (await searchParams).filter === "ready" ? "ready" : "all";
  return <DemoGallery key={filter} initialFilter={filter} />;
}
