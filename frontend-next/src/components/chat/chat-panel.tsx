"use client";

import { useEffect, useRef } from "react";
import { ChevronDown, Sparkles } from "lucide-react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import { ChatMessageBubble } from "./chat-message";
import { ChatSuggestions } from "./chat-suggestions";
import type { ChatMessage } from "./use-chat";

type ChatPanelProps = {
  messages: ChatMessage[];
  isLoading: boolean;
  onSend: (text: string) => void;
  onMinimize: () => void;
};

export function ChatPanel({ messages, isLoading, onSend, onMinimize }: ChatPanelProps) {
  const { t } = useSiteLocale();
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const node = scrollRef.current;
    if (!node) return;
    node.scrollTop = node.scrollHeight;
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const input = inputRef.current;
    if (!input) return;
    const value = input.value.trim();
    if (!value) return;
    input.value = "";
    onSend(value);
  }

  const hasMessages = messages.length > 0;

  return (
    <div className="chat-panel">
      <header className="chat-panel__header">
        <div className="chat-panel__title">
          <Sparkles size={16} />
          <span>{t("WeeklyAI 助手", "WeeklyAI Assistant")}</span>
        </div>
        <button type="button" className="chat-panel__minimize" onClick={onMinimize} aria-label={t("收起", "Minimize")}>
          <ChevronDown size={18} />
        </button>
      </header>

      <div className="chat-panel__body" ref={scrollRef}>
        {!hasMessages ? (
          <div className="chat-welcome">
            <p className="chat-welcome__text">
              {t("问我：黑马推荐、融资动态、硬件趋势、区域新产品。", "Ask me about dark horses, funding trends, hardware, and regional product signals.")}
            </p>
            <ChatSuggestions onSelect={onSend} />
          </div>
        ) : (
          <div className="chat-messages">
            {messages.map((message) => (
              <ChatMessageBubble key={message.id} message={message} />
            ))}
            {isLoading && messages[messages.length - 1]?.content === "" ? (
              <div className="chat-thinking" aria-label={t("思考中", "Thinking")}>
                <span className="chat-thinking__dot" />
                <span className="chat-thinking__dot" />
                <span className="chat-thinking__dot" />
              </div>
            ) : null}
          </div>
        )}
      </div>

      {hasMessages ? (
        <div className="chat-panel__suggestions-row">
          <ChatSuggestions onSelect={onSend} compact />
        </div>
      ) : null}

      <form className="chat-panel__input-row" onSubmit={handleSubmit}>
        <input
          ref={inputRef}
          type="text"
          className="chat-panel__input"
          placeholder={t("输入你的问题…", "Ask your question…")}
          disabled={isLoading}
          autoComplete="off"
        />
        <button type="submit" className="chat-panel__send" disabled={isLoading} aria-label={t("发送", "Send")}>
          {t("发送", "Send")}
        </button>
      </form>

      <div className="chat-panel__footer">
        <span className="chat-panel__powered">{t("Powered by Perplexity", "Powered by Perplexity")}</span>
      </div>
    </div>
  );
}
