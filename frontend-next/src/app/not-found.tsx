import Link from "next/link";

export default function NotFound() {
  return (
    <section className="section">
      <div className="section-header">
        <h1 className="section-title">页面未找到</h1>
        <p className="section-desc">链接可能已失效，或者产品已被移除。</p>
      </div>
      <Link href="/" className="link-btn link-btn--primary">
        返回首页
      </Link>
    </section>
  );
}
