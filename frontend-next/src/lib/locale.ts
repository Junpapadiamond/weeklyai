export const LOCALE_STORAGE_KEY = "weeklyai_locale";
export const LOCALE_COOKIE_KEY = "weeklyai_locale";

export const SUPPORTED_LOCALES = ["zh-CN", "en-US"] as const;
export type SiteLocale = (typeof SUPPORTED_LOCALES)[number];

export const DEFAULT_LOCALE: SiteLocale = "zh-CN";

export function normalizeLocale(value: string | null | undefined): SiteLocale {
  if (value === "en-US" || value === "zh-CN") return value;
  return DEFAULT_LOCALE;
}

export function pickLocaleText(locale: SiteLocale, text: { zh: string; en: string }): string {
  return locale === "en-US" ? text.en : text.zh;
}
