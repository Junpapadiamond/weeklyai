import Link from "next/link";
import { notFound } from "next/navigation";
import { ProductCard } from "@/components/product/product-card";
import { getProductById, getRelatedProducts } from "@/lib/api-client";
import { formatCategories, isValidWebsite, normalizeWebsite } from "@/lib/product-utils";

export const dynamic = "force-dynamic";

type ProductPageProps = {
  params: Promise<{ id: string }>;
};

export default async function ProductPage({ params }: ProductPageProps) {
  const { id } = await params;
  const decodedId = decodeURIComponent(id);

  const [product, related] = await Promise.all([
    getProductById(decodedId),
    getRelatedProducts(decodedId, 6),
  ]);

  if (!product) {
    notFound();
  }

  const website = normalizeWebsite(product.website);

  return (
    <section className="section product-detail-page">
      <div className="section-header">
        <h1 className="section-title">{product.name}</h1>
        <p className="section-desc">{formatCategories(product)}</p>
      </div>

      <article className="detail-card">
        <p className="detail-card__description">{product.description}</p>

        {product.why_matters ? (
          <div className="detail-card__why">
            <h2>为什么重要</h2>
            <p>{product.why_matters}</p>
          </div>
        ) : null}

        <div className="detail-card__grid">
          {product.dark_horse_index ? <div><strong>评分</strong><span>{product.dark_horse_index} 分</span></div> : null}
          {product.funding_total ? <div><strong>融资</strong><span>{product.funding_total}</span></div> : null}
          {product.region ? <div><strong>地区</strong><span>{product.region}</span></div> : null}
          {product.latest_news ? <div><strong>最新动态</strong><span>{product.latest_news}</span></div> : null}
          {product.source ? <div><strong>来源</strong><span>{product.source}</span></div> : null}
        </div>

        <div className="detail-card__actions">
          <Link href="/" className="link-btn">
            返回首页
          </Link>
          {isValidWebsite(website) ? (
            <a className="link-btn link-btn--primary" href={website} target="_blank" rel="noopener noreferrer">
              访问官网
            </a>
          ) : (
            <span className="pending-tag">官网待验证</span>
          )}
        </div>
      </article>

      <section className="section">
        <div className="section-header">
          <h2 className="section-title">相关产品</h2>
        </div>

        <div className="products-grid">
          {related.length ? related.map((item) => <ProductCard key={item._id || item.name} product={item} compact />) : null}
        </div>

        {!related.length ? (
          <div className="empty-state">
            <p className="empty-state-text">暂无相关产品。</p>
          </div>
        ) : null}
      </section>
    </section>
  );
}
