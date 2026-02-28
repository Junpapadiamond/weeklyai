import { pickLocaleText } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";

export default async function Loading() {
  const locale = await getRequestLocale();
  return (
    <section className="section">
      <div className="loading-block">{pickLocaleText(locale, { zh: "页面加载中...", en: "Loading page..." })}</div>
    </section>
  );
}
