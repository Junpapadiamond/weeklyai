"use client";

import Link from "next/link";
import { useEffect } from "react";
import { RefreshCw, TriangleAlert } from "lucide-react";
import { isAppShell } from "@/lib/app-shell";

type ErrorPageProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    // Keep error visible in dev and collect digest in production logs.
    console.error("weeklyai_render_error", {
      message: error.message,
      digest: error.digest,
    });
  }, [error]);

  const appShell = isAppShell();

  return (
    <main className="section">
      <div className="error-block">
        <div className="error-code">
          <TriangleAlert size={16} />
          {appShell ? "APP NETWORK ERROR" : "RUNTIME ERROR"}
        </div>
        <h1 className="section-title">{appShell ? "网络异常，请稍后重试" : "Something went wrong"}</h1>
        <p className="section-desc">
          {appShell
            ? "当前网络或服务不稳定，点击重试继续使用。"
            : "The page failed to render. Please retry or go back to the homepage."}
        </p>
        <div className="list-controls">
          <button type="button" className="link-btn link-btn--primary" onClick={reset}>
            <RefreshCw size={14} /> {appShell ? "重试" : "Retry"}
          </button>
          <Link href="/" className="link-btn">
            {appShell ? "返回首页" : "Back to home"}
          </Link>
        </div>
      </div>
    </main>
  );
}
