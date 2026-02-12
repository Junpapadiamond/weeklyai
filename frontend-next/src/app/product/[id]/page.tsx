import Link from "next/link";
import { notFound } from "next/navigation";
import { WebsiteScreenshot } from "@/components/common/website-screenshot";
import { ProductCard } from "@/components/product/product-card";
import { SmartLogo } from "@/components/common/smart-logo";
import { getProductById, getRelatedProducts } from "@/lib/api-client";
import {
  formatCategories,
  getProductScore,
  isPlaceholderValue,
  isValidWebsite,
  normalizeWebsite,
} from "@/lib/product-utils";

export const dynamic = "force-dynamic";

type ProductPageProps = {
  params: Promise<{ id: string }>;
};

function formatScore(score: number): string {
  if (score <= 0) return "待评";
  return Number.isInteger(score) ? `${score}分` : `${score.toFixed(1)}分`;
}

function formatDate(value?: string): string {
  if (!value) return "-";
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return "-";
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export default async function ProductPage({ params }: ProductPageProps) {
  const { id } = await params;
  const decodedId = decodeURIComponent(id);

  const [product, related] = await Promise.all([getProductById(decodedId), getRelatedProducts(decodedId, 10)]);

  if (!product) {
    notFound();
  }

  const website = normalizeWebsite(product.website);
  const score = getProductScore(product);
  const scoreLabel = formatScore(score);
  const categoryLine = formatCategories(product);
  const regionLine = product.region?.trim();
  const description = product.description?.trim() || "描述待补充";
  const funding = !isPlaceholderValue(product.funding_total) ? product.funding_total?.trim() : "-";
  const valuation = !isPlaceholderValue(product.valuation) ? product.valuation?.trim() : "-";
  const discoveredDate = formatDate(product.discovered_at || product.first_seen || product.published_at);
  const whyMatters = product.why_matters?.trim() || "why_matters 待补充";
  const latestNews = product.latest_news?.trim() || "暂无最新动态";

  return (
    <section className="section product-detail-page">
      <article className="detail-card detail-card--rich">
        <header className="detail-hero">
          <SmartLogo
            key={`${product._id || product.name}-${product.logo_url || ""}-${product.logo || ""}-${product.website || ""}-${product.source_url || ""}`}
            className="detail-hero__logo"
            name={product.name}
            logoUrl={product.logo_url}
            secondaryLogoUrl={product.logo}
            website={product.website}
            sourceUrl={product.source_url}
            size={128}
          />

          <div className="detail-hero__content">
            <div className="detail-hero__head">
              <h1 className="detail-hero__title">{product.name}</h1>
              {score >= 4 ? (
                <span className="score-badge score-badge--5">{scoreLabel}</span>
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

        <section className="detail-block">
          <h2 className="detail-block__title">📊 关键指标</h2>
          <div className="detail-metrics-grid">
            <div className="detail-metric">
              <span className="detail-metric__label">💰 融资</span>
              <strong className="detail-metric__value">{funding || "-"}</strong>
            </div>
            <div className="detail-metric">
              <span className="detail-metric__label">🏷️ 估值</span>
              <strong className="detail-metric__value">{valuation || "-"}</strong>
            </div>
            <div className="detail-metric">
              <span className="detail-metric__label">📅 发现日期</span>
              <strong className="detail-metric__value">{discoveredDate}</strong>
            </div>
          </div>
        </section>

        <section className="detail-block">
          <h2 className="detail-block__title">💡 为什么重要</h2>
          <p className="detail-block__content">{whyMatters}</p>
        </section>

        <section className="detail-block">
          <h2 className="detail-block__title">📰 最新动态</h2>
          <p className="detail-block__content">{latestNews}</p>
        </section>

        <section className="detail-block">
          <h2 className="detail-block__title">🖼️ 产品截图</h2>
          <WebsiteScreenshot
            className="detail-site-shot"
            website={product.website}
            name={product.name}
            logoUrl={product.logo_url}
            secondaryLogoUrl={product.logo}
            sourceUrl={product.source_url}
            alt={`${product.name} 官网截图`}
            logoSize={84}
          />
        </section>

        <footer className="detail-actions">
          {isValidWebsite(website) ? (
            <a className="link-btn link-btn--primary" href={website} target="_blank" rel="noopener noreferrer">
              访问官网
            </a>
          ) : (
            <span className="pending-tag">官网待验证</span>
          )}
          <Link href="/" className="link-btn">
            返回首页
          </Link>
        </footer>
      </article>

      <section className="detail-related">
        <div className="section-header">
          <h2 className="section-title">🔗 相关产品</h2>
        </div>

        {related.length ? (
          <div className="detail-related__scroll">
            {related.map((item) => (
              <ProductCard key={item._id || item.name} product={item} compact />
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p className="empty-state-text">暂无相关产品。</p>
          </div>
        )}
      </section>
    </section>
  );
}
