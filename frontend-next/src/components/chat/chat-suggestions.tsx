"use client";

import { useMemo } from "react";
import { useSiteLocale } from "@/components/layout/locale-provider";

type ChatSuggestionsProps = {
  onSelect: (text: string) => void;
  compact?: boolean;
};

export function ChatSuggestions({ onSelect, compact = false }: ChatSuggestionsProps) {
  const { t } = useSiteLocale();

  const suggestions = useMemo(
    () => [
      t("最近有哪些值得试试的新产品？", "Find 3 products with clear use cases and sources"),
      t("哪些产品能帮我分析用户访谈？", "What can help me analyze customer interviews?"),
      t("有哪些有意思的 AI 硬件？", "What should I validate about these hardware products?"),
      t("帮我比较几款 AI 编程工具", "Compare the problems two agent products solve"),
      t("找几款还没火起来的 AI 产品", "Show me rising stars scored 2-3"),
      t("欧洲最近有哪些 AI 新产品？", "Find European products and include their discovery dates"),
    ],
    [t]
  );

  const visible = compact ? suggestions.slice(0, 4) : suggestions;

  return (
    <div className="chat-suggestions">
      {visible.map((text) => (
        <button key={text} type="button" className="chat-chip" onClick={() => onSelect(text)}>
          {text}
        </button>
      ))}
    </div>
  );
}
