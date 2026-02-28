"use client";

import { Sparkles, User } from "lucide-react";
import type { ChatMessage } from "./use-chat";

type UiLocale = "zh" | "en";

function t(locale: UiLocale, zh: string, en: string): string {
  return locale === "en" ? en : zh;
}

type ChatMessageProps = {
  locale: UiLocale;
  message: ChatMessage;
};

function cleanDisplayText(text: string): string {
  const value = text || "";
  return value
    .replace(/\[(?:\d+(?:\s*[-,，]\s*\d+)*)\]/g, "")
    .replace(/\[(?:product_data|products?_data|产品数据|source|sources)\]/gi, "")
    .replace(/[ \t]{2,}/g, " ")
    .replace(/[ \t]+([,，。！？!?:;；])/g, "$1");
}

export function ChatMessageBubble({ locale, message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const errorPrefixes = ["HTTP ", "Upstream API error", "Request timed out", "请求超时", "Request failed", "No streamed content"];
  const isError =
    message.content === "__ERROR__" || errorPrefixes.some((prefix) => message.content.startsWith(prefix));
  const displayContent = cleanDisplayText(message.content);

  return (
    <div className={`chat-message ${isUser ? "chat-message--user" : "chat-message--assistant"}`}>
      <div className="chat-message__avatar">{isUser ? <User size={14} /> : <Sparkles size={14} />}</div>
      <div className="chat-message__content">
        {isError ? (
          <p className="chat-message__error">
            {message.content === "__ERROR__"
              ? t(locale, "请求失败，请稍后重试。", "Request failed. Please try again.")
              : message.content}
          </p>
        ) : (
          <>
            <div className="chat-message__text">
              {displayContent}
              {message.isStreaming ? <span className="chat-cursor" /> : null}
            </div>
            {message.products?.length ? (
              <div className="chat-message__products">
                {message.products.map((id) => (
                  <a key={id} href={`/product/${encodeURIComponent(id)}`} className="chat-product-link">
                    {id}
                  </a>
                ))}
              </div>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}
