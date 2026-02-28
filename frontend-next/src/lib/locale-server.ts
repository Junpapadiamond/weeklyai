import { cookies } from "next/headers";
import { DEFAULT_LOCALE, LOCALE_COOKIE_KEY, normalizeLocale, type SiteLocale } from "@/lib/locale";

export async function getRequestLocale(): Promise<SiteLocale> {
  try {
    const cookieStore = await cookies();
    const raw = cookieStore.get(LOCALE_COOKIE_KEY)?.value;
    return normalizeLocale(raw);
  } catch {
    return DEFAULT_LOCALE;
  }
}
