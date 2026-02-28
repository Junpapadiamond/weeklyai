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
      t("推荐 3 个本周黑马", "Recommend 3 dark horses this week"),
      t("最近融资最多的是谁", "Who raised the most recently"),
      t("硬件方向有什么值得看", "What hardware products look promising"),
      t("本周最热的 Agent 产品", "Top trending agent products this week"),
      t("给我 2-3 分潜力股", "Show me rising stars scored 2-3"),
      t("按地区看一下欧洲新品", "Show me recent products from Europe"),
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
