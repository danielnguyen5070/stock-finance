"""Chat HTTP endpoints for Market AI (blocking + SSE streaming)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.ai.agent import AgentError, run_agent, run_agent_stream
from app.exceptions import LLMConfigError, LLMError, LLMRequestError

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    """Incoming chat payload from the client."""

    message: str = Field(
        ...,
        min_length=1,
        description="User question about stocks (any language).",
        examples=["Giá cổ phiếu Nvidia hiện tại là bao nhiêu?"],
    )


class ChatResponse(BaseModel):
    """Final assistant reply after tool calling completes."""

    message: str = Field(
        ...,
        description="Natural-language answer from Market AI.",
        examples=[
            "Nvidia (NVDA) hiện đang giao dịch ở mức 227,38 USD (giá đóng cửa)."
        ],
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with Market AI",
    description=(
        "Sends the user message through the DeepSeek tool-calling agent "
        "(`get_symbol`, `get_stock_price`) and returns the final text reply. "
        "Non-streaming; use `POST /chat/stream` for SSE."
    ),
    response_description="Final assistant message after any tool calls finish.",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Empty / invalid message or missing LLM configuration.",
        },
        status.HTTP_502_BAD_GATEWAY: {
            "description": "Upstream LLM or agent failure.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Unexpected server error.",
        },
    },
)
def chat(request: ChatRequest) -> ChatResponse:
    """Run the stock agent for one user message and return the final answer."""
    try:
        answer = run_agent(request.message)
    except LLMConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except AgentError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except LLMRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except LLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while processing chat request.",
        ) from exc

    return ChatResponse(message=answer)


@router.post(
    "/chat/stream",
    summary="Chat with Market AI (SSE)",
    description=(
        "Server-Sent Events stream of tool and token events while the agent "
        "runs. Each event is `data: <json>` followed by a blank line.\n\n"
        "Event types: `tool_start`, `tool_result`, `token`, `done`, `error`."
    ),
    response_class=StreamingResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "SSE stream (`text/event-stream`).",
            "content": {
                "text/event-stream": {
                    "example": (
                        'data: {"type":"tool_start","tool":"get_symbol"}\n\n'
                        'data: {"type":"tool_result","tool":"get_symbol","data":"NVDA"}\n\n'
                        'data: {"type":"token","content":"Nvidia"}\n\n'
                        'data: {"type":"done"}\n\n'
                    )
                }
            },
        },
    },
)
def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Stream agent progress and the final answer via SSE."""

    def event_source() -> Iterator[str]:
        try:
            for event in run_agent_stream(request.message):
                yield _format_sse(event)
        except Exception as exc:
            yield _format_sse(
                {
                    "type": "error",
                    "message": f"Unexpected streaming error: {exc}",
                }
            )

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _format_sse(event: dict[str, Any]) -> str:
    """Encode one SSE ``data:`` frame."""
    payload = json.dumps(event, ensure_ascii=False, default=_json_default)
    return f"data: {payload}\n\n"


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return str(value)
