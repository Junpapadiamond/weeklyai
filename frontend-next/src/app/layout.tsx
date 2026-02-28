import type { Metadata } from "next";
import { JetBrains_Mono, Noto_Sans_SC, Plus_Jakarta_Sans } from "next/font/google";
import { LocaleProvider } from "@/components/layout/locale-provider";
import { PageShell } from "@/components/layout/page-shell";
import { getRequestLocale } from "@/lib/locale-server";
import "./globals.css";
import "../styles/tokens.css";
import "../styles/base.css";
import "../styles/home.css";
import "../styles/chat.css";

const displayFont = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["400", "500", "600", "700"],
});

const bodyFont = Noto_Sans_SC({
  subsets: ["latin"],
  variable: "--font-cjk",
  weight: ["400", "500", "600", "700"],
});

const bodyLatinFont = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600", "700"],
});

const monoFont = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "WeeklyAI - Discover Rising AI Products",
  description: "Global AI product discovery and inspiration platform",
};

export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const locale = await getRequestLocale();
  return (
    <html lang={locale} suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function () {
                try {
                  var localeKey = "weeklyai_locale";
                  var localeStored = window.localStorage.getItem(localeKey);
                  var locale = localeStored === "zh-CN" || localeStored === "en-US" ? localeStored : "zh-CN";
                  document.documentElement.setAttribute("lang", locale);
                  document.cookie = "weeklyai_locale=" + locale + "; path=/; max-age=31536000; samesite=lax";

                  var key = "weeklyai_theme";
                  var stored = window.localStorage.getItem(key);
                  var next = stored === "dark" || stored === "light"
                    ? stored
                    : (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
                  document.documentElement.setAttribute("data-theme", next);
                } catch (_) {
                  document.documentElement.setAttribute("data-theme", "light");
                }
              })();
            `,
          }}
        />
      </head>
      <body className={`${displayFont.variable} ${bodyLatinFont.variable} ${bodyFont.variable} ${monoFont.variable}`}>
        <LocaleProvider initialLocale={locale}>
          <PageShell>{children}</PageShell>
        </LocaleProvider>
      </body>
    </html>
  );
}
