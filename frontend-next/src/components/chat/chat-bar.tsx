"use client";

import { useEffect, useState } from "react";
import { ArrowUp, Sparkles } from "lucide-react";
import { ChatPanel } from "./chat-panel";
import { ChatSuggestions } from "./chat-suggestions";
import { useChat } from "./use-chat";

type UiLocale = "zh" | "en";
const CHAT_LOCALE_STORAGE_KEY = "weeklyai_chat_locale";

function resolveNavigatorLocale(): UiLocale {
  if (typeof navigator !== "undefined" && navigator.language.toLowerCase().startsWith("en")) {
    return "en";
  }
  return "zh";
}

function resolveInitialLocale(): UiLocale {
  if (typeof window === "undefined") return "zh";
  const saved = window.localStorage.getItem(CHAT_LOCALE_STORAGE_KEY);
  if (saved === "zh" || saved === "en") return saved;
  return resolveNavigatorLocale();
}

function t(locale: UiLocale, zh: string, en: string): string {
  return locale === "en" ? en : zh;
}

export function ChatBar() {
  const [locale, setLocale] = useState<UiLocale>(resolveInitialLocale);
  const [isOpen, setIsOpen] = useState(false);
  const chatLocale = locale === "en" ? "en-US" : "zh-CN";
  const { messages, isLoading, sendMessage } = useChat({ locale: chatLocale });

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(CHAT_LOCALE_STORAGE_KEY, locale);
  }, [locale]);

  function openPanel(initialText?: string) {
    setIsOpen(true);
    if (initialText) sendMessage(initialText);
  }

  function minimizePanel() {
    setIsOpen(false);
  }

  function toggleLocale() {
    setLocale((prev) => (prev === "zh" ? "en" : "zh"));
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
        <ChatPanel
          locale={locale}
          messages={messages}
          isLoading={isLoading}
          onSend={sendMessage}
          onToggleLocale={toggleLocale}
          onMinimize={minimizePanel}
        />
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
            placeholder={t(locale, "问点什么：本周黑马、融资、Agent...", "Ask about dark horses, funding, agents...")}
            autoComplete="off"
            onFocus={() => openPanel()}
          />
          <button
            type="button"
            className="chat-locale-toggle chat-locale-toggle--bar"
            onClick={toggleLocale}
            aria-label={t(locale, "切换到英文", "Switch to Chinese")}
          >
            {locale === "zh" ? "中" : "EN"}
          </button>
          <button type="submit" className="chat-bar__send" aria-label={t(locale, "发送", "Send")}>
            <ArrowUp size={16} />
          </button>
        </form>
        <ChatSuggestions locale={locale} onSelect={(text) => openPanel(text)} compact />
      </div>
    </div>
  );
}
