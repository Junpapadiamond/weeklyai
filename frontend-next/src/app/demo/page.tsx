import { Suspense } from "react";
import { DemoExplorer } from "@/components/demo/demo-explorer";
import { getWeeklyTop } from "@/lib/api-client";
import type { SiteLocale } from "@/lib/locale";
import { pickLocaleText } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Interactive demos",
  description: "See what an AI product does without signing up for it.",
};

function DemoSkeleton({ locale }: { locale: SiteLocale }) {
  return (
    <section className="section">
      <div className="loading-block">
        {pickLocaleText(locale, { zh: "加载产品中...", en: "Loading products..." })}
      </div>
    </section>
  );
}

async function DemoDataSection() {
  // The picker is meant to cover the catalog, not a shortlist: any product a
  // visitor can see elsewhere on the site should be selectable here.
  const products = await getWeeklyTop(0, "composite");
  return <DemoExplorer products={products} />;
}

export default async function DemoPage() {
  const locale = await getRequestLocale();
  return (
    <Suspense fallback={<DemoSkeleton locale={locale} />}>
      <DemoDataSection />
    </Suspense>
  );
}
