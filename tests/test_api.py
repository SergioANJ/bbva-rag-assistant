from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool

from bbva_rag.api.main import AppServices, create_app
from bbva_rag.memory.database import create_session_factory
from bbva_rag.memory.repository import ConversationRepository
from bbva_rag.services.chat import ChatService


class FakeGraph:
    def invoke(self, state):
        return {
            "answer": "Un CDT es un depósito a término [1].",
            "sources": [{"title": "Glosario", "url": "https://x.com/glosario"}],
            "outcome": "answered",
        }


def make_client() -> TestClient:
    factory = create_session_factory(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    repository = ConversationRepository(factory)
    services = AppServices(ChatService(FakeGraph(), repository, 6), repository, store=None)
    return TestClient(create_app(services))


def test_chat_creates_a_conversation_and_stores_it():
    with make_client() as client:
        reply = client.post("/chat", json={"question": "¿Qué es un CDT?"}).json()
        assert reply["sources"][0]["title"] == "Glosario"
        messages = client.get(f"/conversations/{reply['conversation_id']}/messages").json()
        assert [m["role"] for m in messages] == ["user", "assistant"]


def test_feedback_is_saved():
    with make_client() as client:
        reply = client.post("/chat", json={"question": "¿Qué es un CDT?"}).json()
        response = client.post(f"/messages/{reply['message_id']}/feedback", json={"value": 1})
        assert response.status_code == 204


def test_invalid_requests_are_rejected():
    with make_client() as client:
        assert client.post("/chat", json={"question": ""}).status_code == 422
        assert client.post("/messages/1/feedback", json={"value": 5}).status_code == 422
        assert client.post("/messages/999/feedback", json={"value": 1}).status_code == 404


def test_health_reports_database_status():
    with make_client() as client:
        assert client.get("/health").json() == {"postgres": "ok"}
