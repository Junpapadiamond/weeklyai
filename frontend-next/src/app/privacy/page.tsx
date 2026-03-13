import { pickLocaleText } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";

export default async function PrivacyPage() {
  const locale = await getRequestLocale();
  const t = (zh: string, en: string) => pickLocaleText(locale, { zh, en });

  return (
    <section className="section">
      <div className="section-header">
        <h1 className="section-title">{t("隐私政策（摘要）", "Privacy Policy (Summary)")}</h1>
        <p className="section-desc">
          {t("本页面用于 App Store 提交与用户披露。完整条款可在法务版本中扩展。", "This page is provided for App Store disclosure and can be extended into a full legal policy.")}
        </p>
      </div>

      <article className="detail-card">
        <div className="detail-block">
          <h2 className="detail-block__title">{t("我们收集的数据", "Data we collect")}</h2>
          <p className="detail-block__content">
            {t(
              "应用不要求注册。仅在本地存储语言、主题与收藏列表。服务端会记录基础访问日志（如 IP、UA、请求时间）用于稳定性监控与限流。",
              "No account is required. The app stores language, theme, and favorites locally. Server access logs (IP, user-agent, request time) are used for reliability monitoring and rate limiting."
            )}
          </p>
        </div>

        <div className="detail-block">
          <h2 className="detail-block__title">{t("数据用途", "How data is used")}</h2>
          <p className="detail-block__content">
            {t(
              "仅用于提供产品发现内容、接口可用性监控、故障排查与防滥用控制，不用于广告个性化。",
              "Data is used to deliver discovery content, monitor API health, debug incidents, and prevent abuse. It is not used for personalized advertising."
            )}
          </p>
        </div>

        <div className="detail-block">
          <h2 className="detail-block__title">{t("联系我们", "Contact")}</h2>
          <p className="detail-block__content">support@weeklyai.com</p>
        </div>
      </article>
    </section>
  );
}
