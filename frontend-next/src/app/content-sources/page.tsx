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
            {t("如发现来源归因或内容存在问题，请联系 support@weeklyai.com。", "For attribution or content corrections, contact support@weeklyai.com.")}
          </p>
        </div>
      </article>
    </section>
  );
}
