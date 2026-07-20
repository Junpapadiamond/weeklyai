import Link from "next/link";
import { notFound } from "next/navigation";
import { SmartLogo } from "@/components/common/smart-logo";
import { ProductBreakdown } from "@/components/today/product-breakdown";
import { ExperienceWidget } from "@/components/today/experience-widget";
import { getDailyFeatured } from "@/lib/api-client";
import { pickLocaleText, type SiteLocale } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";
import {
  cleanDescription,
  formatCategories,
  getLocalizedProductDescription,
  getLocalizedProductLatestNews,
  getLocalizedProductWhyMatters,
  getProductScore,
  isPlaceholderValue,
  resolveProductLogoSources,
} from "@/lib/product-utils";

export const dynamic = "force-dynamic";

function formatScore(score: number, locale: SiteLocale): string {
  if (score <= 0) return locale === "en-US" ? "Unrated" : "待评";
  if (locale === "en-US") return Number.isInteger(score) ? `${score}/5` : `${score.toFixed(1)}/5`;
  return Number.isInteger(score) ? `${score}分` : `${score.toFixed(1)}分`;
}

function scoreBadgeClass(score: number): string {
  if (score >= 5) return "score-badge--5";
  if (score >= 4) return "score-badge--4";
  return "score-badge--3";
}

export default async function TodayPage() {
  const locale = await getRequestLocale();
  const t = (zh: string, en: string) => pickLocaleText(locale, { zh, en });

  const product = await getDailyFeatured();
  if (!product) notFound();

  const score = getProductScore(product);
  const scoreLabel = formatScore(score, locale);
  const description = cleanDescription(getLocalizedProductDescription(product, locale), locale);
  const whyMatters = getLocalizedProductWhyMatters(product, locale) || t("why_matters 待补充", "Why this matters is pending");
  const latestNews = getLocalizedProductLatestNews(product, locale) || t("暂无最新动态", "No recent updates yet");
  const categoryLine = formatCategories(product, locale);
  const regionLine = product.region?.trim();
  const funding = !isPlaceholderValue(product.funding_total) ? product.funding_total?.trim() : undefined;
  const resolvedLogo = resolveProductLogoSources(product);
  const productDetailId = product._id || product.name;

  return (
    <main className="section today-page">
      <div className="today-eyebrow">
        <span className="today-eyebrow__badge">{t("每日一品", "Today's Pick")}</span>
        <span className="today-eyebrow__date">{new Date().toLocaleDateString(locale === "en-US" ? "en-US" : "zh-CN", { month: "long", day: "numeric" })}</span>
      </div>

      <article className="today-card">
        {/* Hero */}
        <header className="today-hero">
          <SmartLogo
            key={`today-${product._id || product.name}-${resolvedLogo.logoUrl}`}
            className="today-hero__logo"
            name={product.name}
            logoUrl={resolvedLogo.logoUrl}
            secondaryLogoUrl={resolvedLogo.secondaryLogoUrl}
            website={product.website}
            sourceUrl={product.source_url}
            trustPrimaryLogo
            size={80}
            loading="eager"
          />
          <div className="today-hero__content">
            <div className="today-hero__head">
              <h1 className="today-hero__title">{product.name}</h1>
              {score >= 3 && (
                <span className={`score-badge ${scoreBadgeClass(score)}`}>{scoreLabel}</span>
              )}
            </div>
            <p className="today-hero__meta">
              {categoryLine}
              {regionLine ? ` · ${regionLine}` : ""}
              {funding ? ` · ${funding}` : ""}
            </p>
            <p className="today-hero__description">{description}</p>
          </div>
        </header>

        {/* Why it matters */}
        <section className="today-block">
          <h2 className="today-section__title">💡 {t("为什么重要", "Why It Matters")}</h2>
          <p className="today-block__content">{whyMatters}</p>
        </section>

        {/* Breakdown — client component, uses locale from context */}
        <ProductBreakdown product={product} />

        {/* Try it now — client component */}
        <ExperienceWidget product={product} />

        {/* Latest news */}
        <section className="today-block">
          <h2 className="today-section__title">📰 {t("最新动态", "Latest Update")}</h2>
          <p className="today-block__content">{latestNews}</p>
        </section>

        {/* Footer actions */}
        <footer className="today-actions">
          {product.website && (
            <a
              href={product.website}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn--primary"
            >
              {t("访问官网", "Visit Website")}
            </a>
          )}
          <Link
            href={`/product/${encodeURIComponent(productDetailId)}`}
            className="btn btn--ghost"
          >
            {t("查看完整详情", "Full Product Details")}
          </Link>
          <Link href="/" className="btn btn--ghost">
            {t("返回首页", "Back to Home")}
          </Link>
        </footer>
      </article>
    </main>
  );
}
