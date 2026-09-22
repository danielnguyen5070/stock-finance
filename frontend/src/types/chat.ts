export type MessageRole = "user" | "assistant";

export type ToolStatusLabel =
  | "Analyzing..."
  | "Getting stock price..."
  | "Getting crypto price...";

export type MarketAssetType = "stock" | "crypto";

export interface MarketQuote {
  symbol: string;
  price: number;
  change24h: number;
  currency: string;
  assetType: MarketAssetType;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: string;
  marketData?: MarketQuote;
  isStreaming?: boolean;
}

/** Stream events shaped for a future FastAPI SSE / streaming endpoint. */
export type ChatStreamEvent =
  | { type: "tool_status"; status: ToolStatusLabel | null }
  | { type: "token"; content: string }
  | { type: "market_data"; data: MarketQuote }
  | { type: "done" }
  | { type: "error"; message: string };

export interface ChatStreamHandlers {
  onEvent: (event: ChatStreamEvent) => void;
  signal?: AbortSignal;
}
