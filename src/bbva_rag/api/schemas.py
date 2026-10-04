"""Modelos de solicitud y respuesta de la API
(validados por pydantic)"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    conversation_id: str | None = None


class Source(BaseModel):
    title: str
    url: str


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: int
    answer: str
    sources: list[Source]
    outcome: str | None
    latency_seconds: float


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    sources: list[Source]
    feedback: int | None
    created_at: datetime


class FeedbackRequest(BaseModel):
    value: Literal[1, -1]
