"""OpenAI-compatible LLM client pointed at DeepSeek.

Uses the official ``openai`` SDK with DeepSeek's Chat Completions API so
OpenAI-style tool/function calling and streaming both work for the agent.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator, Sequence
from functools import lru_cache
from typing import Any

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
    ChatCompletionChunk,
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
    """Return a cached OpenAI SDK client configured for DeepSeek."""
    return _build_client(get_settings())


def _resolve_client_and_model(
    *,
    model: str | None,
    settings: Settings | None,
) -> tuple[OpenAI, str]:
    cfg = settings or get_settings()
    client = _build_client(cfg) if settings is not None else get_openai_client()
    resolved_model = (model or cfg.deepseek_model).strip() or "deepseek-flash"
    return client, resolved_model


def _build_request_kwargs(
    messages: Sequence[ChatCompletionMessageParam],
    tools: Sequence[ChatCompletionToolParam] | None,
    *,
    model: str,
    stream: bool,
    temperature: float | None,
    tool_choice: str | dict[str, object] | None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": list(messages),
        "stream": stream,
    }
    if tools:
        kwargs["tools"] = list(tools)
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice
    if temperature is not None:
        kwargs["temperature"] = temperature
    return kwargs


def _translate_openai_error(exc: Exception) -> LLMRequestError:
    if isinstance(exc, AuthenticationError):
        return LLMRequestError(
            "DeepSeek authentication failed. Check DEEPSEEK_API_KEY."
        )
    if isinstance(exc, RateLimitError):
        return LLMRequestError("DeepSeek rate limit exceeded. Retry later.")
    if isinstance(exc, APITimeoutError):
        return LLMRequestError("DeepSeek request timed out.")
    if isinstance(exc, APIConnectionError):
        return LLMRequestError(f"Could not connect to DeepSeek API: {exc}")
    if isinstance(exc, APIStatusError):
        return LLMRequestError(
            f"DeepSeek API error ({exc.status_code}): {exc.message}"
        )
    return LLMRequestError(f"Unexpected DeepSeek client error: {exc}")


def get_completion(
    messages: Sequence[ChatCompletionMessageParam],
    tools: Sequence[ChatCompletionToolParam] | None = None,
    *,
    model: str | None = None,
    settings: Settings | None = None,
    temperature: float | None = None,
    tool_choice: str | dict[str, object] | None = None,
) -> ChatCompletion:
    """Request a non-streaming chat completion from DeepSeek."""
    if not messages:
        raise LLMConfigError("messages must not be empty.")

    client, resolved_model = _resolve_client_and_model(
        model=model, settings=settings
    )
    kwargs = _build_request_kwargs(
        messages,
        tools,
        model=resolved_model,
        stream=False,
        temperature=temperature,
        tool_choice=tool_choice,
    )

    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as exc:
        raise _translate_openai_error(exc) from exc

    if not response.choices:
        raise LLMRequestError("DeepSeek returned no completion choices.")

    logger.info(
        "DeepSeek completion model=%s finish_reason=%s",
        resolved_model,
        response.choices[0].finish_reason,
    )
    return response


def stream_completion(
    messages: Sequence[ChatCompletionMessageParam],
    tools: Sequence[ChatCompletionToolParam] | None = None,
    *,
    model: str | None = None,
    settings: Settings | None = None,
    temperature: float | None = None,
    tool_choice: str | dict[str, object] | None = None,
) -> Iterator[dict[str, Any]]:
    """Stream a chat completion from DeepSeek.

    Yields:
        ``{"event": "token", "content": "..."}`` for each content delta while
        the turn still looks like a final answer (no tool-call deltas yet).
        ``{"event": "end", "content": str, "tool_calls": list, "finish_reason": ...}``
        when the provider stream finishes.
    """
    if not messages:
        raise LLMConfigError("messages must not be empty.")

    client, resolved_model = _resolve_client_and_model(
        model=model, settings=settings
    )
    kwargs = _build_request_kwargs(
        messages,
        tools,
        model=resolved_model,
        stream=True,
        temperature=temperature,
        tool_choice=tool_choice,
    )

    try:
        stream = client.chat.completions.create(**kwargs)
    except Exception as exc:
        raise _translate_openai_error(exc) from exc

    content_parts: list[str] = []
    tool_calls_acc: dict[int, dict[str, Any]] = {}
    finish_reason: str | None = None
    saw_tool_calls = False

    try:
        for chunk in stream:
            chunk_finish, deltas = _consume_chunk(chunk)
            if chunk_finish:
                finish_reason = chunk_finish

            for index, patch in deltas["tool_patches"]:
                saw_tool_calls = True
                _merge_tool_call(tool_calls_acc, index, patch)

            for token in deltas["tokens"]:
                content_parts.append(token)
                if not saw_tool_calls:
                    yield {"event": "token", "content": token}
    except Exception as exc:
        raise _translate_openai_error(exc) from exc

    tool_calls = [tool_calls_acc[index] for index in sorted(tool_calls_acc)]
    full_content = "".join(content_parts)

    logger.info(
        "DeepSeek stream end model=%s finish_reason=%s tool_calls=%s",
        resolved_model,
        finish_reason,
        len(tool_calls),
    )
    yield {
        "event": "end",
        "content": full_content,
        "tool_calls": tool_calls,
        "finish_reason": finish_reason,
    }


def _consume_chunk(
    chunk: ChatCompletionChunk,
) -> tuple[str | None, dict[str, Any]]:
    """Extract finish_reason, content tokens, and tool-call patches from a chunk."""
    if not chunk.choices:
        return None, {"tokens": [], "tool_patches": []}

    choice = chunk.choices[0]
    delta = choice.delta
    tokens: list[str] = []
    tool_patches: list[tuple[int, dict[str, Any]]] = []

    if delta and delta.content:
        tokens.append(delta.content)

    if delta and delta.tool_calls:
        for tool_delta in delta.tool_calls:
            index = tool_delta.index if tool_delta.index is not None else 0
            patch: dict[str, Any] = {}
            if tool_delta.id:
                patch["id"] = tool_delta.id
            if tool_delta.type:
                patch["type"] = tool_delta.type
            if tool_delta.function:
                fn_patch: dict[str, str] = {}
                if tool_delta.function.name:
                    fn_patch["name"] = tool_delta.function.name
                if tool_delta.function.arguments:
                    fn_patch["arguments"] = tool_delta.function.arguments
                if fn_patch:
                    patch["function"] = fn_patch
            tool_patches.append((index, patch))

    return choice.finish_reason, {"tokens": tokens, "tool_patches": tool_patches}


def _merge_tool_call(
    acc: dict[int, dict[str, Any]],
    index: int,
    patch: dict[str, Any],
) -> None:
    """Merge a streamed tool-call delta into the accumulator."""
    entry = acc.setdefault(
        index,
        {
            "id": "",
            "type": "function",
            "function": {"name": "", "arguments": ""},
        },
    )
    if "id" in patch:
        entry["id"] = patch["id"]
    if "type" in patch:
        entry["type"] = patch["type"]
    fn_patch = patch.get("function") or {}
    if "name" in fn_patch:
        entry["function"]["name"] += fn_patch["name"]
    if "arguments" in fn_patch:
        entry["function"]["arguments"] += fn_patch["arguments"]
