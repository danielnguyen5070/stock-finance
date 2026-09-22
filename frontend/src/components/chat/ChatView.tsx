"use client";

import { useEffect, useRef, useState } from "react";

import { ChatInput } from "@/components/chat/ChatInput";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { ToolStatus } from "@/components/chat/ToolStatus";
import { streamChat } from "@/lib/api/chat";
import { SUGGESTED_PROMPTS } from "@/lib/chat/prompts";
import type {
  ChatMessage as ChatMessageType,
  StockQuote,
  ToolStatusLabel,
} from "@/types/chat";

function createId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function toolStatusLabel(tool: string): ToolStatusLabel {
  switch (tool) {
    case "get_symbol":
      return "Finding stock symbol...";
    case "get_stock_price":
      return "Getting stock price...";
    default:
      return "Working...";
  }
}

function isStockQuote(data: unknown): data is StockQuote {
  if (typeof data !== "object" || data === null) return false;
  const record = data as Record<string, unknown>;
  return (
    typeof record.symbol === "string" &&
    typeof record.timestamp === "string" &&
    typeof record.open === "number" &&
    typeof record.high === "number" &&
    typeof record.low === "number" &&
    typeof record.close === "number" &&
    typeof record.volume === "number"
  );
}

const WELCOME_MESSAGE: ChatMessageType = {
  id: "welcome",
  role: "assistant",
  content:
    "Hi — I'm **Market AI**. Ask me about stock prices.\n\nTry `Nvidia`, `Apple`, or `What's the price of AAPL?`.",
  createdAt: new Date().toISOString(),
};

export function ChatView() {
  const [messages, setMessages] = useState<ChatMessageType[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [toolStatus, setToolStatus] = useState<ToolStatusLabel | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, toolStatus, isLoading]);

  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  function stopGeneration() {
    abortRef.current?.abort();
    abortRef.current = null;
    setToolStatus(null);
    setIsLoading(false);
    setMessages((prev) =>
      prev.map((message) =>
        message.isStreaming ? { ...message, isStreaming: false } : message
      )
    );
  }

  async function sendMessage(raw: string) {
    const content = raw.trim();
    if (!content || isLoading) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    const userMessage: ChatMessageType = {
      id: createId(),
      role: "user",
      content,
      createdAt: new Date().toISOString(),
    };

    const assistantId = createId();
    const assistantMessage: ChatMessageType = {
      id: assistantId,
      role: "assistant",
      content: "",
      createdAt: new Date().toISOString(),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setInput("");
    setIsLoading(true);
    setToolStatus(null);

    await streamChat(content, {
      signal: controller.signal,
      onToolStart: (tool) => {
        setToolStatus(toolStatusLabel(tool));
      },
      onToolResult: (tool, data) => {
        if (tool === "get_stock_price" && isStockQuote(data)) {
          setMessages((prev) =>
            prev.map((message) =>
              message.id === assistantId
                ? { ...message, stockQuote: data }
                : message
            )
          );
        }
        setToolStatus(null);
      },
      onToken: (token) => {
        setToolStatus(null);
        setMessages((prev) =>
          prev.map((message) =>
            message.id === assistantId
              ? { ...message, content: message.content + token }
              : message
          )
        );
      },
      onDone: () => {
        setMessages((prev) =>
          prev.map((message) =>
            message.id === assistantId
              ? { ...message, isStreaming: false }
              : message
          )
        );
      },
      onError: (errorMessage) => {
        setMessages((prev) =>
          prev.map((message) =>
            message.id === assistantId
              ? {
                  ...message,
                  content:
                    message.content ||
                    `Something went wrong: ${errorMessage}`,
                  isStreaming: false,
                }
              : message
          )
        );
      },
    });

    if (!controller.signal.aborted) {
      setToolStatus(null);
      setIsLoading(false);
      setMessages((prev) =>
        prev.map((message) =>
          message.id === assistantId
            ? { ...message, isStreaming: false }
            : message
        )
      );
    }
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto flex w-full max-w-2xl flex-col gap-5 px-3 py-6 sm:px-4">
          {messages.length === 1 ? (
            <div className="mb-2 grid gap-2 sm:grid-cols-2">
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => sendMessage(prompt)}
                  disabled={isLoading}
                  className="rounded-xl border border-border/80 bg-card px-3 py-2.5 text-left text-sm text-muted-foreground transition-colors hover:bg-muted/60 hover:text-foreground disabled:opacity-50"
                >
                  {prompt}
                </button>
              ))}
            </div>
          ) : null}

          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}

          {toolStatus ? <ToolStatus status={toolStatus} /> : null}

          <div ref={bottomRef} />
        </div>
      </div>

      <ChatInput
        value={input}
        onChange={setInput}
        onSubmit={() => sendMessage(input)}
        onStop={stopGeneration}
        isLoading={isLoading}
      />
    </div>
  );
}
