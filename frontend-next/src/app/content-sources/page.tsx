import { pickLocaleText } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";

export default async function ContentSourcesPage() {
  const locale = await getRequestLocale();
  const t = (zh: string, en: string) => pickLocaleText(locale, { zh, en });

  return (
    <section className="section">
      <div className="section-header">
        <h1 className="section-title">{t("收录与来源说明", "Content Sources")}</h1>
        <p className="section-desc">
          {t("黑马雷达从公开资料中整理 AI 产品信息，帮你了解产品用途和最新进展。", "Darkhorse Radar aggregates publicly accessible AI industry updates and organizes them into structured summaries.")}
        </p>
      </div>

      <article className="detail-card">
        <div className="detail-block">
          <h2 className="detail-block__title">{t("黑马和潜力股怎么选？", "How we select products")}</h2>
          <p className="detail-block__content">{t(
            "我们关注用途明确、有新意的早期 AI 产品，筛选时会检查官网和来源，排除待核实记录及已经成名的产品。黑马指数为 4–5 分的归入「黑马」，2–3 分的归入「潜力股」。这个分数衡量产品的发现潜力，不代表实际使用效果。",
            "We look for AI products with a concrete use case and a distinct approach. Recommendations require website and source links; pending verification and established industry leaders are excluded. Scores of 4–5 indicate dark horses; 2–3 indicate rising stars. These measure discovery potential, not tested product quality."
          )}</p>
        </div>
        <div className="detail-block">
          <h2 className="detail-block__title">{t("收录日期代表什么？", "Reading the dates")}</h2>
          <p className="detail-block__content">{t(
            "收录日期是产品进入本站的时间，不是产品发布日期。近期没有新收录时，页面会显示往期黑马。资讯有各自的发布时间，可以通过原文链接查看完整信息。",
            "Discovery dates show when a record entered our catalog, not when the product launched. The recent-discovery window is five days; older selections are labeled as archive material. News synchronization and product discovery have separate timestamps. Follow the source to check the event date and original claims."
          )}</p>
        </div>
        <div className="detail-block">
          <h2 className="detail-block__title">{t("主要来源", "Primary sources")}</h2>
          <p className="detail-block__content">
            {t(
              "产品官网、Hacker News、Product Hunt、YouTube、X、Reddit，以及科技媒体的公开报道。",
              "Includes but is not limited to: Hacker News, Product Hunt, YouTube, X, Reddit, technology media RSS, and public official announcements."
            )}
          </p>
        </div>

        <div className="detail-block">
          <h2 className="detail-block__title">{t("信息如何整理？", "Processing")}</h2>
          <p className="detail-block__content">
            {t(
              "系统自动收集资料、合并重复记录，并整理成便于阅读的产品简介。信息供了解行业和寻找产品时参考，不构成投资建议或商业承诺。",
              "Data is deduplicated, structured, and rewritten for readability through an automated pipeline. Content is for discovery reference only and does not constitute investment advice or commercial commitments."
            )}
          </p>
        </div>

        <div className="detail-block">
          <h2 className="detail-block__title">{t("反馈与更正", "Corrections")}</h2>
          <p className="detail-block__content">
            <a href="https://github.com/Junpapadiamond/weeklyai/issues/new" target="_blank" rel="noopener noreferrer">{t("提交内容更正，请附产品名称、来源链接及更正原因。", "Submit a correction with the product name, source link, and reason.")}</a>
          </p>
        </div>
      </article>
    </section>
  );
}
