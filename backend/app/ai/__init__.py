"""AI / LLM helpers (DeepSeek via OpenAI SDK)."""

from app.ai.agent import run_agent
from app.ai.openai_client import get_completion, get_openai_client
from app.ai.tools import FUNCTION_MAP, make_openai_tool, tools

__all__ = [
    "FUNCTION_MAP",
    "get_completion",
    "get_openai_client",
    "make_openai_tool",
    "run_agent",
    "tools",
]
