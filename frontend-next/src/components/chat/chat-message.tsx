"use client";

import { ChatCircleDots, UserCircle } from "@phosphor-icons/react";
import { Fragment } from "react";
import { useSiteLocale } from "@/components/layout/locale-provider";
import type { ChatMessage } from "./use-chat";

type ChatMessageProps = {
  message: ChatMessage;
};

function bareLink(text: string): string {
  let href = text;
  // Prose often wraps a URL in parentheses. Keep balanced parentheses that
  // belong to the URL itself, and leave trailing prose outside the anchor.
  for (;;) {
    const previous = href;
    href = href.replace(/[.,;!?。，；！？]+$/, "");
    for (const [open, close] of [["(", ")"], ["[", "]"], ["（", "）"]]) {
      if (href.endsWith(close) && href.split(close).length > href.split(open).length) {
        href = href.slice(0, -1);
      }
    }
    if (href === previous) return href;
  }
}

// Render source links without accepting HTML or unsafe URL schemes from the model.
function linkedText(text: string) {
  return text.split(/(\[[^\]\n]+\]\(https?:\/\/[^\s)]+\)|https?:\/\/[^\s<>]+)/g).map((part, index) => {
    const markdown = part.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/);
    const href = markdown?.[2] || (/^https?:\/\//.test(part) ? bareLink(part) : "");
    if (!href) return part;
    return <Fragment key={index}>
      <a href={href} target="_blank" rel="noopener noreferrer">{markdown?.[1] || href}</a>
      {markdown ? "" : part.slice(href.length)}
    </Fragment>;
  });
}

function cleanDisplayText(text: string): string {
  const value = text || "";
  return value
    .replace(/\[(?:\d+(?:\s*[-,，]\s*\d+)*)\]/g, "")
    .replace(/\[(?:product_data|products?_data|产品数据|source|sources)\]/gi, "")
    .replace(/[ \t]{2,}/g, " ")
    .replace(/[ \t]+([,，。！？!?:;；])/g, "$1");
}

export function ChatMessageBubble({ message }: ChatMessageProps) {
  const { t } = useSiteLocale();
  const isUser = message.role === "user";
  const errorPrefixes = ["HTTP ", "Upstream API error", "Request timed out", "请求超时", "Request failed", "No streamed content"];
  const isError =
    message.isError || message.content === "__ERROR__" || errorPrefixes.some((prefix) => message.content.startsWith(prefix));
  const displayContent = cleanDisplayText(message.content);

  return (
    <div className={`chat-message ${isUser ? "chat-message--user" : "chat-message--assistant"}`}>
      <div className="chat-message__avatar">{isUser ? <UserCircle size={14} /> : <ChatCircleDots size={14} />}</div>
      <div className="chat-message__content">
        {isError ? (
          <p className="chat-message__error">
            {message.content === "__ERROR__"
              ? t("请求失败，请稍后重试。", "Request failed. Please try again.")
              : message.content}
          </p>
        ) : (
          <>
            <div className="chat-message__text">
              {linkedText(displayContent)}
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
