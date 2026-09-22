"""OpenAI / DeepSeek tool definitions derived from Python callables.

Schemas and descriptions are generated from type hints and docstrings so
future tools (e.g. ``get_crypto_price``) only need a well-typed function.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any, get_type_hints

from openai.types.chat import ChatCompletionToolParam
from pydantic import BaseModel, TypeAdapter, create_model

from app.services.stock import get_stock_price, get_symbol

# Internal kwargs that must not be exposed to the LLM as tool parameters.
_INTERNAL_PARAM_NAMES = frozenset({"settings"})


def _parameter_fields(fn: Callable[..., Any]) -> dict[str, Any]:
    """Build pydantic ``create_model`` field map from a function signature."""
    hints = get_type_hints(fn)
    fields: dict[str, Any] = {}

    for name, param in inspect.signature(fn).parameters.items():
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        if name in _INTERNAL_PARAM_NAMES:
            continue

        annotation = hints.get(name, Any)
        if param.default is inspect.Parameter.empty:
            fields[name] = (annotation, ...)
        else:
            fields[name] = (annotation, param.default)

    if not fields:
        raise ValueError(f"Function '{fn.__name__}' has no public parameters.")

    return fields


def make_openai_tool(fn: Callable[..., Any]) -> ChatCompletionToolParam:
    """Build an OpenAI-compatible tool dict from a Python function.

    - ``description`` comes from ``inspect.getdoc(fn)``
    - ``parameters`` comes from ``TypeAdapter(...).json_schema()`` on a
      pydantic model synthesized from the function's public parameters
    """
    description = inspect.getdoc(fn)
    if not description:
        raise ValueError(f"Function '{fn.__name__}' is missing a docstring.")

    model: type[BaseModel] = create_model(
        f"{fn.__name__}Parameters",
        **_parameter_fields(fn),
    )
    parameters = TypeAdapter(model).json_schema()

    # OpenAI expects a plain object schema; drop pydantic model title noise.
    parameters.pop("title", None)

    return {
        "type": "function",
        "function": {
            "name": fn.__name__,
            "description": description,
            "parameters": parameters,
        },
    }


FUNCTION_MAP: dict[str, Callable[..., Any]] = {
    "get_symbol": get_symbol,
    "get_stock_price": get_stock_price,
}

tools: list[ChatCompletionToolParam] = [
    make_openai_tool(get_symbol),
    make_openai_tool(get_stock_price),
]
