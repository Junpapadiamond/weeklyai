import { pickLocaleText } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";

export default async function ContentSourcesPage() {
  const locale = await getRequestLocale();
  const t = (zh: string, en: string) => pickLocaleText(locale, { zh, en });

  return (
    <section className="section">
      <div className="section-header">
        <h1 className="section-title">{t("内容来源说明", "Content Sources")}</h1>
        <p className="section-desc">
          {t("WeeklyAI 聚合公开可访问的 AI 行业动态，并进行结构化摘要。", "WeeklyAI aggregates publicly accessible AI industry updates and organizes them into structured summaries.")}
        </p>
      </div>

      <article className="detail-card">
        <div className="detail-block">
          <h2 className="detail-block__title">{t("如何筛选", "How we select products")}</h2>
          <p className="detail-block__content">{t(
            "推荐聚焦用途明确、具有差异化的 AI 产品。推荐列表需要官网及来源链接，并排除待核实记录与已成名的行业领军产品。4–5 分为黑马，2–3 分为潜力股；这是发现价值评分，不是实测质量评分。",
            "We look for AI products with a concrete use case and a distinct approach. Recommendations require website and source links; pending verification and established industry leaders are excluded. Scores of 4–5 indicate dark horses; 2–3 indicate rising stars. These measure discovery potential, not tested product quality."
          )}</p>
        </div>
        <div className="detail-block">
          <h2 className="detail-block__title">{t("如何阅读日期", "Reading the dates")}</h2>
          <p className="detail-block__content">{t(
            "收录日期表示我们发现该记录的时间，不代表产品发布日期。近期发现窗口为 5 天；没有近期记录时会明确显示历史档案。新闻同步时间与产品收录时间分开计算。请沿来源链接核对事件日期与原始信息。",
            "Discovery dates show when a record entered our catalog, not when the product launched. The recent-discovery window is five days; older selections are labeled as archive material. News synchronization and product discovery have separate timestamps. Follow the source to check the event date and original claims."
          )}</p>
        </div>
        <div className="detail-block">
          <h2 className="detail-block__title">{t("主要来源", "Primary sources")}</h2>
          <p className="detail-block__content">
            {t(
              "包含但不限于：Hacker News、Product Hunt、YouTube、X、Reddit、科技媒体 RSS 与公开官网发布内容。",
              "Includes but is not limited to: Hacker News, Product Hunt, YouTube, X, Reddit, technology media RSS, and public official announcements."
            )}
          </p>
        </div>

        <div className="detail-block">
          <h2 className="detail-block__title">{t("处理方式", "Processing")}</h2>
          <p className="detail-block__content">
            {t(
              "系统通过自动化流程进行去重、结构化和可读性重写。信息仅作行业发现参考，不构成投资或商业承诺。",
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
