"use client";

import { useEffect, useRef, useState } from "react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { DemoPlayer } from "@/components/demo/demo-player";
import { fetchDemo, generateDemo, type DemoError } from "@/lib/demo-client";
import type { DemoSpec } from "@/lib/demo-schema";

type State =
  | { kind: "checking" }
  | { kind: "absent"; generationAvailable: boolean }
  | { kind: "building" }
  | { kind: "ready"; spec: DemoSpec }
  | { kind: "failed"; error: DemoError; message: string };

/**
 * Demo block on a product page. Looks for an existing demo on mount, which is
 * cheap; generating one is left to an explicit click because it costs money and
 * takes half a minute.
 */
export function ProductDemoSection({ productId, productName }: { productId: string; productName: string }) {
  const { t } = useSiteLocale();
  const [state, setState] = useState<State>({ kind: "checking" });
  // Seconds actually waited, restarted per attempt via `run`.
  const [run, setRun] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    abortRef.current = controller;
    void fetchDemo(productId, controller.signal).then((result) => {
      if (controller.signal.aborted) return;
      setState(result.ok ? { kind: "ready", spec: result.spec } : { kind: "absent", generationAvailable: result.generationAvailable });
    });
    return () => controller.abort();
  }, [productId]);

  useEffect(() => {
    if (state.kind !== "building") return;
    const timer = window.setInterval(() => setElapsed((seconds) => seconds + 1), 1000);
    return () => window.clearInterval(timer);
  }, [state.kind, run]);

  async function build(refresh = false) {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setRun((value) => value + 1);
    setElapsed(0);
    setState({ kind: "building" });
    const result = await generateDemo(productId, { refresh, signal: controller.signal });
    if (controller.signal.aborted) return;
    setState(
      result.ok
        ? { kind: "ready", spec: result.spec }
        : { kind: "failed", error: result.error, message: result.message }
    );
  }

  if (state.kind === "checking") return null;

  if (state.kind === "ready") {
    return (
      <section className="detail-block">
        <h2 className="detail-block__title">{t("交互演示", "Interactive demo")}</h2>
        <DemoPlayer spec={state.spec} onRegenerate={() => void build(true)} />
      </section>
    );
  }

  return (
    <section className="detail-block">
      <h2 className="detail-block__title">{t("交互演示", "Interactive demo")}</h2>
      <div className="demo-entry">
        {state.kind === "building" ? (
          <>
            <p role="status" aria-live="polite">
              {t(
                `正在为 ${productName} 生成演示…已用 ${elapsed} 秒，通常需要 15–40 秒。`,
                `Building a demo for ${productName}… ${elapsed}s elapsed, usually 15–40 seconds.`
              )}
            </p>
            <button
              type="button"
              className="demo-btn"
              onClick={() => {
                abortRef.current?.abort();
                setState({ kind: "absent", generationAvailable: true });
              }}
            >
              {t("取消", "Cancel")}
            </button>
          </>
        ) : state.kind === "failed" ? (
          <>
            <p role="alert">
              {state.message ||
                t("没能生成这个演示，请稍后再试。", "That demo could not be built. Please try again shortly.")}
            </p>
            {state.error !== "NOT_CONFIGURED" && state.error !== "GENERATION_DISABLED" ? (
              <button type="button" className="demo-btn" onClick={() => void build()}>
                {t("重试", "Try again")}
              </button>
            ) : null}
          </>
        ) : state.generationAvailable ? (
          <>
            <p>
              {t(
                "还没有为这个产品建过演示。现场生成一个，看它到底做什么——不用注册。",
                "No demo has been built for this product yet. Generate one now and see what it actually does — no signup."
              )}
            </p>
            <button type="button" className="demo-btn demo-btn--primary" onClick={() => void build()}>
              {t("生成演示", "Build a demo")}
            </button>
          </>
        ) : (
          <p>
            {t(
              "还没有为这个产品建过演示。",
              "No demo has been built for this product yet."
            )}{" "}
            <a href="/demo">{t("看看已有的演示", "Browse the demos that exist")}</a>
          </p>
        )}
      </div>
    </section>
  );
}
