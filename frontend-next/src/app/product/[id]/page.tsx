import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ArrowUpRight, Layers3, MapPinned, Sparkles, type LucideIcon } from "lucide-react";
import { WebsiteScreenshot } from "@/components/common/website-screenshot";
import { FavoriteButton } from "@/components/favorites/favorite-button";
import { ProductShareButton } from "@/components/product/product-share-button";
import { SmartLogo } from "@/components/common/smart-logo";
import { getProductById, getRelatedProducts } from "@/lib/api-client";
import { pickLocaleText, type SiteLocale } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";
import {
  cleanDescription,
  formatAbsoluteDate,
  formatCategories,
  formatRelativeDate,
  getLocalizedProductDescription,
  getLocalizedProductLatestNews,
  getLocalizedProductWhyMatters,
  getProductScore,
  getScoreBadgeClass,
  isPlaceholderValue,
  isValidWebsite,
  normalizeWebsite,
  resolveProductCountry,
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

export default async function ProductPage({ params }: ProductPageProps) {
  const locale = await getRequestLocale();
  const t = (zh: string, en: string) => pickLocaleText(locale, { zh, en });
  const { id } = await params;
  const decodedId = decodeURIComponent(id);

  const [product, related] = await Promise.all([getProductById(decodedId), getRelatedProducts(decodedId, 10)]);

  if (!product) {
    notFound();
  }

  const website = normalizeWebsite(product.website);
  const hasWebsite = isValidWebsite(website) && !product.needs_verification;
  const score = getProductScore(product);
  const scoreLabel = formatScore(score, locale);
  const categoryLine = formatCategories(product, locale);
  const region = resolveProductCountry(product);
  const description = cleanDescription(getLocalizedProductDescription(product, locale), locale);
  const funding = !isPlaceholderValue(product.funding_total) ? product.funding_total?.trim() : "";
  const valuation = !isPlaceholderValue(product.valuation) ? product.valuation?.trim() : "";
  const firstSeenValue = product.discovered_at || product.first_seen || product.published_at;
  const latestSignalValue = product.published_at || product.first_seen || product.discovered_at;
  const whyMatters = getLocalizedProductWhyMatters(product, locale) || t("why_matters 待补充", "Why this matters is pending");
  const latestNews = getLocalizedProductLatestNews(product, locale) || t("暂无最新动态", "No recent updates yet");
  const sourceLabel = String(product.source || "").trim();
  const railFacts = [
    categoryLine
      ? {
          icon: Layers3,
          label: t("方向", "Directions"),
          value: categoryLine,
        }
      : null,
    !region.unknown
      ? {
          icon: MapPinned,
          label: t("地区", "Region"),
          value: region.display,
        }
      : null,
    funding
      ? {
          icon: Sparkles,
          label: t("融资", "Funding"),
          value: funding,
        }
      : null,
    valuation
      ? {
          icon: Sparkles,
          label: t("估值", "Valuation"),
          value: valuation,
        }
      : null,
    firstSeenValue
      ? {
          icon: Sparkles,
          label: t("首次发现", "First seen"),
          value: formatRelativeDate(firstSeenValue, locale),
          title: formatAbsoluteDate(firstSeenValue, locale, { includeTime: true }),
        }
      : null,
    latestSignalValue && latestSignalValue !== firstSeenValue
      ? {
          icon: Sparkles,
          label: t("最近信号", "Latest signal"),
          value: formatRelativeDate(latestSignalValue, locale),
          title: formatAbsoluteDate(latestSignalValue, locale, { includeTime: true }),
        }
      : null,
    sourceLabel
      ? {
          icon: Sparkles,
          label: t("来源", "Source"),
          value: sourceLabel,
        }
      : null,
  ].filter(Boolean) as Array<{ icon: LucideIcon; label: string; value: string; title?: string }>;

  return (
    <section className="section product-detail-page">
      <article className="detail-shell detail-card detail-card--rich">
        <div className="detail-main">
          <header className="detail-hero detail-hero--split">
            <SmartLogo
              key={`${product._id || product.name}-${product.logo_url || ""}-${product.logo || ""}-${product.website || ""}-${product.source_url || ""}`}
              className="detail-hero__logo"
              name={product.name}
              logoUrl={product.logo_url}
              secondaryLogoUrl={product.logo}
              website={product.website}
              sourceUrl={product.source_url}
              size={128}
              loading="eager"
            />

            <div className="detail-hero__content">
              <p className="detail-hero__eyebrow">
                {sourceLabel ? `${t("来源", "Source")} · ${sourceLabel}` : t("AI 产品情报卡", "AI product briefing")}
              </p>
              <h1 className="detail-hero__title">{product.name}</h1>
              <p className="detail-hero__description">{description}</p>
            </div>
          </header>

          <section className="detail-block">
            <h2 className="detail-block__title">💡 {t("为什么重要", "Why It Matters")}</h2>
            <p className="detail-block__content">{whyMatters}</p>
          </section>

          {related.length ? (
            <section className="detail-inline-related">
              <div className="detail-inline-related__head">
                <h2 className="detail-block__title">🔗 {t("同赛道对比", "Related products")}</h2>
                <p>{t("快速建立这个产品在赛道中的位置感。", "Quickly place this product within its category.")}</p>
              </div>
              <div className="detail-inline-related__grid">
                {related.slice(0, 3).map((item) => {
                  const itemScore = getProductScore(item);
                  const itemScoreLabel = formatScore(itemScore, locale);
                  const itemId = encodeURIComponent(item._id || item.name);
                  return (
                    <Link key={item._id || item.name} href={`/product/${itemId}`} className="detail-inline-related__card">
                      <div className="detail-inline-related__card-head">
                        <h3>{item.name}</h3>
                        <span className={`score-badge ${getScoreBadgeClass(itemScore, "score")}`}>{itemScoreLabel}</span>
                      </div>
                      <p>{cleanDescription(getLocalizedProductDescription(item, locale), locale)}</p>
                    </Link>
                  );
                })}
              </div>
            </section>
          ) : null}

          <section className="detail-block">
            <h2 className="detail-block__title">📰 {t("最新动态", "Latest Update")}</h2>
            <p className="detail-block__content">{latestNews}</p>
          </section>
        </div>

        <aside className="detail-sidebar">
          <div className="detail-sidebar__panel">
            <div className="detail-sidebar__score">
              <span className={`score-badge ${getScoreBadgeClass(score, "score")}`}>{scoreLabel}</span>
              <p>{t("本页右侧集中展示信号强度、关键事实和常用操作。", "The right rail keeps the score, key facts, and actions in one place.")}</p>
            </div>

            <div className="detail-sidebar__facts">
              {railFacts.map((fact) => {
                const Icon = fact.icon;
                return (
                  <div className="detail-sidebar__fact" key={fact.label}>
                    <div className="detail-sidebar__fact-label">
                      <Icon size={14} />
                      <span>{fact.label}</span>
                    </div>
                    <strong className="detail-sidebar__fact-value" title={fact.title}>
                      {fact.value}
                    </strong>
                  </div>
                );
              })}
            </div>

            <div className="detail-actions detail-actions--stacked">
              <div className="detail-actions__row">
                <FavoriteButton product={product} size="md" showLabel />
                <ProductShareButton productName={product.name} />
              </div>

              <div className="detail-actions__row">
                {hasWebsite ? (
                  <a className="link-btn link-btn--primary" href={website} target="_blank" rel="noopener noreferrer">
                    <ArrowUpRight size={14} /> {t("访问官网", "Visit website")}
                  </a>
                ) : (
                  <span className="pending-tag">{t("官网待验证", "Website pending verification")}</span>
                )}
                <Link href="/" className="link-btn">
                  <ArrowLeft size={14} /> {t("返回首页", "Back to home")}
                </Link>
              </div>
            </div>

            <section className="detail-sidebar__shot">
              <div className="detail-sidebar__shot-head">
                <h2 className="detail-block__title">🖼️ {t("官网缩略图", "Website preview")}</h2>
                <p>{t("截图仅作参考，不抢正文注意力。", "The screenshot is secondary context, not the main story.")}</p>
              </div>

              {hasWebsite ? (
                <a href={website} target="_blank" rel="noopener noreferrer" className="detail-sidebar__shot-link">
                  <WebsiteScreenshot
                    className="detail-site-shot"
                    website={product.website}
                    name={product.name}
                    logoUrl={product.logo_url}
                    secondaryLogoUrl={product.logo}
                    sourceUrl={product.source_url}
                    category={product.category}
                    categories={product.categories}
                    isHardware={product.is_hardware}
                    alt={`${product.name} ${t("官网截图", "website screenshot")}`}
                    logoSize={84}
                  />
                </a>
              ) : (
                <div className="detail-sidebar__shot-empty">
                  <span className="pending-tag">{t("官网待验证", "Website pending verification")}</span>
                </div>
              )}
            </section>
          </div>
        </aside>
      </article>
    </section>
  );
}
