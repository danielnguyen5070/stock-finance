"""Tool-calling agent loop for the stock chatbot.

Orchestrates DeepSeek completions with OpenAI-style tools from
``app.ai.tools``. Supports blocking (``run_agent``) and SSE-oriented
streaming (``run_agent_stream``).
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from datetime import date, datetime
from typing import Any

from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCall,
)

from app.ai.openai_client import get_completion, stream_completion
from app.ai.tools import FUNCTION_MAP, tools
from app.exceptions import LLMConfigError, LLMError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are Market AI, a helpful stock market assistant. "
    "Use the provided tools to look up ticker symbols and stock prices when needed. "
    "Prefer calling tools rather than guessing prices or symbols. "
    "When you have enough data, answer clearly and concisely for the user. "
    "You may reply in the same language the user used."
)

# Safety cap so a buggy model cannot loop forever.
DEFAULT_MAX_ROUNDS = 8

AgentEvent = dict[str, Any]


class AgentError(LLMError):
    """Raised when the agent cannot produce a final answer."""


def run_agent(
    question: str,
    *,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
) -> str:
    """Run a DeepSeek tool-calling loop for a single user question.

    Returns:
        Final assistant text content.
    """
    messages = _initial_messages(question, max_rounds=max_rounds)

    for round_index in range(1, max_rounds + 1):
        logger.info("Agent round %s/%s", round_index, max_rounds)
        completion = get_completion(messages, tools=tools)
        message = completion.choices[0].message

        tool_calls = message.tool_calls or []
        if not tool_calls:
            text = (message.content or "").strip()
            if text:
                return text
            raise AgentError("Model returned an empty final response.")

        messages.append(_assistant_tool_call_message(message))

        for tool_call in tool_calls:
            result_content, _ = _execute_tool_call(
                name=tool_call.function.name,
                arguments_json=tool_call.function.arguments or "{}",
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_content,
                }
            )

    raise AgentError(
        f"Agent stopped after {max_rounds} rounds without a final answer."
    )


def run_agent_stream(
    question: str,
    *,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
) -> Iterator[AgentEvent]:
    """Yield agent events for SSE while running the tool-calling loop.

    Event shapes:
        ``{"type": "tool_start", "tool": "..."}``
        ``{"type": "tool_result", "tool": "...", "data": ...}``
        ``{"type": "token", "content": "..."}``
        ``{"type": "done"}``
        ``{"type": "error", "message": "..."}``
    """
    try:
        messages = _initial_messages(question, max_rounds=max_rounds)
        yielded_tokens = False

        for round_index in range(1, max_rounds + 1):
            logger.info("Agent stream round %s/%s", round_index, max_rounds)

            end_event: dict[str, Any] | None = None
            for event in stream_completion(messages, tools=tools):
                if event["event"] == "token":
                    yielded_tokens = True
                    yield {"type": "token", "content": event["content"]}
                elif event["event"] == "end":
                    end_event = event

            if end_event is None:
                yield {
                    "type": "error",
                    "message": "DeepSeek stream ended without a completion.",
                }
                return

            tool_calls = end_event.get("tool_calls") or []
            if not tool_calls:
                text = (end_event.get("content") or "").strip()
                if not text and not yielded_tokens:
                    yield {
                        "type": "error",
                        "message": "Model returned an empty final response.",
                    }
                    return
                yield {"type": "done"}
                return

            messages.append(_assistant_tool_calls_from_dicts(tool_calls))

            for tool_call in tool_calls:
                name = tool_call["function"]["name"]
                arguments_json = tool_call["function"].get("arguments") or "{}"
                tool_call_id = tool_call.get("id") or ""

                yield {"type": "tool_start", "tool": name}
                result_content, result_data = _execute_tool_call(
                    name=name,
                    arguments_json=arguments_json,
                )
                yield {
                    "type": "tool_result",
                    "tool": name,
                    "data": result_data,
                }
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": result_content,
                    }
                )

        yield {
            "type": "error",
            "message": (
                f"Agent stopped after {max_rounds} rounds without a final answer."
            ),
        }
    except LLMError as exc:
        logger.exception("Agent stream failed")
        yield {"type": "error", "message": str(exc)}
    except Exception as exc:
        logger.exception("Unexpected agent stream failure")
        yield {
            "type": "error",
            "message": f"Unexpected agent error: {exc}",
        }


def _initial_messages(
    question: str,
    *,
    max_rounds: int,
) -> list[ChatCompletionMessageParam]:
    prompt = question.strip()
    if not prompt:
        raise LLMConfigError("question must not be empty.")
    if max_rounds < 1:
        raise LLMConfigError("max_rounds must be >= 1.")

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]


def _assistant_tool_call_message(
    message: ChatCompletionMessage,
) -> ChatCompletionMessageParam:
    """Convert an assistant message with tool_calls into an API message dict."""
    tool_calls = message.tool_calls or []
    return _assistant_tool_calls_from_dicts(
        [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
            }
            for call in tool_calls
        ],
        content=message.content,
    )


def _assistant_tool_calls_from_dicts(
    tool_calls: list[dict[str, Any]],
    *,
    content: str | None = None,
) -> ChatCompletionMessageParam:
    payload: dict[str, Any] = {
        "role": "assistant",
        "content": content,
        "tool_calls": [
            {
                "id": call.get("id") or "",
                "type": call.get("type") or "function",
                "function": {
                    "name": call["function"]["name"],
                    "arguments": call["function"].get("arguments") or "{}",
                },
            }
            for call in tool_calls
        ],
    }
    return payload  # type: ignore[return-value]


def _execute_tool_call(
    *,
    name: str,
    arguments_json: str,
) -> tuple[str, Any]:
    """Execute a tool via ``FUNCTION_MAP``.

    Returns:
        ``(content_for_model, data_for_event)`` where ``content_for_model`` is
        a JSON string for the ``role=tool`` message and ``data_for_event`` is
        a JSON-serializable value for SSE ``tool_result`` events.
    """
    if name not in FUNCTION_MAP:
        logger.warning("Unknown tool requested: %s", name)
        error = {
            "error": f"Unknown tool '{name}'. Available: {sorted(FUNCTION_MAP)}",
            "error_type": "ToolError",
        }
        return json.dumps(error, ensure_ascii=False), error

    try:
        arguments = json.loads(arguments_json or "{}")
    except json.JSONDecodeError as exc:
        logger.warning("Invalid tool arguments for %s: %s", name, exc)
        error = {
            "error": f"Invalid JSON arguments for '{name}': {exc}",
            "error_type": "ToolError",
            "arguments": arguments_json,
        }
        return json.dumps(error, ensure_ascii=False), error

    if not isinstance(arguments, dict):
        error = {
            "error": f"Tool '{name}' expects a JSON object of arguments.",
            "error_type": "ToolError",
            "arguments": arguments,
        }
        return json.dumps(error, ensure_ascii=False, default=_json_default), error

    fn = FUNCTION_MAP[name]
    logger.info("Executing tool %s args=%s", name, arguments)

    try:
        result = fn(**arguments)
    except TypeError as exc:
        logger.exception("Tool %s got invalid arguments", name)
        error = {
            "error": str(exc),
            "error_type": "ToolError",
            "arguments": arguments,
        }
        return json.dumps(error, ensure_ascii=False, default=_json_default), error
    except Exception as exc:
        logger.exception("Tool %s failed", name)
        error = {
            "error": str(exc),
            "error_type": type(exc).__name__,
            "arguments": arguments,
        }
        return json.dumps(error, ensure_ascii=False, default=_json_default), error

    # Normalize to JSON-friendly data for both the model and SSE clients.
    content = _serialize_tool_result(result)
    data = json.loads(content)
    return content, data


def _run_tool_call(tool_call: ChatCompletionMessageToolCall) -> str:
    """Backward-compatible helper used by older call sites / tests."""
    content, _ = _execute_tool_call(
        name=tool_call.function.name,
        arguments_json=tool_call.function.arguments or "{}",
    )
    return content


def _serialize_tool_result(result: Any) -> str:
    """Serialize a Python tool result to JSON for the model."""
    return json.dumps(result, ensure_ascii=False, default=_json_default)


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return str(value)
