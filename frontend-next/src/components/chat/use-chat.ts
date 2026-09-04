"use client";
import { useCallback, useEffect, useRef, useState } from "react";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  products?: string[];
  isStreaming?: boolean;
  isError?: boolean;
};

export function useChat({ locale }: { locale: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  useEffect(() => () => abortRef.current?.abort(), []);

  const sendMessage = useCallback(async (text: string) => {
    const message = text.trim();
    if (!message || message.length > 2000 || abortRef.current) return;
    const controller = new AbortController();
    abortRef.current = controller;
    const id = crypto.randomUUID();
    const history = messages.filter(m => m.content && !m.isError).slice(-6)
      .map(({ role, content }) => ({ role, content: content.slice(0, 2000) }));
    setMessages(prev => [...prev, { id: crypto.randomUUID(), role: "user", content: message }, { id, role: "assistant", content: "" }]);
    setIsLoading(true);
    const timeout = window.setTimeout(() => controller.abort(), 45000);
    try {
      const response = await fetch("/api/v1/chat", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, locale, history }), signal: controller.signal,
      });
      const result = await response.json();
      if (controller.signal.aborted) return;
      const content = typeof result.content === "string" ? result.content : "__ERROR__";
      setMessages(prev => prev.map(item => item.id === id ? { ...item, content, isError: !response.ok || !result.success } : item));
    } catch {
      if (abortRef.current === controller) {
        const content = locale === "en-US" ? "The research request could not finish. Please try again." : "研究请求未能完成，请重试。";
        setMessages(prev => prev.map(item => item.id === id ? { ...item, content, isError: true } : item));
      }
    } finally {
      window.clearTimeout(timeout);
      if (abortRef.current === controller) { abortRef.current = null; setIsLoading(false); }
    }
  }, [locale, messages]);

  const clearMessages = useCallback(() => {
    abortRef.current?.abort(); abortRef.current = null; setMessages([]); setIsLoading(false);
  }, []);
  return { messages, isLoading, sendMessage, clearMessages };
}
