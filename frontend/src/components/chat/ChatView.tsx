"use client";

import { useEffect, useRef, useState } from "react";

import { ChatInput } from "@/components/chat/ChatInput";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { ToolStatus } from "@/components/chat/ToolStatus";
import { streamChat, SUGGESTED_PROMPTS } from "@/lib/chat";
import type { ChatMessage as ChatMessageType, ToolStatusLabel } from "@/types/chat";

function createId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

const WELCOME_MESSAGE: ChatMessageType = {
  id: "welcome",
  role: "assistant",
  content:
    "Hi — I'm **Market AI**. Ask me about stock or crypto prices.\n\nTry `AAPL`, `TSLA`, `BTC`, or `ETH`.",
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
      onEvent: (event) => {
        switch (event.type) {
          case "tool_status":
            setToolStatus(event.status);
            break;
          case "token":
            setMessages((prev) =>
              prev.map((message) =>
                message.id === assistantId
                  ? {
                      ...message,
                      content: message.content + event.content,
                    }
                  : message
              )
            );
            break;
          case "market_data":
            setMessages((prev) =>
              prev.map((message) =>
                message.id === assistantId
                  ? { ...message, marketData: event.data }
                  : message
              )
            );
            break;
          case "error":
            setMessages((prev) =>
              prev.map((message) =>
                message.id === assistantId
                  ? {
                      ...message,
                      content:
                        message.content ||
                        `Something went wrong: ${event.message}`,
                      isStreaming: false,
                    }
                  : message
              )
            );
            break;
          case "done":
            setMessages((prev) =>
              prev.map((message) =>
                message.id === assistantId
                  ? { ...message, isStreaming: false }
                  : message
              )
            );
            break;
        }
      },
    });

    setToolStatus(null);
    setIsLoading(false);
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
        isLoading={isLoading}
      />
    </div>
  );
}
