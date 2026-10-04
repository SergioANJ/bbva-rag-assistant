"""API HTTP del asistente. Se ejecuta con:
uvicorn bbva_rag.api.main:app"""

import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from bbva_rag.api.schemas import ChatRequest, ChatResponse, FeedbackRequest, MessageOut
from bbva_rag.config import Settings, get_settings, setup_logging
from bbva_rag.graph.builder import create_rag_graph
from bbva_rag.memory.database import create_session_factory
from bbva_rag.memory.repository import ConversationRepository
from bbva_rag.services.chat import ChatService
from bbva_rag.vectorstore.qdrant_store import QdrantStore


@dataclass
class AppServices:
    chat: ChatService
    repository: ConversationRepository
    store: QdrantStore | None


def build_services(settings: Settings) -> AppServices:
    """Se carga los modelos y abre las conexiones una sola vez, cuando se inicie la API."""
    repository = ConversationRepository(create_session_factory(settings.database_url))
    chat = ChatService(create_rag_graph(settings), repository, settings.history_max_messages)
    store = QdrantStore(settings.qdrant_url, settings.qdrant_collection)
    return AppServices(chat, repository, store)


def create_app(services: AppServices | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        setup_logging()
        app.state.services = services or build_services(get_settings())
        yield

    app = FastAPI(
        title="Bancolombia RAG Assistant",
        description="Asistente conversacional sobre el contenido público de bancolombia.com",
        version="1.0.0",
        lifespan=lifespan,
    )

    def get_services(request: Request) -> AppServices:
        return request.app.state.services

    @app.get("/health")
    def health(request: Request):
        services = get_services(request)
        status = {"postgres": "ok" if services.repository.ping() else "down"}
        if services.store is not None:
            try:
                services.store.count()
                status["qdrant"] = "ok"
            except Exception:
                status["qdrant"] = "down"
        healthy = all(value == "ok" for value in status.values())
        return JSONResponse(status_code=200 if healthy else 503, content=status)

    @app.post("/chat", response_model=ChatResponse)
    def chat(body: ChatRequest, request: Request):
        conversation_id = body.conversation_id or str(uuid.uuid4())
        reply = get_services(request).chat.ask(conversation_id, body.question)
        return ChatResponse(**reply.__dict__)

    @app.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
    def conversation_messages(conversation_id: str, request: Request):
        return get_services(request).repository.conversation_messages(conversation_id)

    @app.post("/messages/{message_id}/feedback", status_code=204)
    def feedback(message_id: int, body: FeedbackRequest, request: Request):
        try:
            get_services(request).repository.set_feedback(message_id, body.value)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return Response(status_code=204)

    return app


app = create_app()
