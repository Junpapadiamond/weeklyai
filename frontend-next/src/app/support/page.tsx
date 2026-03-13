import { pickLocaleText } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";

export default async function SupportPage() {
  const locale = await getRequestLocale();
  const t = (zh: string, en: string) => pickLocaleText(locale, { zh, en });

  return (
    <section className="section">
      <div className="section-header">
        <h1 className="section-title">{t("支持与反馈", "Support")}</h1>
        <p className="section-desc">
          {t("如遇到数据异常、功能问题或审核补充需要，可通过以下方式联系。", "For data issues, feature bugs, or review follow-ups, contact us below.")}
        </p>
      </div>

      <article className="detail-card">
        <div className="detail-block">
          <h2 className="detail-block__title">{t("联系邮箱", "Contact email")}</h2>
          <p className="detail-block__content">support@weeklyai.com</p>
        </div>
        <div className="detail-block">
          <h2 className="detail-block__title">{t("工作时间", "Support window")}</h2>
          <p className="detail-block__content">
            {t("周一至周五 10:00 - 18:00（UTC+8）", "Monday to Friday, 10:00 - 18:00 (UTC+8)")}
          </p>
        </div>
      </article>
    </section>
  );
}
