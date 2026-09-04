import Link from "next/link";
import { notFound } from "next/navigation";
import { WebsiteScreenshot } from "@/components/common/website-screenshot";
import { ProductCard } from "@/components/product/product-card";
import { SmartLogo } from "@/components/common/smart-logo";
import { FavoriteButton } from "@/components/favorites/favorite-button";
import { getProductById, getRelatedProducts } from "@/lib/api-client";
import { pickLocaleText, type SiteLocale } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";
import {
  formatCategories,
  cleanDescription,
  getProductWebsiteSearchUrl,
  getLocalizedProductDescription,
  getLocalizedProductLatestNews,
  getLocalizedProductWhyMatters,
  getProductScore,
  isPlaceholderValue,
  isValidWebsite,
  normalizeWebsite,
  resolveProductLogoSources,
  resolveProductCountry,
  getLocalizedCountryName,
} from "@/lib/product-utils";

export const dynamic = "force-dynamic";

type ProductPageProps = {
  params: Promise<{ id: string }>;
};

function formatScore(score: number, locale: SiteLocale): string {
  if (score <= 0) return locale === "en-US" ? "Unrated" : "待评";
  if (locale === "en-US") {
    return Number.isInteger(score) ? `${score}/5` : `${score.toFixed(1)}/5`;
  }
  return Number.isInteger(score) ? `${score}分` : `${score.toFixed(1)}分`;
}

function scoreBadgeClass(score: number): string {
  if (score >= 5) return "score-badge--5";
  if (score >= 4) return "score-badge--4";
  return "score-badge--3";
}

