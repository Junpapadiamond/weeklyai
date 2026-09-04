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
      t("推荐 3 个有明确用途的产品，附来源", "Find 3 products with clear use cases and sources"),
      t("哪些产品能帮我分析用户访谈？", "What can help me analyze customer interviews?"),
      t("硬件产品有哪些值得验证的假设？", "What should I validate about these hardware products?"),
      t("比较两个 Agent 产品解决的问题", "Compare the problems two agent products solve"),
      t("给我 2-3 分潜力股", "Show me rising stars scored 2-3"),
      t("欧洲有哪些产品值得研究？请标注收录日期", "Find European products and include their discovery dates"),
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
