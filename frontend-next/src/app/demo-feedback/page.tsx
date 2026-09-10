import { pickLocaleText } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";

export const metadata = {
  title: "Demo corrections",
  description: "Report an inaccurate interactive demo, or ask for one to be removed.",
};

/**
 * Required before any Tier 2 (simulation) demo is published. The labelling
 * contract commits to a 48-hour turnaround and to removal on request, so the
 * address has to exist and be findable from inside every demo.
 */
export default async function DemoFeedbackPage() {
  const locale = await getRequestLocale();
  const t = (zh: string, en: string) => pickLocaleText(locale, { zh, en });

  return (
    <section className="section">
      <div className="section-header">
        <h1 className="section-title">{t("演示纠错与下架", "Demo corrections and removal")}</h1>
        <p className="section-desc">
          {t(
            "交互演示由 WeeklyAI 独立制作，未获相关产品方背书。如果内容有误，或你希望它下架，我们会处理。",
            "Interactive demos are built independently by WeeklyAI and are not endorsed by the products they describe. If something is wrong, or you want a demo taken down, we will act on it."
          )}
        </p>
      </div>

      <article className="detail-card">
        <div className="detail-block">
          <h2 className="detail-block__title">{t("联系方式", "How to reach us")}</h2>
          <p className="detail-block__content">
            support@weeklyai.com
            <br />
            {t(
              "请附上演示链接，并说明哪一处不准确。",
              "Include the demo link and say which part is inaccurate."
            )}
          </p>
        </div>

        <div className="detail-block">
          <h2 className="detail-block__title">{t("我们的承诺", "What we commit to")}</h2>
          <p className="detail-block__content">
            {t(
              "48 小时内更正或下架，不作争辩。产品方要求下架的，直接下架。",
              "Corrected or removed within 48 hours, without argument. If the product's team asks for removal, it comes down."
            )}
          </p>
        </div>

        <div className="detail-block">
          <h2 className="detail-block__title">{t("演示是怎么标注的", "How demos are labelled")}</h2>
          <p className="detail-block__content">
            {t(
              "「示意性演示」表示这是对产品所做工作的重构，不是真实界面，也不使用产品方的 Logo、配色或界面元素。「概念解读」表示这是对产品所处位置的独立解读，不涉及界面。演示中的每个数字，要么标注来源，要么标为示例数据。",
              "“Illustrative reconstruction” means it recreates the job a product does, not its real interface, and uses none of the product's logo, colors or UI. “Concept explainer” means an independent explanation of where a product sits, with no interface claim at all. Every figure in a demo either cites a source or is marked as example data."
            )}
          </p>
        </div>

        <div className="detail-block">
          <h2 className="detail-block__title">{t("评分是独立的", "Scoring is independent")}</h2>
          <p className="detail-block__content">
            {t(
              "演示与评分互不影响。产品方提供 API 密钥或帮我们更正内容，只会提升演示的形式，不会改变评分——这一点由代码保证，演示流水线没有写入评分字段的权限。",
              "Demos and scoring do not affect one another. A product team supplying an API key or correcting a demo can improve the demo's format but never its score — enforced in code, since the demo pipeline has no write access to scoring fields."
            )}
          </p>
        </div>
      </article>
    </section>
  );
}
