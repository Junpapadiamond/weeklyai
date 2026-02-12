"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { usePathname } from "next/navigation";
import { Dice5, Heart, Flame, Newspaper, Search, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { countFavorites, openFavoritesPanel, subscribeFavorites } from "@/lib/favorites";

const ThemeToggle = dynamic(() => import("@/components/layout/theme-toggle").then((mod) => mod.ThemeToggle), {
  ssr: false,
});

const navItems = [
  { href: "/", label: "黑马推荐", icon: Flame },
  { href: "/discover", label: "随机发现", icon: Dice5 },
  { href: "/blog", label: "博客动态", icon: Newspaper },
  { href: "/search", label: "搜索", icon: Search },
];

export function SiteHeader() {
  const pathname = usePathname();
  const [favoritesCount, setFavoritesCount] = useState(0);

  useEffect(() => {
    const sync = () => setFavoritesCount(countFavorites());
    sync();
    return subscribeFavorites(sync);
  }, []);

  return (
    <header className="navbar">
      <div className="nav-container">
        <Link href="/" className="logo" aria-label="WeeklyAI 首页">
          <span className="logo-icon">
            <Sparkles size={18} />
          </span>
          <span className="logo-text">WeeklyAI</span>
        </Link>

        <nav className="nav-links" aria-label="主导航">
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
          <button className="nav-favorites" type="button" onClick={() => openFavoritesPanel("product")} aria-label="打开收藏夹">
            <Heart size={16} />
            <span>收藏 {favoritesCount}</span>
          </button>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
