import pytest
from sqlalchemy.pool import StaticPool

from bbva_rag.memory.database import create_session_factory
from bbva_rag.memory.repository import ConversationRepository
from bbva_rag.services.chat import ERROR_MESSAGE, ChatService


def make_repository() -> ConversationRepository:
    # StaticPool: every connection shares the same in-memory SQLite database
    factory = create_session_factory(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    return ConversationRepository(factory)


def test_recent_messages_are_the_last_n_in_chronological_order():
    repo = make_repository()
    for i in range(3):
        repo.add_exchange("c1", f"pregunta {i}", f"respuesta {i}", {})
    messages = repo.recent_messages("c1", limit=3)
    assert [m["content"] for m in messages] == ["respuesta 1", "pregunta 2", "respuesta 2"]


def test_zero_limit_returns_no_history():
    repo = make_repository()
    repo.add_exchange("c1", "pregunta", "respuesta", {})
    assert repo.recent_messages("c1", limit=0) == []


def test_conversations_are_isolated():
    repo = make_repository()
    repo.add_exchange("c1", "pregunta de c1", "respuesta", {})
    assert repo.recent_messages("c2", limit=10) == []


def test_feedback_only_for_assistant_messages():
    repo = make_repository()
    answer_id = repo.add_exchange("c1", "pregunta", "respuesta", {})
    repo.set_feedback(answer_id, 1)
    with pytest.raises(ValueError):
        repo.set_feedback(answer_id - 1, 1)  # the user's message
    with pytest.raises(ValueError):
        repo.set_feedback(answer_id, 5)


class FakeGraph:
    def __init__(self, fail: bool = False):
        self.fail, self.received_history = fail, None

    def invoke(self, state):
        if self.fail:
            raise RuntimeError("OpenAI is down")
        self.received_history = state["history"]
        return {
            "answer": f"respuesta a {state['question']}",
            "outcome": "answered",
            "intent": "bank_query",
        }


def test_service_sends_previous_messages_as_history():
    graph = FakeGraph()
    service = ChatService(graph, make_repository(), history_max_messages=6)
    service.ask("c1", "¿Qué es un CDT?")
    service.ask("c1", "¿y qué plazos tiene?")
    assert graph.received_history == [
        {"role": "user", "content": "¿Qué es un CDT?"},
        {"role": "assistant", "content": "respuesta a ¿Qué es un CDT?"},
    ]


def test_service_saves_errors_and_returns_a_friendly_message():
    repo = make_repository()
    reply = ChatService(FakeGraph(fail=True), repo, 6).ask("c1", "¿Qué es un CDT?")
    assert reply.answer == ERROR_MESSAGE
    assert reply.outcome == "error"
    assert repo.recent_messages("c1", 2)[1]["content"] == ERROR_MESSAGE
