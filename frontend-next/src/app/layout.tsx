import type { Metadata, Viewport } from "next";
import { headers } from "next/headers";
import { JetBrains_Mono, Noto_Sans_SC, Plus_Jakarta_Sans } from "next/font/google";
import { LocaleProvider } from "@/components/layout/locale-provider";
import { PageShell } from "@/components/layout/page-shell";
import { isAppShellUserAgent } from "@/lib/app-shell";
import { pickLocaleText } from "@/lib/locale";
import { getRequestLocale } from "@/lib/locale-server";
import "./globals.css";
import "../styles/tokens.css";
import "../styles/base.css";
import "../styles/home.css";
import "../styles/chat.css";
import "../styles/briefing.css";
import "../styles/demo.css";
import "../styles/research.css";
import "../styles/brand.css";
import "../styles/chinese.css";

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

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://darkhorseradar.com";

export async function generateMetadata(): Promise<Metadata> {
  const locale = await getRequestLocale();
  const siteName = pickLocaleText(locale, { zh: "黑马雷达", en: "Darkhorse Radar" });
  const title = pickLocaleText(locale, {
    zh: "黑马雷达 · 发现 AI 新产品",
    en: "Darkhorse Radar — Early AI products, hands on",
  });
  const description = pickLocaleText(locale, {
    zh: "发现海内外 AI 新产品，按分类找工具、看产品亮点、浏览交互演示。收录智能体、编程、视频、AI 硬件等领域的黑马与潜力股。",
    en: "A radar for early AI products, built for product managers. Every pick links to its source, and most come with a hands-on demo you can try without signing up.",
  });

  return {
    metadataBase: new URL(SITE_URL),
    applicationName: siteName,
    title: {
      default: title,
      template: pickLocaleText(locale, { zh: "%s · 黑马雷达", en: "%s · Darkhorse Radar" }),
    },
    description,
    alternates: { canonical: "/" },
    openGraph: {
      type: "website",
      url: SITE_URL,
      siteName,
      locale: locale === "zh-CN" ? "zh_CN" : "en_US",
      title,
      description,
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
    },
  };
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const locale = await getRequestLocale();
  const requestHeaders = await headers();
  const appShell = isAppShellUserAgent(requestHeaders.get("user-agent"));

  return (
    <html lang={locale} suppressHydrationWarning data-scroll-behavior="smooth" data-app-shell={appShell ? "ios" : undefined}>
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
          <PageShell isAppShell={appShell}>{children}</PageShell>
        </LocaleProvider>
      </body>
    </html>
  );
}
