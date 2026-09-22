# Market AI — Frontend

Next.js chat UI that streams replies from the FastAPI SSE endpoint.

## Stack

- Next.js App Router + TypeScript
- Tailwind CSS + shadcn/ui
- `react-markdown` for assistant replies

## Getting started

Run the backend first (`uvicorn` on port 8000), then:

```bash
cd frontend
cp .env.example .env.local   # optional; defaults to http://127.0.0.1:8000
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Project layout

- `src/app` — App Router pages
- `src/components/chat` — chat UI components
- `src/lib/api/chat.ts` — SSE client for `POST /chat/stream`
- `src/types/chat.ts` — shared message / stream event types

## SSE events consumed

- `tool_start` / `tool_result`
- `token`
- `done`
- `error`
