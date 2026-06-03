"use client";

import { useSiteLocale } from "@/components/layout/locale-provider";
import type { Product } from "@/types/api";

type BreakdownItem = {
  icon: string;
  labelZh: string;
  labelEn: string;
  value: string | undefined;
};

type Props = {
  product: Product;
};

export function ProductBreakdown({ product }: Props) {
  const { t } = useSiteLocale();
  const bd = product.extra?.breakdown;

  if (!bd) return null;

  const items: BreakdownItem[] = [
    { icon: "💡", labelZh: "核心价值", labelEn: "Core Value", value: bd.core_value_proposition },
    { icon: "🔄", labelZh: "用户流程", labelEn: "User Workflow", value: bd.key_user_workflow },
    { icon: "✨", labelZh: "Aha 时刻", labelEn: "Aha Moment", value: bd.aha_moment },
    { icon: "👤", labelZh: "目标用户", labelEn: "Target Users", value: bd.target_users },
    { icon: "💰", labelZh: "商业模式", labelEn: "Business Model", value: bd.business_model },
    { icon: "🏰", labelZh: "竞争优势", labelEn: "Moat", value: bd.competitive_moat },
  ].filter((item) => item.value);

  if (items.length === 0) return null;

  return (
    <section className="today-breakdown">
      <h2 className="today-section__title">
        {t("产品洞察", "Product Breakdown")}
      </h2>
      <div className="today-breakdown__grid">
        {items.map((item) => (
          <div key={item.labelEn} className="today-breakdown__card">
            <span className="today-breakdown__icon">{item.icon}</span>
            <div className="today-breakdown__body">
              <span className="today-breakdown__label">{t(item.labelZh, item.labelEn)}</span>
              <p className="today-breakdown__value">{item.value}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
