# Market AI

Simple Next.js chat UI for stock & crypto questions. Uses mock streaming for now — designed to plug into a Python FastAPI SSE API later.

## Stack

- Next.js App Router + TypeScript
- Tailwind CSS + shadcn/ui
- `react-markdown` for assistant replies

## Getting started

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Project layout

- `src/app` — App Router pages
- `src/components/chat` — `ChatMessage`, `ChatInput`, `ToolStatus`, `MarketCard`, `ChatView`
- `src/lib/chat` — mock stream client (`streamChat`) and sample quotes
- `src/types/chat.ts` — shared message / stream event types

## Connecting FastAPI later

Keep the `ChatStreamEvent` shape in `src/types/chat.ts` and swap the body of `streamChat` in `src/lib/chat/client.ts` for an SSE/`fetch` stream against your API. The React UI already handles:

- `tool_status`
- `token`
- `market_data`
- `done`
- `error`
