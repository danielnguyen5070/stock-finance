"""Chat HTTP endpoint for Market AI (non-streaming)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.ai.agent import AgentError, run_agent
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
        "Non-streaming; a streaming variant will follow."
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
