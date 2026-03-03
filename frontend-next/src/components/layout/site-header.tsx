"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { usePathname } from "next/navigation";
import { Dice5, Heart, Flame, Newspaper, Search, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import type { SiteLocale } from "@/lib/locale";
import { countFavorites, openFavoritesPanel, subscribeFavorites } from "@/lib/favorites";
import { useSiteLocale } from "@/components/layout/locale-provider";

const ThemeToggle = dynamic(() => import("@/components/layout/theme-toggle").then((mod) => mod.ThemeToggle), {
  ssr: false,
});

export function SiteHeader() {
  const pathname = usePathname();
  const { locale, setLocale, t } = useSiteLocale();
  const [favoritesCount, setFavoritesCount] = useState(0);

  useEffect(() => {
    const sync = () => setFavoritesCount(countFavorites());
    sync();
    return subscribeFavorites(sync);
  }, []);

  const navItems = [
    { href: "/", label: t("黑马推荐", "Dark Horses"), icon: Flame },
    { href: "/discover", label: t("随机发现", "Discover"), icon: Dice5 },
    { href: "/blog", label: t("博客动态", "News"), icon: Newspaper },
    { href: "/search", label: t("搜索", "Search"), icon: Search },
  ];

  function applyLocale(nextLocale: SiteLocale) {
    setLocale(nextLocale);
  }

  return (
    <header className="navbar">
      <div className="nav-container">
        <Link href="/" className="logo" aria-label={t("WeeklyAI 首页", "WeeklyAI home")}>
          <span className="logo-icon">
            <Sparkles size={18} />
          </span>
          <span className="logo-text">WeeklyAI</span>
        </Link>

        <nav className="nav-links" aria-label={t("主导航", "Main navigation")}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link key={item.href} href={item.href} className={`nav-link ${isActive ? "active" : ""}`}>
                <span className="nav-icon">
                  <Icon size={16} />
                </span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="nav-actions">
          <div className="locale-switcher" role="group" aria-label={t("切换语言", "Switch language")}>
            <button
              type="button"
              className={`locale-switcher__btn ${locale === "zh-CN" ? "active" : ""}`}
              onClick={() => applyLocale("zh-CN")}
              aria-pressed={locale === "zh-CN"}
            >
              中文
            </button>
            <button
              type="button"
              className={`locale-switcher__btn ${locale === "en-US" ? "active" : ""}`}
              onClick={() => applyLocale("en-US")}
              aria-pressed={locale === "en-US"}
            >
              EN
            </button>
          </div>
          <button
            className="nav-favorites"
            type="button"
            onClick={() => openFavoritesPanel("product")}
            aria-label={t("打开收藏夹", "Open favorites")}
          >
            <Heart size={16} />
            <span>{t("收藏", "Favorites")} {favoritesCount}</span>
          </button>
          <ThemeToggle ariaLabel={t("切换主题", "Toggle theme")} />
        </div>
      </div>
    </header>
  );
}
