"""AI / LLM helpers (DeepSeek via OpenAI SDK)."""

from app.ai.openai_client import get_completion, get_openai_client

__all__ = ["get_completion", "get_openai_client"]
