from fastapi import FastAPI

from app.api.routes import api_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Stock market data API foundation for Market AI.",
    version="0.1.0",
    debug=settings.debug,
)

app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok", "env": settings.app_env}
