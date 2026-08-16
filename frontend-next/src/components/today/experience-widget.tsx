"use client";

import { useState, useRef } from "react";
import { Sparkles, ExternalLink } from "lucide-react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { tryProduct } from "@/lib/api-client";
import type { Product } from "@/types/api";

type Props = {
  product: Product;
};

type State = "idle" | "loading" | "streaming" | "done" | "error";

export function ExperienceWidget({ product }: Props) {
  const { locale, t } = useSiteLocale();
  const [input, setInput] = useState("");
  const [output, setOutput] = useState("");
  const [state, setState] = useState<State>("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const abortRef = useRef<AbortController | null>(null);

  const experience = product.extra?.experience;
  if (!experience) return null;

  const demoType = experience.demo_type ?? "text_generation";
  const isPassive = demoType === "iframe" || demoType === "static";
  const placeholder = experience.demo_placeholder || t("输入你的需求...", "Enter your request...");
  const exampleInputs = experience.example_inputs ?? [];
  const fallbackUrl = experience.fallback_url ?? "";

  if (isPassive && !fallbackUrl) return null;

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || state === "loading" || state === "streaming") return;

    if (isPassive && fallbackUrl) {
      window.open(fallbackUrl, "_blank", "noopener,noreferrer");
      return;
    }

    abortRef.current?.abort();
    setState("loading");
    setOutput("");
    setErrorMsg("");

    try {
      const response = await tryProduct(product._id || product.name, trimmed, locale === "en-US" ? "en" : "zh");
      if (!response.ok || !response.body) {
        setState("error");
        setErrorMsg(t("请求失败，请稍后重试", "Request failed, please try again"));
        return;
      }

      setState("streaming");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data:")) continue;
          const raw = line.slice(5).trim();
          if (!raw) continue;
          try {
            const event = JSON.parse(raw);
            if (event.type === "text") {
              setOutput((prev) => prev + event.content);
            } else if (event.type === "redirect" && event.url) {
              window.open(event.url, "_blank", "noopener,noreferrer");
              setState("done");
              return;
            } else if (event.type === "error") {
              setState("error");
              setErrorMsg(event.message || t("发生错误", "An error occurred"));
              return;
            } else if (event.type === "done") {
              setState("done");
              return;
            }
          } catch {
            // skip malformed chunk
          }
        }
      }
      setState("done");
    } catch {
      setState("error");
      setErrorMsg(t("网络错误，请稍后重试", "Network error, please try again"));
    }
  }

  function handleReset() {
    abortRef.current?.abort();
    setOutput("");
    setInput("");
    setState("idle");
    setErrorMsg("");
  }

  const isRunning = state === "loading" || state === "streaming";

  return (
    <section className="today-experience">
      <h2 className="today-section__title">
        <Sparkles size={16} aria-hidden="true" />
        {t("立即体验", "Try It Now")}
      </h2>

      {isPassive && fallbackUrl ? (
        <div className="today-experience__passive">
          <p className="today-experience__passive-note">
            {t("该产品提供官方 playground，点击下方按钮直接体验：", "This product has an official playground — try it directly:")}
          </p>
          <a
            href={fallbackUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn--primary today-experience__external"
          >
            <ExternalLink size={14} aria-hidden="true" />
            {t("打开官方 Demo", "Open Official Demo")}
          </a>
        </div>
      ) : (
        <>
          {exampleInputs.length > 0 && state === "idle" && (
            <div className="today-experience__examples">
              <span className="today-experience__examples-label">{t("试试这些输入：", "Try these inputs:")}</span>
              {exampleInputs.map((ex) => (
                <button
                  key={ex}
                  type="button"
                  className="today-experience__example-chip"
                  onClick={() => setInput(ex)}
                >
                  {ex}
                </button>
              ))}
            </div>
          )}

          <form className="today-experience__form" onSubmit={handleGenerate}>
            <textarea
              className="today-experience__input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={placeholder}
              rows={3}
              disabled={isRunning}
              aria-label={t("输入内容", "Enter input")}
            />
            <div className="today-experience__actions">
              {(state === "done" || state === "error") && (
                <button type="button" className="btn btn--ghost" onClick={handleReset}>
                  {t("重置", "Reset")}
                </button>
              )}
              <button
                type="submit"
                className="btn btn--primary"
                disabled={!input.trim() || isRunning}
              >
                {isRunning ? t("生成中...", "Generating...") : t("生成", "Generate")}
              </button>
            </div>
          </form>

          {(output || state === "loading") && (
            <div className="today-experience__output" aria-live="polite">
              {state === "loading" && !output && (
                <span className="today-experience__thinking">{t("思考中...", "Thinking...")}</span>
              )}
              {output && <p className="today-experience__result">{output}</p>}
            </div>
          )}

          {state === "error" && errorMsg && (
            <p className="today-experience__error" role="alert">{errorMsg}</p>
          )}
        </>
      )}
    </section>
  );
}
