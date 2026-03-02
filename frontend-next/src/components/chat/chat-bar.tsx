"use client";

import { useState } from "react";
import { ArrowUp, Sparkles } from "lucide-react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { ChatPanel } from "./chat-panel";
import { ChatSuggestions } from "./chat-suggestions";
import { useChat } from "./use-chat";

export function ChatBar() {
  const { locale, t } = useSiteLocale();
  const [isOpen, setIsOpen] = useState(false);
  const { messages, isLoading, sendMessage, status } = useChat({ locale });

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

  return (
    <div className="chat-bar-anchor">
      <div className="chat-bar">
        <form className="chat-bar__form" onSubmit={handleBarSubmit}>
          <div className="chat-bar__glow-blur" aria-hidden="true" />
          <span className="chat-bar__icon">
            <Sparkles size={16} />
          </span>
          <input
            name="chatInput"
            type="text"
            className="chat-bar__input"
            placeholder={t("问点什么：本周黑马、融资、Agent...", "Ask about dark horses, funding, agents...")}
            autoComplete="off"
            onFocus={() => openPanel()}
          />
          <button type="submit" className="chat-bar__send" aria-label={t("发送", "Send")}>
            <ArrowUp size={16} />
          </button>
        </form>
        <p className={`chat-bar__status ${status.ready ? "is-ready" : "is-degraded"}`}>
          {status.checking
            ? t("AI 能力检测中...", "Checking AI status...")
            : status.ready
              ? t("AI 助手已接入，可直接提问。", "AI assistant is online.")
              : t("AI 助手暂不可用（配置缺失或服务异常）。", "AI assistant unavailable (config or service issue).")}
        </p>
        <ChatSuggestions onSelect={(text) => openPanel(text)} compact />
      </div>
    </div>
  );
}
