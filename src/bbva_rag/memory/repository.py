"""Repositorio: el único lugar que lee o escribe el historial de conversaciones."""

from sqlalchemy import select, text
from sqlalchemy.orm import Session, sessionmaker

from bbva_rag.memory.models import Conversation, Message, utcnow


class ConversationRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    def add_exchange(self, conversation_id: str, question: str, answer: str, metadata: dict) -> int:
        """Guarda la pregunta y la respuesta en una sola transacción;
        devuelve el ID de la respuesta"""
        with self._session_factory.begin() as session:
            conversation = session.get(Conversation, conversation_id)
            if conversation is None:
                session.add(Conversation(id=conversation_id))
            else:
                conversation.updated_at = utcnow()
            session.add(Message(conversation_id=conversation_id, role="user", content=question))
            reply = Message(
                conversation_id=conversation_id, role="assistant", content=answer, **metadata
            )
            session.add(reply)
            session.flush()
            return reply.id

    def recent_messages(self, conversation_id: str, limit: int) -> list[dict]:
        """Últimos mensajes de una conversación, del más antiguo al más reciente"""
        if limit <= 0:
            return []
        with self._session_factory() as session:
            rows = session.scalars(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.id.desc())
                .limit(limit)
            ).all()
        return [{"role": m.role, "content": m.content} for m in reversed(rows)]

    def set_feedback(self, message_id: int, value: int) -> None:
        if value not in (1, -1):
            raise ValueError("Feedback must be 1 (useful) or -1 (not useful)")
        with self._session_factory.begin() as session:
            message = session.get(Message, message_id)
            if message is None or message.role != "assistant":
                raise ValueError(f"No assistant message with id {message_id}")
            message.feedback = value

    def conversation_messages(self, conversation_id: str) -> list[dict]:
        """Todos los mensajes de una conversación, del más antiguo al
        más antiguo (para la interfaz de usuario)"""
        with self._session_factory() as session:
            rows = session.scalars(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.id)
            ).all()
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "sources": m.sources or [],
                "feedback": m.feedback,
                "created_at": m.created_at,
            }
            for m in rows
        ]

    def ping(self) -> bool:
        """Verdadero si la base de datos responde"""
        try:
            with self._session_factory() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
