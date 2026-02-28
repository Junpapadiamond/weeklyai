import { Suspense } from "react";
import { DiscoverDataSection } from "@/components/discover/discover-data-section";
import type { SiteLocale } from "@/lib/locale";
import { pickLocaleText } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";

function DiscoverSkeleton({ locale }: { locale: SiteLocale }) {
  return (
    <section className="section">
      <div className="loading-block">
        {pickLocaleText(locale, { zh: "加载随机发现中...", en: "Loading discovery deck..." })}
      </div>
    </section>
  );
}

export default async function DiscoverPage() {
  const locale = await getRequestLocale();
  return (
    <Suspense fallback={<DiscoverSkeleton locale={locale} />}>
      <DiscoverDataSection />
    </Suspense>
  );
}
