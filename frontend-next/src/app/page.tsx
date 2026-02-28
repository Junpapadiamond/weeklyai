import { Suspense } from "react";
import { HomeDataSection } from "@/components/home/home-data-section";
import type { SiteLocale } from "@/lib/locale";
import { pickLocaleText } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";

function HomeSkeleton({ locale }: { locale: SiteLocale }) {
  return (
    <div className="section">
      <div className="loading-block">
        {pickLocaleText(locale, { zh: "正在加载首页数据...", en: "Loading homepage data..." })}
      </div>
    </div>
  );
}

export default async function HomePage() {
  const locale = await getRequestLocale();
  return (
    <Suspense fallback={<HomeSkeleton locale={locale} />}>
      <HomeDataSection />
    </Suspense>
  );
}
