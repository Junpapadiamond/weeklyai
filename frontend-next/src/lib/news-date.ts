import type { SiteLocale } from "./locale";

/** SSR and browsers must format the same instant in the same display timezone. */
export function formatNewsDate(value: string | undefined, locale: SiteLocale): string {
  let normalized = value || "";
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(normalized) && !/(?:Z|[+-]\d{2}:?\d{2})$/i.test(normalized)) {
    normalized += "Z";
  }
  const date = new Date(normalized);
  if (!Number.isFinite(date.getTime())) return locale === "zh-CN" ? "时间待补充" : "Timestamp unavailable";
  const timeZone = locale === "zh-CN" ? "Asia/Shanghai" : "UTC";
  return `${date.toLocaleString(locale, {
    timeZone, month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
  })} ${locale === "zh-CN" ? "北京时间" : "UTC"}`;
}
