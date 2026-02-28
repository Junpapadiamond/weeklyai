"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  DEFAULT_LOCALE,
  LOCALE_COOKIE_KEY,
  LOCALE_STORAGE_KEY,
  normalizeLocale,
  pickLocaleText,
  type SiteLocale,
} from "@/lib/locale";

type LocaleContextValue = {
  locale: SiteLocale;
  setLocale: (next: SiteLocale) => void;
  t: (zh: string, en: string) => string;
};

const LocaleContext = createContext<LocaleContextValue | null>(null);

type LocaleProviderProps = {
  initialLocale?: SiteLocale;
  children: ReactNode;
};

export function LocaleProvider({ initialLocale = DEFAULT_LOCALE, children }: LocaleProviderProps) {
  const [locale, setLocale] = useState<SiteLocale>(initialLocale);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(LOCALE_STORAGE_KEY);
      const normalized = normalizeLocale(stored);
      if (normalized !== locale) {
        setLocale(normalized);
      }
    } catch {
      // ignore localStorage access errors
    }
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
    try {
      window.localStorage.setItem(LOCALE_STORAGE_KEY, locale);
    } catch {
      // ignore localStorage access errors
    }
    document.cookie = `${LOCALE_COOKIE_KEY}=${locale}; path=/; max-age=31536000; samesite=lax`;
  }, [locale]);

  const t = useCallback((zh: string, en: string) => pickLocaleText(locale, { zh, en }), [locale]);
  const value = useMemo(() => ({ locale, setLocale, t }), [locale, setLocale, t]);

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useSiteLocale() {
  const context = useContext(LocaleContext);
  if (!context) {
    throw new Error("useSiteLocale must be used within LocaleProvider");
  }
  return context;
}
