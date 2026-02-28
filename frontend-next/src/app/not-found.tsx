import Link from "next/link";
import { pickLocaleText } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";

export default async function NotFound() {
  const locale = await getRequestLocale();
  return (
    <section className="section">
      <div className="section-header">
        <h1 className="section-title">{pickLocaleText(locale, { zh: "页面未找到", en: "Page not found" })}</h1>
        <p className="section-desc">
          {pickLocaleText(locale, {
            zh: "链接可能已失效，或者产品已被移除。",
            en: "The link may be invalid, or this product has been removed.",
          })}
        </p>
      </div>
      <Link href="/" className="link-btn link-btn--primary">
        {pickLocaleText(locale, { zh: "返回首页", en: "Back to home" })}
      </Link>
    </section>
  );
}
