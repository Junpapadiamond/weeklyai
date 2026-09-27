import { Suspense } from "react";
import { HomeDataSection } from "@/components/home/home-data-section";
import type { SiteLocale } from "@/lib/locale";
import { pickLocaleText } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";

function HomeSkeleton({ locale }: { locale: SiteLocale }) {
  return (
    <div className="section home-skeleton" role="status" aria-busy="true">
      <span className="sr-only">{pickLocaleText(locale, { zh: "正在加载首页数据...", en: "Loading homepage data..." })}</span>
      <div className="home-skeleton__hero" aria-hidden="true">
        <div className="home-skeleton__line" />
        <div className="home-skeleton__line home-skeleton__line--title" />
        <div className="home-skeleton__line home-skeleton__line--title" />
        <div className="home-skeleton__line" />
      </div>
      {[0, 1, 2].map((row) => <div className="home-skeleton__row" aria-hidden="true" key={row}><div className="home-skeleton__logo" /><div><div className="home-skeleton__line" /><div className="home-skeleton__line" /></div></div>)}
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
