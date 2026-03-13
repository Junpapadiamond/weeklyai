import type { ReactNode } from "react";
import { AppNetworkGuard } from "@/components/common/app-network-guard";
import { FavoritesPanel } from "@/components/favorites/favorites-panel";
import { SiteHeader } from "@/components/layout/site-header";

type PageShellProps = {
  isAppShell?: boolean;
  children: ReactNode;
};

export function PageShell({ isAppShell = false, children }: PageShellProps) {
  return (
    <>
      <div className="bg-decoration" aria-hidden="true">
        <div className="bg-gradient-1" />
        <div className="bg-gradient-2" />
        <div className="bg-grid" />
      </div>
      <AppNetworkGuard enabled={isAppShell} />
      <SiteHeader isAppShell={isAppShell} />
      <FavoritesPanel />
      <main className="main-content">{children}</main>
    </>
  );
}
