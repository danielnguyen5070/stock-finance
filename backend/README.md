# Market AI — Backend

Python FastAPI foundation for stock (and later crypto) market data.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run API

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

- Health: [http://localhost:8000/health](http://localhost:8000/health)
- Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Chat: `POST /chat` with `{"message": "..."}`
- Symbol: `GET /stocks/symbol?company=Nvidia`
- Price: `GET /stocks/NVDA/price`

## Test services locally (no server)

```bash
cd backend
source .venv/bin/activate
python scripts/test_stock.py
python scripts/test_stock.py --company "Apple"
```

With ``DEEPSEEK_API_KEY`` set in `.env`:

```bash
python scripts/test_llm.py
python scripts/test_llm.py --prompt "Say hello in one word"
python scripts/test_agent.py
python scripts/test_agent.py --question "What is Apple's stock price?" --verbose
```

## Layout

```
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # pydantic-settings / .env
│   ├── exceptions.py
│   ├── ai/
│   │   ├── openai_client.py # DeepSeek via OpenAI SDK
│   │   ├── tools.py         # OpenAI tool defs + FUNCTION_MAP
│   │   └── agent.py         # Tool-calling loop (run_agent)
│   ├── api/
│   │   ├── chat.py          # POST /chat
│   │   └── routes/stocks.py # Stock HTTP endpoints
│   ├── models/stock.py      # TypedDict shapes
│   └── services/stock.py    # get_symbol, get_stock_price
├── scripts/test_stock.py    # CLI smoke test (stocks)
├── scripts/test_llm.py      # CLI smoke test (DeepSeek)
├── scripts/test_agent.py    # CLI smoke test (tool-calling agent)
├── .env.example
└── requirements.txt
```

`get_crypto_price()` can follow the same pattern in `services/crypto.py` later.
