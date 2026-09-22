# Market AI

Stock & crypto chatbot — Next.js frontend with a FastAPI backend.

## Structure

```
stock-finance/
├── frontend/   # Next.js App Router UI (Market AI chat)
└── backend/    # Python FastAPI (stock data services)
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Smoke-test stock helpers without the server:

```bash
cd backend && source .venv/bin/activate
python scripts/test_stock.py --company "Nvidia"
```

See `backend/README.md` for API routes and layout.