function formatDate(value?: string): string {
  if (!value) return "-";
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return "-";
  const yyyy = date.getUTCFullYear();
  const mm = String(date.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(date.getUTCDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export default async function ProductPage({ params }: ProductPageProps) {
  const locale = await getRequestLocale();
  const t = (zh: string, en: string) => pickLocaleText(locale, { zh, en });
  const { id } = await params;
  const decodedId = id;

  const [product, related] = await Promise.all([getProductById(decodedId), getRelatedProducts(decodedId, 10)]);

  if (!product) {
    notFound();
  }

  const website = normalizeWebsite(product.website);
  const score = getProductScore(product);
  const scoreLabel = formatScore(score, locale);
  const categoryLine = formatCategories(product, locale);
  const regionLine = getLocalizedCountryName(resolveProductCountry(product), locale);
  const description = cleanDescription(getLocalizedProductDescription(product, locale), locale);
  const funding = !isPlaceholderValue(product.funding_total) ? product.funding_total?.trim() : "-";
  const valuation = !isPlaceholderValue(product.valuation) ? product.valuation?.trim() : "-";
  const discoveredDate = formatDate(product.discovered_at || product.first_seen || product.published_at);
  const whyMatters = getLocalizedProductWhyMatters(product, locale) || t("研究摘要待补充", "Research note pending");
  const latestNews = getLocalizedProductLatestNews(product, locale) || t("暂无最新动态", "No recent updates yet");
  const websiteSearchUrl = getProductWebsiteSearchUrl(product.name, locale);
  const resolvedLogo = resolveProductLogoSources(product);

  return (
    <section className="section product-detail-page">
      <article className="detail-card detail-card--rich">
        <header className="detail-hero">
          <SmartLogo
            key={`${product._id || product.name}-${resolvedLogo.logoUrl}-${resolvedLogo.secondaryLogoUrl}-${product.website || ""}-${product.source_url || ""}`}
            className="detail-hero__logo"
            name={product.name}
            logoUrl={resolvedLogo.logoUrl}
            secondaryLogoUrl={resolvedLogo.secondaryLogoUrl}
            website={product.website}
            sourceUrl={product.source_url}
            trustPrimaryLogo
            size={128}
          />

          <div className="detail-hero__content">
            <div className="detail-hero__head">
              <h1 className="detail-hero__title">{product.name}</h1>
              {score >= 3 ? (
                <span className={`score-badge ${scoreBadgeClass(score)}`}>{scoreLabel}</span>
              ) : (
                <span className="product-badge">{scoreLabel}</span>
              )}
            </div>
            <p className="detail-hero__meta">
              {categoryLine}
              {regionLine ? ` · ${regionLine}` : ""}
            </p>
            <p className="detail-hero__description">{description}</p>
          </div>
        </header>
        {product.needs_verification ? <p className="section-desc">{t("这条记录尚待核实。请通过原始来源确认产品身份与数据后再使用。", "This record needs verification. Check the original source before relying on its identity or figures.")}</p> : null}

        <section className="detail-block">
          <h2 className="detail-block__title">{t("档案信息", "On record")}</h2>
          <div className="detail-metrics-grid">
            <div className="detail-metric">
              <span className="detail-metric__label">{t("融资记录", "Reported funding")}</span>
              <strong className="detail-metric__value">{funding || "-"}</strong>
            </div>
            <div className="detail-metric">
              <span className="detail-metric__label">{t("估值记录", "Reported valuation")}</span>
              <strong className="detail-metric__value">{valuation || "-"}</strong>
            </div>
            <div className="detail-metric">
              <span className="detail-metric__label">{t("收录日期", "Discovered")}</span>
              <strong className="detail-metric__value">{discoveredDate}</strong>
            </div>
          </div>
        </section>

        <section className="detail-block">
          <h2 className="detail-block__title">{t("值得研究的原因", "Why look closer")}</h2>
          <p className="detail-block__content">{whyMatters}</p>
        </section>

        <section className="detail-block">
          <h2 className="detail-block__title">{t("记录中的动态", "Recorded update")}</h2>
          <p className="detail-block__content">{latestNews}</p>
        </section>

        <section className="detail-block">
          <h2 className="detail-block__title">{t("网站预览", "Website preview")}</h2>
          <WebsiteScreenshot
            className="detail-site-shot"
            website={product.website}
            name={product.name}
            logoUrl={resolvedLogo.logoUrl}
            secondaryLogoUrl={resolvedLogo.secondaryLogoUrl}
            sourceUrl={product.source_url}
            trustPrimaryLogo
            category={product.category}
            categories={product.categories}
            isHardware={product.is_hardware}
            alt={`${product.name} ${t("官网截图", "website screenshot")}`}
            logoSize={84}
          />
        </section>

        <footer className="detail-actions">
          <FavoriteButton product={product} />
          {product.source_url && isValidWebsite(product.source_url) ? <a className="link-btn" href={product.source_url} target="_blank" rel="noopener noreferrer">{t("阅读原始来源", "Read original source")}</a> : null}
          {isValidWebsite(website) && !product.needs_verification ? (
            <a className="link-btn link-btn--primary" href={website} target="_blank" rel="noopener noreferrer">
              {t("访问官网", "Visit website")}
            </a>
          ) : (
            <a
              className="pending-tag pending-tag--action"
              href={websiteSearchUrl}
              target="_blank"
              rel="noopener noreferrer"
              title={t("点击跳转 Google 搜索官网", "Open Google search for the official website")}
            >
              {t("官网待验证", "Website pending verification")}
            </a>
          )}
          <Link href="/" className="link-btn">
            {t("返回首页", "Back to home")}
          </Link>
        </footer>
      </article>

      <section className="detail-related">
        <div className="section-header">
          <h2 className="section-title">{t("继续研究", "Continue exploring")}</h2>
        </div>

        {related.length ? (
          <div className="detail-related__scroll">
            {related.map((item) => (
              <ProductCard key={item._id || item.name} product={item} compact />
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p className="empty-state-text">{t("暂无相关产品。", "No related products yet.")}</p>
          </div>
        )}
      </section>
    </section>
  );
}
