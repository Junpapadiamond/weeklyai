"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { usePathname } from "next/navigation";
import { Shuffle, BookmarkSimple, Binoculars, MagnifyingGlass, PlayCircle } from "@phosphor-icons/react";
import { useEffect, useState } from "react";
import { HorseMark } from "@/components/brand/horse-mark";
import type { SiteLocale } from "@/lib/locale";
import { ChatBar } from "@/components/chat/chat-bar";
import { countFavorites, openFavoritesPanel, subscribeFavorites } from "@/lib/favorites";
import { useSiteLocale } from "@/components/layout/locale-provider";

const ThemeToggle = dynamic(() => import("@/components/layout/theme-toggle").then((mod) => mod.ThemeToggle), {
  ssr: false,
});

type SiteHeaderProps = {
  isAppShell?: boolean;
};

export function SiteHeader({ isAppShell = false }: SiteHeaderProps) {
  const pathname = usePathname();
  const { locale, setLocale, t } = useSiteLocale();
  const [favoritesCount, setFavoritesCount] = useState(0);

  useEffect(() => {
    const sync = () => setFavoritesCount(countFavorites());
    sync();
    return subscribeFavorites(sync);
  }, []);

  const navItems = [
    { href: "/", label: t("产品观察", "The brief") },
    { href: "/discover", label: t("随机发现", "Discover") },
    { href: "/demo", label: t("交互演示", "Demos") },
    { href: "/blog", label: t("博客动态", "News") },
    { href: "/search", label: t("搜索", "Search") },
  ];

  const mobileNavItems = [
    { href: "/", label: t("首页", "Home"), icon: Binoculars },
    { href: "/discover", label: t("发现", "Discover"), icon: Shuffle },
    { href: "/demo", label: t("演示", "Demos"), icon: PlayCircle },
    { href: "/search", label: t("搜索", "Search"), icon: MagnifyingGlass },
  ];

  function applyLocale(nextLocale: SiteLocale) {
    setLocale(nextLocale);
  }

  function isNavActive(href: string) {
    if (href === "/") return pathname === "/";
    return pathname === href || pathname.startsWith(`${href}/`);
  }

  return (
    <header className="navbar">
      <div className="nav-container">
        <Link href="/" className="logo" aria-label={t("黑马雷达首页", "Darkhorse Radar home")}>
          <HorseMark className="brand-mark" />
          <span className="brand-wordmark">
            <span className="logo-text">{t("黑马雷达", "Darkhorse Radar")}</span>
            <span className="brand-wordmark__caption">{t("DARKHORSE RADAR", "INDEPENDENT PRODUCT DISCOVERY")}</span>
          </span>
        </Link>

        <nav className="nav-links" aria-label={t("主导航", "Main navigation")}>
          {navItems.map((item) => {
            const isActive = isNavActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-link ${isActive ? "active" : ""}`}
                aria-current={isActive ? "page" : undefined}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="nav-actions">
          {!isAppShell ? (
            <div className="nav-ai">
              <ChatBar variant="compactTrigger" />
            </div>
          ) : null}
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
            <BookmarkSimple size={16} />
            <span>{t("收藏", "Favorites")} {favoritesCount}</span>
          </button>
          <ThemeToggle ariaLabel={t("切换主题", "Toggle theme")} />
        </div>
      </div>

      <nav className="mobile-tabbar" aria-label={t("底部导航", "Bottom navigation")}>
        {mobileNavItems.map((item) => {
          const Icon = item.icon;
          const isActive = isNavActive(item.href);
          return (
            <Link
              key={`mobile-${item.href}`}
              href={item.href}
              className={`mobile-tabbar__link ${isActive ? "active" : ""}`}
              aria-current={isActive ? "page" : undefined}
            >
              <span className="mobile-tabbar__icon">
                <Icon size={16} />
              </span>
              <span>{item.label}</span>
            </Link>
          );
        })}
        <button
          type="button"
          className="mobile-tabbar__button"
          aria-label={t("打开收藏夹", "Open favorites")}
          onClick={() => openFavoritesPanel("product")}
        >
          <span className="mobile-tabbar__icon">
            <BookmarkSimple size={16} />
          </span>
          <span>{t("收藏", "Favorites")}</span>
          <strong className="mobile-tabbar__badge">{favoritesCount}</strong>
        </button>
      </nav>
    </header>
  );
}
