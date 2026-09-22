from fastapi import FastAPI

from app.api import chat
from app.api.routes import api_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "Market AI backend: stock data helpers and a DeepSeek-powered chat agent. "
        "Use `POST /chat` for non-streaming answers; streaming will be added later."
    ),
    version="0.1.0",
    debug=settings.debug,
)

app.include_router(api_router)
app.include_router(chat.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok", "env": settings.app_env}
