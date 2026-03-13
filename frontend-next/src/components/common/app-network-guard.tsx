"use client";

import { RefreshCw, WifiOff } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useSiteLocale } from "@/components/layout/locale-provider";

const API_BASE =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000/api/v1").trim()
    : "http://localhost:5000/api/v1";

const HEALTH_PATH = "/products/last-updated";
const HEALTH_TIMEOUT_MS = 7000;

type NetworkStatus = "checking" | "healthy" | "offline" | "timeout" | "error";

type AppNetworkGuardProps = {
  enabled?: boolean;
};

function withTimeout(signal: AbortSignal, timeoutMs: number) {
  const controller = new AbortController();
  const relayAbort = () => controller.abort();
  signal.addEventListener("abort", relayAbort, { once: true });

  const timeoutId = window.setTimeout(() => {
    controller.abort();
  }, timeoutMs);

  return {
    signal: controller.signal,
    done() {
      signal.removeEventListener("abort", relayAbort);
      window.clearTimeout(timeoutId);
    },
  };
}

export function AppNetworkGuard({ enabled = false }: AppNetworkGuardProps) {
  const { t } = useSiteLocale();
  const [status, setStatus] = useState<NetworkStatus>("checking");
  const [visible, setVisible] = useState(false);
  const [checking, setChecking] = useState(false);

  const statusText = useMemo(() => {
    if (status === "offline") {
      return t("当前网络已离线，请检查连接后重试。", "You are offline. Please reconnect and retry.");
    }
    if (status === "timeout") {
      return t("请求超时，可能是网络较慢或 API 暂时不可用。", "Request timed out. The network may be slow or the API is temporarily unavailable.");
    }
    if (status === "error") {
      return t("服务暂时不可用，请稍后重试。", "Service is temporarily unavailable. Please try again.");
    }
    return t("正在检查网络状态…", "Checking network status...");
  }, [status, t]);

  const checkHealth = useCallback(async () => {
    if (!enabled || typeof window === "undefined") return;

    if (!window.navigator.onLine) {
      setStatus("offline");
      setVisible(true);
      return;
    }

    setChecking(true);
    setStatus("checking");

    const requestController = new AbortController();
    const scoped = withTimeout(requestController.signal, HEALTH_TIMEOUT_MS);

    try {
      const response = await fetch(`${API_BASE.replace(/\/$/, "")}${HEALTH_PATH}`, {
        method: "GET",
        cache: "no-store",
        headers: { Accept: "application/json" },
        signal: scoped.signal,
      });

      // 429 still means API is reachable and app should continue rendering.
      if (response.ok || response.status === 429) {
        setStatus("healthy");
        setVisible(false);
        return;
      }

      setStatus("error");
      setVisible(true);
    } catch (error) {
      if ((error as Error).name === "AbortError") {
        setStatus("timeout");
      } else {
        setStatus("error");
      }
      setVisible(true);
    } finally {
      scoped.done();
      setChecking(false);
    }
  }, [enabled]);

  useEffect(() => {
    if (!enabled || typeof window === "undefined") return;

    void checkHealth();

    const onOffline = () => {
      setStatus("offline");
      setVisible(true);
    };

    const onOnline = () => {
      void checkHealth();
    };

    window.addEventListener("offline", onOffline);
    window.addEventListener("online", onOnline);
    return () => {
      window.removeEventListener("offline", onOffline);
      window.removeEventListener("online", onOnline);
    };
  }, [checkHealth, enabled]);

  if (!enabled || !visible) return null;

  return (
    <div className="app-network-overlay" role="dialog" aria-live="polite" aria-modal="false">
      <div className="app-network-overlay__card">
        <div className="app-network-overlay__icon" aria-hidden="true">
          <WifiOff size={22} />
        </div>
        <h2>{t("网络连接异常", "Network connection issue")}</h2>
        <p>{statusText}</p>
        <button type="button" className="link-btn link-btn--primary" onClick={() => void checkHealth()} disabled={checking}>
          <RefreshCw size={14} className={checking ? "app-network-overlay__spin" : ""} />
          {checking ? t("重试中…", "Retrying…") : t("重试", "Retry")}
        </button>
      </div>
    </div>
  );
}
