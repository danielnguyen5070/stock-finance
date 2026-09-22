import {
  MOCK_CRYPTO_QUOTES,
  MOCK_STOCK_QUOTES,
} from "@/lib/chat/mock-data";
import type {
  ChatStreamEvent,
  ChatStreamHandlers,
  MarketQuote,
  ToolStatusLabel,
} from "@/types/chat";

function sleep(ms: number, signal?: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException("Aborted", "AbortError"));
      return;
    }

    const timeout = setTimeout(resolve, ms);

    signal?.addEventListener(
      "abort",
      () => {
        clearTimeout(timeout);
        reject(new DOMException("Aborted", "AbortError"));
      },
      { once: true }
    );
  });
}

function findQuote(message: string): MarketQuote | null {
  const upper = message.toUpperCase();

  for (const symbol of Object.keys(MOCK_CRYPTO_QUOTES)) {
    if (
      upper.includes(symbol) ||
      (symbol === "BTC" && /BITCOIN/.test(upper)) ||
      (symbol === "ETH" && /ETHEREUM/.test(upper)) ||
      (symbol === "SOL" && /SOLANA/.test(upper))
    ) {
      return MOCK_CRYPTO_QUOTES[symbol];
    }
  }

  for (const symbol of Object.keys(MOCK_STOCK_QUOTES)) {
    if (upper.includes(symbol)) {
      return MOCK_STOCK_QUOTES[symbol];
    }
  }

  if (/\b(CRYPTO|COIN)\b/.test(upper)) {
    return MOCK_CRYPTO_QUOTES.BTC;
  }

  if (/\b(STOCK|SHARE|EQUITY)\b/.test(upper)) {
    return MOCK_STOCK_QUOTES.AAPL;
  }

  return null;
}

function buildMarkdown(quote: MarketQuote | null, userMessage: string): string {
  if (!quote) {
    return [
      "I can help with **stocks** and **crypto** prices.",
      "",
      "Try asking about symbols like `AAPL`, `TSLA`, `BTC`, or `ETH`.",
      "",
      `You asked: _${userMessage.trim() || "…"}_`,
    ].join("\n");
  }

  const direction = quote.change24h >= 0 ? "up" : "down";
  const assetLabel = quote.assetType === "crypto" ? "cryptocurrency" : "stock";

  return [
    `Here's the latest mock quote for **${quote.symbol}** (${assetLabel}).`,
    "",
    `- Price: **${quote.price.toLocaleString("en-US", {
      style: "currency",
      currency: quote.currency,
    })}**`,
    `- 24h change: **${direction} ${Math.abs(quote.change24h).toFixed(2)}%**`,
    "",
    "_This is mock data — ready to swap for a live FastAPI stream._",
  ].join("\n");
}

async function emit(
  handlers: ChatStreamHandlers,
  event: ChatStreamEvent
) {
  if (handlers.signal?.aborted) {
    throw new DOMException("Aborted", "AbortError");
  }
  handlers.onEvent(event);
}

/**
 * Mock streaming chat. Replace the body with a FastAPI SSE fetch later;
 * keep the same ChatStreamEvent shape so the UI stays unchanged.
 */
export async function streamChat(
  message: string,
  handlers: ChatStreamHandlers
): Promise<void> {
  const quote = findQuote(message);

  const toolStatuses: ToolStatusLabel[] = quote
    ? [
        "Analyzing...",
        quote.assetType === "crypto"
          ? "Getting crypto price..."
          : "Getting stock price...",
      ]
    : ["Analyzing..."];

  try {
    for (const status of toolStatuses) {
      await emit(handlers, { type: "tool_status", status });
      await sleep(700, handlers.signal);
    }

    await emit(handlers, { type: "tool_status", status: null });

    if (quote) {
      await emit(handlers, { type: "market_data", data: quote });
      await sleep(200, handlers.signal);
    }

    const markdown = buildMarkdown(quote, message);
    const chunkSize = 12;

    for (let i = 0; i < markdown.length; i += chunkSize) {
      await emit(handlers, {
        type: "token",
        content: markdown.slice(i, i + chunkSize),
      });
      await sleep(28, handlers.signal);
    }

    await emit(handlers, { type: "done" });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      return;
    }

    const messageText =
      error instanceof Error ? error.message : "Unknown streaming error";
    await emit(handlers, { type: "error", message: messageText });
  }
}
