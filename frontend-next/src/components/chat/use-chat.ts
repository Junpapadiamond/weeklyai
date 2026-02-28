"use client";

import { useCallback, useMemo, useRef, useState } from "react";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  products?: string[];
  isStreaming?: boolean;
};

type UseChatOptions = {
  locale: string;
};

type StreamMode = "auto" | "json" | "sse";

const API_BASE =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000/api/v1").trim()
    : "http://localhost:5000/api/v1";

const STREAM_MODE_RAW =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_CHAT_STREAM_MODE || "auto").trim().toLowerCase()
    : "auto";

const TYPE_INTERVAL_MS = 18;
const SSE_TIMEOUT_MS = 12000;
const JSON_TIMEOUT_MS = 12000;

function resolveStreamMode(raw: string): StreamMode {
  if (raw === "sse" || raw === "json") return raw;
  return "auto";
}

let messageCounter = 0;
function nextMessageId() {
  messageCounter += 1;
  return `msg-${Date.now()}-${messageCounter}`;
}

export function useChat({ locale }: UseChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const typingRef = useRef<number | null>(null);
  const streamMode = useMemo(() => resolveStreamMode(STREAM_MODE_RAW), []);

  const clearTyping = useCallback(() => {
    if (typingRef.current !== null) {
      window.clearInterval(typingRef.current);
      typingRef.current = null;
    }
  }, []);

  const patchAssistant = useCallback((assistantId: string, patch: Partial<ChatMessage>) => {
    setMessages((prev) => prev.map((item) => (item.id === assistantId ? { ...item, ...patch } : item)));
  }, []);

  const appendAssistantText = useCallback((assistantId: string, chunk: string) => {
    setMessages((prev) =>
      prev.map((item) =>
        item.id === assistantId
          ? {
              ...item,
              content: `${item.content}${chunk}`,
            }
          : item
      )
    );
  }, []);

  const playTypewriter = useCallback(
    (assistantId: string, fullContent: string, signal: AbortSignal) =>
      new Promise<boolean>((resolve) => {
        let index = 0;
        clearTyping();

        typingRef.current = window.setInterval(() => {
          if (signal.aborted) {
            clearTyping();
            resolve(false);
            return;
          }

          index += 2;
          const partial = fullContent.slice(0, index);
          const done = index >= fullContent.length;

          patchAssistant(assistantId, { content: partial, isStreaming: !done });

          if (done) {
            clearTyping();
            resolve(true);
          }
        }, TYPE_INTERVAL_MS);
      }),
    [clearTyping, patchAssistant]
  );

  const consumeSse = useCallback(
    async (
      assistantId: string,
      text: string,
      controller: AbortController
    ): Promise<{ ok: boolean; errorMessage?: string }> => {
      const timeoutId = window.setTimeout(() => {
        controller.abort();
      }, SSE_TIMEOUT_MS);

      try {
        const response = await fetch(`${API_BASE}/chat?stream=1`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
          },
          body: JSON.stringify({ message: text, locale, stream: true }),
          signal: controller.signal,
        });

        if (!response.ok) {
          let errorMessage = "";
          try {
            const payload = (await response.json()) as { content?: string; message?: string };
            errorMessage = String(payload.content || payload.message || "").trim();
          } catch {
            // ignore parsing errors
          }
          return { ok: false, errorMessage: errorMessage || `HTTP ${response.status}` };
        }

        if (!response.body) {
          return { ok: false, errorMessage: "Empty stream body." };
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let hasText = false;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const rawLine of lines) {
            const line = rawLine.trim();
            if (!line.startsWith("data:")) continue;

            const payload = line.slice(5).trim();
            if (!payload || payload === "[DONE]") continue;

            let parsed: { type?: string; content?: string; message?: string } = {};
            try {
              parsed = JSON.parse(payload) as typeof parsed;
            } catch {
              continue;
            }

            if (parsed.type === "text" && parsed.content) {
              hasText = true;
              appendAssistantText(assistantId, parsed.content);
              continue;
            }

            if (parsed.type === "error") {
              return {
                ok: false,
                errorMessage: String(parsed.message || "").trim() || "Stream request failed.",
              };
            }

            if (parsed.type === "done") {
              patchAssistant(assistantId, { isStreaming: false });
            }
          }
        }

        if (!hasText) {
          return { ok: false, errorMessage: "No streamed content received." };
        }

        patchAssistant(assistantId, { isStreaming: false });
        return { ok: true };
      } catch (error) {
        if ((error as Error).name === "AbortError") {
          return { ok: false, errorMessage: "SSE timeout, switching to JSON mode." };
        }
        throw error;
      } finally {
        window.clearTimeout(timeoutId);
      }
    },
    [appendAssistantText, locale, patchAssistant]
  );

  const consumeJson = useCallback(
    async (
      assistantId: string,
      text: string,
      controller: AbortController
    ): Promise<{ ok: boolean; errorMessage?: string }> => {
      const timeoutId = window.setTimeout(() => {
        controller.abort();
      }, JSON_TIMEOUT_MS);

      try {
        const response = await fetch(`${API_BASE}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text, locale }),
          signal: controller.signal,
        });

        let payload: { success?: boolean; content?: string; message?: string } = {};
        try {
          payload = (await response.json()) as typeof payload;
        } catch {
          // ignore parsing errors
        }

        const fullContent = String(payload.content || payload.message || "").trim();
        if (!response.ok || !payload.success || !fullContent) {
          return {
            ok: false,
            errorMessage: fullContent || (response.ok ? "Empty response content." : `HTTP ${response.status}`),
          };
        }

        patchAssistant(assistantId, { content: "", isStreaming: true });
        const ok = await playTypewriter(assistantId, fullContent, controller.signal);
        return ok ? { ok: true } : { ok: false, errorMessage: "Request cancelled." };
      } catch (error) {
        if ((error as Error).name === "AbortError") {
          return { ok: false, errorMessage: "Request timed out. Please try again." };
        }
        throw error;
      } finally {
        window.clearTimeout(timeoutId);
      }
    },
    [locale, patchAssistant, playTypewriter]
  );

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isLoading) return;

      clearTyping();

      const userMessage: ChatMessage = {
        id: nextMessageId(),
        role: "user",
        content: trimmed,
      };

      const assistantId = nextMessageId();
      const assistantMessage: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsLoading(true);

      abortRef.current?.abort();
      const requestController = new AbortController();
      abortRef.current = requestController;

      try {
        let result: { ok: boolean; errorMessage?: string } = { ok: false };

        if (streamMode !== "json") {
          const sseController = new AbortController();
          const relayAbort = () => sseController.abort();
          requestController.signal.addEventListener("abort", relayAbort, { once: true });
          result = await consumeSse(assistantId, trimmed, sseController);
          requestController.signal.removeEventListener("abort", relayAbort);
        }

        if (!result.ok && streamMode !== "sse" && !requestController.signal.aborted) {
          const jsonController = new AbortController();
          const relayAbort = () => jsonController.abort();
          requestController.signal.addEventListener("abort", relayAbort, { once: true });
          patchAssistant(assistantId, { content: "", isStreaming: true });
          result = await consumeJson(assistantId, trimmed, jsonController);
          requestController.signal.removeEventListener("abort", relayAbort);
        }

        if (!result.ok) {
          patchAssistant(assistantId, {
            content: String(result.errorMessage || "").trim() || "__ERROR__",
            isStreaming: false,
          });
        }
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          patchAssistant(assistantId, { content: "__ERROR__", isStreaming: false });
        }
      } finally {
        clearTyping();
        if (abortRef.current === requestController) {
          abortRef.current = null;
        }
        setIsLoading(false);
      }
    },
    [clearTyping, consumeJson, consumeSse, isLoading, patchAssistant, streamMode]
  );

  const clearMessages = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    clearTyping();
    setMessages([]);
    setIsLoading(false);
  }, [clearTyping]);

  return { messages, isLoading, sendMessage, clearMessages };
}
