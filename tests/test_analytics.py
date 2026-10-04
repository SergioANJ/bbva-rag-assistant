from datetime import UTC, datetime

from bbva_rag.analytics.metrics import build_exchanges, percentile, summarize
from bbva_rag.analytics.topics import cluster_questions, top_keywords

NOW = datetime(2026, 10, 4, tzinfo=UTC)


def message(id, conversation, role, content, **meta):
    base = {
        "id": id,
        "conversation_id": conversation,
        "role": role,
        "content": content,
        "created_at": NOW,
        "intent": None,
        "outcome": None,
        "standalone_question": None,
        "top_score": None,
        "attempts": None,
        "sources": [],
        "timings": {},
        "latency_seconds": None,
        "feedback": None,
    }
    return base | meta


MESSAGES = [
    message(1, "c1", "user", "¿Qué es un CDT?"),
    message(
        2,
        "c1",
        "assistant",
        "Un CDT es... [1]",
        intent="bank_query",
        outcome="answered",
        attempts=1,
        latency_seconds=9.0,
        feedback=1,
        sources=[{"title": "Glosario", "url": "https://www.bancolombia.com/acerca-de/glosario"}],
        timings={"analyze": 1.0, "retrieve_1": 0.5, "rerank_1": 5.0, "generate": 2.0},
    ),
    message(3, "c2", "user", "¿Qué es el fleteo?"),
    message(
        4,
        "c2",
        "assistant",
        "No encontré...",
        intent="bank_query",
        outcome="no_answer",
        attempts=2,
        latency_seconds=15.0,
        feedback=-1,
        timings={
            "analyze": 1.0,
            "retrieve_1": 0.5,
            "rerank_1": 5.0,
            "rewrite": 1.0,
            "retrieve_2": 0.5,
            "rerank_2": 5.0,
        },
    ),
    message(5, "c2", "user", "gracias"),
    message(
        6,
        "c2",
        "assistant",
        "¡Con gusto!",
        intent="greeting",
        outcome="direct_reply",
        attempts=0,
        latency_seconds=1.0,
    ),
]


def test_exchanges_pair_each_answer_with_its_question():
    exchanges = build_exchanges(MESSAGES)
    assert [e["question"] for e in exchanges] == [
        "¿Qué es un CDT?",
        "¿Qué es el fleteo?",
        "gracias",
    ]


def test_answer_rate_ignores_greetings():
    summary = summarize(build_exchanges(MESSAGES), minutes_saved_per_answer=5)
    assert summary["answer_rate"] == 0.5  # 1 answered of 2 bank questions
    assert summary["rewrite_rate"] == 0.5


def test_node_times_merge_repeated_attempts():
    summary = summarize(build_exchanges(MESSAGES), 5)
    assert summary["avg_node_seconds"]["rerank"] == 7.5  # (5 + 10) / 2


def test_unanswered_questions_and_impact():
    summary = summarize(build_exchanges(MESSAGES), minutes_saved_per_answer=6)
    assert [q["question"] for q in summary["unanswered_questions"]] == ["¿Qué es el fleteo?"]
    assert summary["impact"]["estimated_hours_saved"] == 0.1  # 1 answer × 6 min
    assert summary["top_sections"] == {"acerca-de": 1}
    assert summary["feedback"]["positive_rate"] == 0.5


def test_percentile():
    assert percentile([1, 2, 3, 4, 100], 50) == 3
    assert percentile([], 95) is None


def test_keywords_skip_stopwords():
    assert top_keywords(["¿Cómo abro un CDT?", "¿Cuánto rinde un CDT?"])[0] == "cdt"


class FakeEmbedder:
    dimensions = 2

    def embed_documents(self, texts):
        # Questions mentioning "cdt" point one way, the rest the other way
        return [[1.0, 0.0] if "cdt" in t.lower() else [0.0, 1.0] for t in texts]


def test_questions_are_grouped_by_topic():
    questions = [
        "¿Qué es un CDT?",
        "Plazos del CDT",
        "Tasa del CDT",
        "Cuota de manejo tarjeta",
        "Bloquear tarjeta",
        "Avance con tarjeta",
    ]
    topics = cluster_questions(questions, FakeEmbedder(), max_topics=4)
    assert sorted(t["size"] for t in topics) == [3, 3]
