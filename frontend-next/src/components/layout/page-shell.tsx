import type { ReactNode } from "react";
import { SiteHeader } from "@/components/layout/site-header";

type PageShellProps = {
  children: ReactNode;
};

export function PageShell({ children }: PageShellProps) {
  return (
    <>
      <div className="bg-decoration" aria-hidden="true">
        <div className="bg-gradient-1" />
        <div className="bg-gradient-2" />
        <div className="bg-grid" />
      </div>
      <SiteHeader />
      <main className="main-content">{children}</main>
    </>
  );
}
