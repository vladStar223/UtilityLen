"""Route for streaming the AI-lawyer chat via Server-Sent Events."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agent import tools
from app.agent.runner import generate_stream
from app.core.auth import get_current_user_optional
from app.core.logging import logger
from app.core.rate_limit import limiter
from app.core.security import verify_api_key
from app.db import crud
from app.db.database import get_db
from app.db.models import User

router = APIRouter(dependencies=[Depends(verify_api_key)])


class ChatRequest(BaseModel):
    comparison_id: str = Field(
        description="ID ранее выполненного сравнения, по контексту которого ведётся диалог",
        examples=["cmp-20240215-abc123"],
    )
    message: str = Field(
        description="Сообщение пользователя для AI-юриста",
        examples=["Почему выросла сумма за отопление?", "Можно ли оспорить этот тариф?"],
        max_length=2000,
    )
    history: Optional[List[dict]] = Field(
        default=None,
        description="История диалога (опционально, для поддержания контекста)",
        examples=[[{"role": "user", "content": "Привет"}, {"role": "assistant", "content": "Здравствуйте!"}]],
        max_length=50,
    )


@router.post(
    "/chat/stream",
    summary="SSE-стриминг диалога с AI-юристом",
    description="""
Запускает стриминговый диалог с AI-юристом по контексту ранее выполненного сравнения.

Ответ передаётся в формате Server-Sent Events (SSE). Типы событий:
- `token` — фрагмент текста ответа;
- `tool_call` — уведомление о вызове инструмента (например, поиск по нормативам);
- `done` — завершение стрима.

Фронтенд должен подписаться на `EventSource` и обрабатывать каждое событие.
""",
    responses={
        200: {
            "description": "SSE-стрим успешно открыт",
            "content": {
                "text/event-stream": {
                    "example": 'event: token\ndata: {"text": "Сумма"}\n\nevent: token\ndata: {"text": " выросла"}\n\nevent: done\ndata: {}\n\n'
                }
            },
        },
        400: {
            "description": "Некорректный запрос (например, пустое сообщение)",
            "content": {
                "application/json": {
                    "example": {"detail": "Message must not be empty"}
                }
            },
        },
        404: {
            "description": "comparison_id не найден в хранилище",
            "content": {
                "application/json": {
                    "example": {"detail": "Comparison 'unknown-id' not found"}
                }
            },
        },
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "basic": {
                            "summary": "Простой вопрос по сравнению",
                            "value": {
                                "comparison_id": "cmp-20240215-abc123",
                                "message": "Почему выросла сумма за отопление?",
                            },
                        },
                        "with_history": {
                            "summary": "Вопрос с историей диалога",
                            "value": {
                                "comparison_id": "cmp-20240215-abc123",
                                "message": "А можно оспорить?",
                                "history": [
                                    {"role": "user", "content": "Почему выросла сумма за отопление?"},
                                    {"role": "assistant", "content": "Тариф вырос на 8.3%..."},
                                ],
                            },
                        },
                    }
                }
            }
        }
    },
)
@limiter.limit("20/minute")
def chat_stream(
    request: Request,
    payload: ChatRequest,
    api_key_owner: str = Depends(verify_api_key),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    owner_id = user.user_id if user is not None else api_key_owner
    try:
        record = tools.get_report(payload.comparison_id, owner_id)
    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail=f"Access to comparison '{payload.comparison_id}' is forbidden",
        )
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Comparison '{payload.comparison_id}' not found",
        )

    try:
        crud.save_chat_message(
            db,
            comparison_id=payload.comparison_id,
            role="user",
            content=payload.message,
        )
    except Exception as exc:
        db.rollback()
        logger.exception(f"Database error in operation: {exc.__class__.__name__}")

    return StreamingResponse(
        generate_stream(payload.comparison_id, payload.message, payload.history, owner_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
