# Market AI

Stock & crypto chatbot — Next.js frontend with a FastAPI backend (coming soon).

## Structure

```
stock-finance/
├── frontend/   # Next.js App Router UI (Market AI chat)
└── backend/    # Python FastAPI (placeholder)
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

Mock streaming is wired today; swap `frontend/src/lib/chat/client.ts` for a FastAPI SSE client later.
