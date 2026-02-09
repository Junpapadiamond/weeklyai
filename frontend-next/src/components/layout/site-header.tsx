"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { usePathname } from "next/navigation";
import { Flame, Newspaper, Search, Sparkles } from "lucide-react";

const ThemeToggle = dynamic(() => import("@/components/layout/theme-toggle").then((mod) => mod.ThemeToggle), {
  ssr: false,
});

const navItems = [
  { href: "/", label: "黑马推荐", icon: Flame },
  { href: "/blog", label: "博客动态", icon: Newspaper },
  { href: "/search", label: "搜索", icon: Search },
];

export function SiteHeader() {
  const pathname = usePathname();

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

        <ThemeToggle />
      </div>
    </header>
  );
}
