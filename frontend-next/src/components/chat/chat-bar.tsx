"use client";

import { useState } from "react";
import { ArrowUp, Sparkles } from "lucide-react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { ChatPanel } from "./chat-panel";
import { ChatSuggestions } from "./chat-suggestions";
import { useChat } from "./use-chat";

type ChatBarProps = {
  variant?: "full" | "compactTrigger";
};

export function ChatBar({ variant = "full" }: ChatBarProps) {
  const { locale, t } = useSiteLocale();
  const [isOpen, setIsOpen] = useState(false);
  const { messages, isLoading, sendMessage } = useChat({ locale });

  function openPanel(initialText?: string) {
    setIsOpen(true);
    if (initialText) sendMessage(initialText);
  }

  function minimizePanel() {
    setIsOpen(false);
  }

  function handleBarSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const input = form.elements.namedItem("chatInput") as HTMLInputElement;
    const value = input?.value.trim();
    if (!value) return;
    input.value = "";
    openPanel(value);
  }

  if (isOpen) {
    return (
      <div className="chat-overlay">
        <div className="chat-overlay__backdrop" onClick={minimizePanel} />
        <ChatPanel messages={messages} isLoading={isLoading} onSend={sendMessage} onMinimize={minimizePanel} />
      </div>
    );
  }

  if (variant === "compactTrigger") {
    return (
      <div className="chat-bar-anchor chat-bar-anchor--compact">
        <button
          type="button"
          className="chat-trigger"
          aria-haspopup="dialog"
          aria-label={t("打开 AI 助手", "Open AI assistant")}
          onClick={() => openPanel()}
        >
          <span className="chat-trigger__icon">
            <Sparkles size={14} />
          </span>
          <span>{t("Ask AI", "Ask AI")}</span>
        </button>
      </div>
    );
  }

  return (
    <div className="chat-bar-anchor">
      <div className="chat-bar chat-bar--desktop">
        <div className="chat-bar__eyebrow">
          <span className="chat-bar__eyebrow-chip">
            <Sparkles size={12} />
            {t("Ask AI", "Ask AI")}
          </span>
          <span className="chat-bar__eyebrow-copy">
            {t("向助手直接问产品、融资、赛道和地区信号。", "Ask the assistant about products, funding, categories, and regional signals.")}
          </span>
        </div>

        <form className="chat-bar__form" onSubmit={handleBarSubmit}>
          <div className="chat-bar__glow-blur" aria-hidden="true" />
          <span className="chat-bar__icon">
            <Sparkles size={16} />
          </span>
          <input
            name="chatInput"
            type="text"
            className="chat-bar__input"
            placeholder={t("Ask AI：本周黑马、融资、Agent、硬件趋势...", "Ask AI about dark horses, funding, agents, hardware trends...")}
            autoComplete="off"
            onFocus={() => openPanel()}
          />
          <button type="submit" className="chat-bar__send" aria-label={t("发送", "Send")}>
            <ArrowUp size={16} />
          </button>
        </form>
        <ChatSuggestions onSelect={(text) => openPanel(text)} compact />
      </div>

      <button type="button" className="chat-bar__fab" onClick={() => openPanel()}>
        <Sparkles size={16} />
        {t("Ask AI", "Ask AI")}
      </button>
    </div>
  );
}
