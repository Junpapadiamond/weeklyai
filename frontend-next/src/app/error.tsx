"use client";

import Link from "next/link";
import { useEffect } from "react";
import { ArrowClockwise, Warning } from "@phosphor-icons/react";
import { isAppShell } from "@/lib/app-shell";
import { useSiteLocale } from "@/components/layout/locale-provider";

type ErrorPageProps = {
  error: Error & { digest?: string };
  retry: () => void;
};

export default function ErrorPage({ error, retry }: ErrorPageProps) {
  const { t } = useSiteLocale();
  useEffect(() => {
    // Keep error visible in dev and collect digest in production logs.
    console.error("weeklyai_render_error", {
      message: error.message,
      digest: error.digest,
    });
  }, [error]);

  const appShell = isAppShell();

  return (
    <section className="section">
      <div className="error-block" role="alert">
        <div className="error-code">
          <Warning size={16} />
          {appShell ? "APP NETWORK ERROR" : "RUNTIME ERROR"}
        </div>
        <h1 className="section-title">{t("暂时无法加载，请重试", "Unable to load this page")}</h1>
        <p className="section-desc">
          {t("当前网络或服务不稳定，点击重试继续使用，也可以返回首页。", "Please retry, or return to the homepage.")}
        </p>
        <div className="list-controls">
          <button type="button" className="link-btn link-btn--primary" onClick={retry}>
            <ArrowClockwise size={14} /> {t("重试", "Retry")}
          </button>
          <Link href="/" className="link-btn">
            {t("返回首页", "Back to home")}
          </Link>
        </div>
      </div>
    </section>
  );
}
