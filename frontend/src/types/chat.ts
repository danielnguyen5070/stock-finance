export type MessageRole = "user" | "assistant";

export type ToolName = "get_symbol" | "get_stock_price" | (string & {});

export type ToolStatusLabel =
  | "Finding stock symbol..."
  | "Getting stock price..."
  | "Working...";

/** OHLCV payload from FastAPI `get_stock_price` tool_result. */
export interface StockQuote {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: string;
  stockQuote?: StockQuote;
  isStreaming?: boolean;
}

/** SSE event payloads from `POST /chat/stream`. */
export type ChatStreamEvent =
  | { type: "tool_start"; tool: string }
  | { type: "tool_result"; tool: string; data: unknown }
  | { type: "token"; content: string }
  | { type: "done" }
  | { type: "error"; message: string };

export interface StreamChatCallbacks {
  onToolStart?: (tool: string) => void;
  onToolResult?: (tool: string, data: unknown) => void;
  onToken?: (content: string) => void;
  onDone?: () => void;
  onError?: (message: string) => void;
  signal?: AbortSignal;
}
