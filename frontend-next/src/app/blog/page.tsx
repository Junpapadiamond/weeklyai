import type { Metadata } from "next";
import { Suspense } from "react";
import { BlogDataSection } from "@/components/blog/blog-data-section";
import { pickLocaleText } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";

export async function generateMetadata(): Promise<Metadata> {
  const locale = await getRequestLocale();
  return {
    title: pickLocaleText(locale, { zh: "AI 资讯", en: "News" }),
  };
}

export default async function BlogPage() {
  const locale = await getRequestLocale();
  return (
    <Suspense
      fallback={
        <div className="section">
          <div className="loading-block">{pickLocaleText(locale, { zh: "正在加载资讯…", en: "Loading news feed..." })}</div>
        </div>
      }
    >
      <BlogDataSection />
    </Suspense>
  );
}
