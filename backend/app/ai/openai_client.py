"""OpenAI-compatible LLM client pointed at DeepSeek.

Uses the official ``openai`` SDK with DeepSeek's Chat Completions API so
OpenAI-style tool/function calling works for stock helpers next.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Sequence

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)

from app.config import Settings, get_settings
from app.exceptions import LLMConfigError, LLMRequestError

logger = logging.getLogger(__name__)


def _build_client(settings: Settings) -> OpenAI:
    """Construct an OpenAI SDK client for DeepSeek from settings."""
    api_key = settings.deepseek_api_key.strip()
    if not api_key:
        raise LLMConfigError(
            "DEEPSEEK_API_KEY is not set. Add it to backend/.env."
        )

    return OpenAI(
        api_key=api_key,
        base_url=settings.deepseek_base_url.rstrip("/"),
        timeout=settings.llm_timeout_seconds,
    )


@lru_cache
def get_openai_client() -> OpenAI:
    """Return a cached OpenAI SDK client configured for DeepSeek.

    Reads ``DEEPSEEK_API_KEY`` and ``DEEPSEEK_BASE_URL`` from settings.

    Raises:
        LLMConfigError: If ``DEEPSEEK_API_KEY`` is missing.
    """
    return _build_client(get_settings())


def get_completion(
    messages: Sequence[ChatCompletionMessageParam],
    tools: Sequence[ChatCompletionToolParam] | None = None,
    *,
    model: str | None = None,
    settings: Settings | None = None,
    temperature: float | None = None,
    tool_choice: str | dict[str, object] | None = None,
) -> ChatCompletion:
    """Request a chat completion from DeepSeek (OpenAI-compatible).

    Compatible with OpenAI-style tool/function calling: pass ``tools`` as a
    list of ``{"type": "function", "function": {...}}`` definitions. The
    returned ``ChatCompletion`` may include ``tool_calls`` on the assistant
    message for a later execution loop.

    Args:
        messages: Conversation messages (system / user / assistant / tool).
        tools: Optional OpenAI-format tool definitions.
        model: Override model id (defaults to ``DEEPSEEK_MODEL``).
        settings: Optional settings override (mainly for tests).
        temperature: Optional sampling temperature.
        tool_choice: Optional tool choice (``"auto"``, ``"none"``, or a
            specific function object). Only sent when ``tools`` is provided.

    Returns:
        The full ``ChatCompletion`` response from the API.

    Raises:
        LLMConfigError: Missing API key or empty ``messages``.
        LLMRequestError: Auth, rate-limit, timeout, or other API failures.
    """
    if not messages:
        raise LLMConfigError("messages must not be empty.")

    cfg = settings or get_settings()
    client = _build_client(cfg) if settings is not None else get_openai_client()
    resolved_model = (model or cfg.deepseek_model).strip() or "deepseek-flash"

    kwargs: dict[str, object] = {
        "model": resolved_model,
        "messages": list(messages),
        "stream": False,
    }
    if tools:
        kwargs["tools"] = list(tools)
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice
    if temperature is not None:
        kwargs["temperature"] = temperature

    try:
        response = client.chat.completions.create(**kwargs)
    except AuthenticationError as exc:
        raise LLMRequestError(
            "DeepSeek authentication failed. Check DEEPSEEK_API_KEY."
        ) from exc
    except RateLimitError as exc:
        raise LLMRequestError("DeepSeek rate limit exceeded. Retry later.") from exc
    except APITimeoutError as exc:
        raise LLMRequestError("DeepSeek request timed out.") from exc
    except APIConnectionError as exc:
        raise LLMRequestError(
            f"Could not connect to DeepSeek API: {exc}"
        ) from exc
    except APIStatusError as exc:
        raise LLMRequestError(
            f"DeepSeek API error ({exc.status_code}): {exc.message}"
        ) from exc
    except Exception as exc:
        raise LLMRequestError(f"Unexpected DeepSeek client error: {exc}") from exc

    if not response.choices:
        raise LLMRequestError("DeepSeek returned no completion choices.")

    logger.info(
        "DeepSeek completion model=%s finish_reason=%s",
        resolved_model,
        response.choices[0].finish_reason,
    )
    return response
