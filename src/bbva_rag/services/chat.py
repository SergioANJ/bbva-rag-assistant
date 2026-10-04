"""Servicio de chat (Facade): una llamada para consultar con memoria;
oculta el gráfico y la base de datos"""

import time
from dataclasses import dataclass

from loguru import logger

from bbva_rag.memory.repository import ConversationRepository

ERROR_MESSAGE = "Ocurrió un error al procesar tu pregunta. Por favor, intenta de nuevo."


@dataclass(frozen=True)
class ChatReply:
    conversation_id: str
    message_id: int
    answer: str
    sources: list[dict]
    outcome: str
    latency_seconds: float


class ChatService:
    def __init__(self, graph, repository: ConversationRepository, history_max_messages: int):
        self._graph = graph
        self._repository = repository
        self._history_max_messages = history_max_messages

    def ask(self, conversation_id: str, question: str) -> ChatReply:
        history = self._repository.recent_messages(conversation_id, self._history_max_messages)

        started = time.perf_counter()
        try:
            state = self._graph.invoke({"question": question, "history": history})
        except Exception:
            logger.exception(f"Graph failed for conversation {conversation_id}")
            state = {"answer": ERROR_MESSAGE, "outcome": "error"}
        latency = time.perf_counter() - started

        context = state.get("context") or []
        metadata = {
            "intent": state.get("intent"),
            "outcome": state.get("outcome"),
            "standalone_question": state.get("standalone_question"),
            "top_score": context[0].score if context else None,
            "attempts": state.get("attempts", 0),
            "sources": state.get("sources", []),
            "timings": state.get("timings", {}),
            "latency_seconds": latency,
        }
        message_id = self._repository.add_exchange(
            conversation_id, question, state["answer"], metadata
        )
        return ChatReply(
            conversation_id=conversation_id,
            message_id=message_id,
            answer=state["answer"],
            sources=metadata["sources"],
            outcome=metadata["outcome"],
            latency_seconds=latency,
        )
