/**
 * Chat API surface.
 *
 * Today: mock streaming via `streamChat`.
 * Later: point `streamChat` at a FastAPI SSE endpoint, e.g.
 *
 *   POST /api/chat  (or GET /api/chat/stream)
 *   events: tool_status | token | market_data | done | error
 *
 * Keep `ChatStreamEvent` stable so React components do not need to change.
 */
export { streamChat } from "@/lib/chat/client";
export {
  MOCK_CRYPTO_QUOTES,
  MOCK_STOCK_QUOTES,
  SUGGESTED_PROMPTS,
} from "@/lib/chat/mock-data";
