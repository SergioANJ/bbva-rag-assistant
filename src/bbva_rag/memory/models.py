"""Tablas de base de datos: conversaciones y sus mensajes"""

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", order_by="Message.id"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )

    # Assistant-only metadata, used by the analytics phase
    intent: Mapped[str | None] = mapped_column(String(32))
    outcome: Mapped[str | None] = mapped_column(String(32))
    standalone_question: Mapped[str | None] = mapped_column(Text)
    top_score: Mapped[float | None] = mapped_column(Float)
    attempts: Mapped[int | None] = mapped_column(Integer)
    sources: Mapped[list | None] = mapped_column(JSON)
    timings: Mapped[dict | None] = mapped_column(JSON)
    latency_seconds: Mapped[float | None] = mapped_column(Float)
    feedback: Mapped[int | None] = mapped_column(SmallInteger)  # 1 = useful, -1 = not useful

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
