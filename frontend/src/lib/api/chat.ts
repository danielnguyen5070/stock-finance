import type { ChatStreamEvent, StreamChatCallbacks } from "@/types/chat";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

function getApiBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
    DEFAULT_API_BASE_URL
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseSseEvent(raw: string): ChatStreamEvent | null {
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!isRecord(parsed) || typeof parsed.type !== "string") {
      return null;
    }

    switch (parsed.type) {
      case "tool_start":
        if (typeof parsed.tool !== "string") return null;
        return { type: "tool_start", tool: parsed.tool };
      case "tool_result":
        if (typeof parsed.tool !== "string") return null;
        return {
          type: "tool_result",
          tool: parsed.tool,
          data: parsed.data,
        };
      case "token":
        if (typeof parsed.content !== "string") return null;
        return { type: "token", content: parsed.content };
      case "done":
        return { type: "done" };
      case "error":
        if (typeof parsed.message !== "string") return null;
        return { type: "error", message: parsed.message };
      default:
        return null;
    }
  } catch {
    return null;
  }
}

function dispatchEvent(event: ChatStreamEvent, callbacks: StreamChatCallbacks) {
  switch (event.type) {
    case "tool_start":
      callbacks.onToolStart?.(event.tool);
      break;
    case "tool_result":
      callbacks.onToolResult?.(event.tool, event.data);
      break;
    case "token":
      callbacks.onToken?.(event.content);
      break;
    case "done":
      callbacks.onDone?.();
      break;
    case "error":
      callbacks.onError?.(event.message);
      break;
  }
}

/**
 * Consume one or more complete SSE frames from `buffer`.
 * Incomplete trailing data stays in the returned remainder.
 */
function consumeSseBuffer(
  buffer: string,
  callbacks: StreamChatCallbacks
): string {
  const frames = buffer.split("\n\n");
  const remainder = frames.pop() ?? "";

  for (const frame of frames) {
    const lines = frame.split(/\r?\n/);
    for (const line of lines) {
      if (!line.startsWith("data:")) continue;
      const payload = line.slice(5).trimStart();
      if (!payload || payload === "[DONE]") continue;
      const event = parseSseEvent(payload);
      if (event) {
        dispatchEvent(event, callbacks);
      }
    }
  }

  return remainder;
}

/**
 * Stream a chat reply from the FastAPI SSE endpoint.
 *
 * POST `{API}/chat/stream` with `{ message }`, then parse `data:` JSON events.
 * Supports multi-event network chunks and events split across chunks.
 */
export async function streamChat(
  message: string,
  callbacks: StreamChatCallbacks = {}
): Promise<void> {
  const trimmed = message.trim();
  if (!trimmed) {
    callbacks.onError?.("Message must not be empty.");
    return;
  }

  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify({ message: trimmed }),
      signal: callbacks.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      return;
    }
    const text =
      error instanceof Error ? error.message : "Failed to reach chat API";
    callbacks.onError?.(text);
    return;
  }

  if (!response.ok) {
    let detail = `Chat request failed (${response.status})`;
    try {
      const body: unknown = await response.json();
      if (isRecord(body) && typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // ignore body parse errors
    }
    callbacks.onError?.(detail);
    return;
  }

  if (!response.body) {
    callbacks.onError?.("Chat stream response has no body.");
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        buffer += decoder.decode();
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      buffer = consumeSseBuffer(buffer, callbacks);
    }

    if (buffer.trim()) {
      consumeSseBuffer(`${buffer}\n\n`, callbacks);
    }
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      return;
    }
    const text =
      error instanceof Error ? error.message : "Chat stream interrupted";
    callbacks.onError?.(text);
  } finally {
    reader.releaseLock();
  }
}
