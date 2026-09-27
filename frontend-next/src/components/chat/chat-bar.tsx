"use client";

import { useState } from "react";
import { ArrowUp, ChatCircleDots } from "@phosphor-icons/react";
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
            <ChatCircleDots size={14} />
          </span>
          <span>{t("AI 助手", "Ask Radar")}</span>
        </button>
      </div>
    );
  }

  return (
    <div className="chat-bar-anchor">
      <div className="chat-bar chat-bar--desktop">
        <div className="chat-bar__eyebrow">
          <span className="chat-bar__eyebrow-chip">
            <ChatCircleDots size={12} />
            {t("AI 助手", "Ask Radar")}
          </span>
          <span className="chat-bar__eyebrow-copy">
            {t("说说你的需求，让助手帮你找产品。", "Ask the assistant about products, funding, categories, and regional signals.")}
          </span>
        </div>

        <form className="chat-bar__form" onSubmit={handleBarSubmit}>
          <span className="chat-bar__icon">
            <ChatCircleDots size={16} />
          </span>
          <input
            name="chatInput"
            type="text"
            className="chat-bar__input"
            placeholder={t("想找什么工具？比如：帮我推荐几款 AI 编程工具", "Ask AI about dark horses, funding, agents, hardware trends...")}
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
        <ChatCircleDots size={16} />
        {t("AI 助手", "Ask Radar")}
      </button>
    </div>
  );
}
