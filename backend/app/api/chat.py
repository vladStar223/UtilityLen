"""Route for streaming the AI-lawyer chat via Server-Sent Events."""

from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent.runner import generate_stream

router = APIRouter()


class ChatRequest(BaseModel):
    comparison_id: str
    message: str
    history: Optional[List[dict]] = None


@router.post("/chat/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        generate_stream(request.comparison_id, request.message, request.history),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
