"""Tool-calling agent loop for the stock chatbot.

Orchestrates DeepSeek completions with OpenAI-style tools from
``app.ai.tools``. New tools only need registration in ``FUNCTION_MAP`` /
``tools`` — this module stays unchanged.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Any

from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCall,
)

from app.ai.openai_client import get_completion
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


class AgentError(LLMError):
    """Raised when the agent cannot produce a final answer."""


def run_agent(
    question: str,
    *,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
) -> str:
    """Run a DeepSeek tool-calling loop for a single user question.

    Flow:
        1. Send system + user messages with tool definitions.
        2. If the model returns ``tool_calls``, execute them via
           ``FUNCTION_MAP``, append results, and call the model again.
        3. Repeat until a normal text answer (or ``max_rounds`` is hit).

    Args:
        question: End-user question (any language).
        max_rounds: Maximum model turns (tool rounds + final answer).

    Returns:
        Final assistant text content.

    Raises:
        LLMConfigError: Empty question or missing API configuration.
        AgentError: No final text after the allowed rounds.
        LLMRequestError: Upstream DeepSeek failures (from ``get_completion``).
    """
    prompt = question.strip()
    if not prompt:
        raise LLMConfigError("question must not be empty.")
    if max_rounds < 1:
        raise LLMConfigError("max_rounds must be >= 1.")

    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

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
            result_content = _run_tool_call(tool_call)
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


def _assistant_tool_call_message(
    message: ChatCompletionMessage,
) -> ChatCompletionMessageParam:
    """Convert an assistant message with tool_calls into an API message dict."""
    tool_calls = message.tool_calls or []
    payload: dict[str, Any] = {
        "role": "assistant",
        "content": message.content,
        "tool_calls": [
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
    }
    return payload  # type: ignore[return-value]


def _run_tool_call(tool_call: ChatCompletionMessageToolCall) -> str:
    """Execute one tool call via ``FUNCTION_MAP`` and return JSON content."""
    name = tool_call.function.name
    raw_args = tool_call.function.arguments or "{}"

    if name not in FUNCTION_MAP:
        logger.warning("Unknown tool requested: %s", name)
        return _error_payload(
            f"Unknown tool '{name}'. Available: {sorted(FUNCTION_MAP)}"
        )

    try:
        arguments = json.loads(raw_args)
    except json.JSONDecodeError as exc:
        logger.warning("Invalid tool arguments for %s: %s", name, exc)
        return _error_payload(
            f"Invalid JSON arguments for '{name}': {exc}",
            arguments=raw_args,
        )

    if not isinstance(arguments, dict):
        return _error_payload(
            f"Tool '{name}' expects a JSON object of arguments.",
            arguments=arguments,
        )

    fn = FUNCTION_MAP[name]
    logger.info("Executing tool %s args=%s", name, arguments)

    try:
        result = fn(**arguments)
    except TypeError as exc:
        # Wrong / missing kwargs from the model.
        logger.exception("Tool %s got invalid arguments", name)
        return _error_payload(str(exc), arguments=arguments)
    except Exception as exc:
        logger.exception("Tool %s failed", name)
        return _error_payload(
            str(exc),
            error_type=type(exc).__name__,
            arguments=arguments,
        )

    return _serialize_tool_result(result)


def _serialize_tool_result(result: Any) -> str:
    """Serialize a Python tool result to JSON for the model."""
    return json.dumps(result, ensure_ascii=False, default=_json_default)


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return str(value)


def _error_payload(
    message: str,
    *,
    error_type: str = "ToolError",
    arguments: Any | None = None,
) -> str:
    payload: dict[str, Any] = {
        "error": message,
        "error_type": error_type,
    }
    if arguments is not None:
        payload["arguments"] = arguments
    return json.dumps(payload, ensure_ascii=False, default=_json_default)
