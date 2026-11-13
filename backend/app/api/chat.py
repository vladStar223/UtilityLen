"""Route for streaming the AI-lawyer chat via Server-Sent Events."""

from typing import List, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agent.runner import generate_stream
from app.db import crud
from app.db.database import get_db

router = APIRouter()


class ChatRequest(BaseModel):
    comparison_id: str = Field(
        description="ID ранее выполненного сравнения, по контексту которого ведётся диалог",
        examples=["cmp-20240215-abc123"],
    )
    message: str = Field(
        description="Сообщение пользователя для AI-юриста",
        examples=["Почему выросла сумма за отопление?", "Можно ли оспорить этот тариф?"],
    )
    history: Optional[List[dict]] = Field(
        default=None,
        description="История диалога (опционально, для поддержания контекста)",
        examples=[[{"role": "user", "content": "Привет"}, {"role": "assistant", "content": "Здравствуйте!"}]],
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
    openapi_examples={
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
    },
)
def chat_stream(request: ChatRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    try:
        crud.save_chat_message(
            db,
            comparison_id=request.comparison_id,
            role="user",
            content=request.message,
        )
    except Exception:
        db.rollback()

    return StreamingResponse(
        generate_stream(request.comparison_id, request.message, request.history),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
