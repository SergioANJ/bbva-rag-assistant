import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from bbva_rag.config import Settings
from bbva_rag.llm.context import cited_sources, format_context, format_history
from bbva_rag.llm.factory import create_chat_model
from bbva_rag.llm.prompts import answer_messages
from bbva_rag.llm.schemas import QueryAnalysis
from bbva_rag.retrieval.base import RetrievedChunk


def make_chunk(name: str) -> RetrievedChunk:
    return RetrievedChunk(
        f"id-{name}", f"https://x.com/{name}", name.upper(), "personas", f"texto {name}", 1.0
    )


CHUNKS = [make_chunk("cdt"), make_chunk("tarjeta"), make_chunk("cdt")]


def test_context_is_numbered_from_one():
    context = format_context(CHUNKS[:2])
    assert context.startswith("[1] CDT (https://x.com/cdt)")
    assert "[2] TARJETA (https://x.com/tarjeta)" in context


def test_cited_sources_are_unique_and_ignore_invalid_numbers():
    answer = "El CDT es seguro [1][3]. La tarjeta tiene cuota [2]. Dato raro [9]."
    sources = cited_sources(answer, CHUNKS)
    assert sources == [
        {"title": "CDT", "url": "https://x.com/cdt"},
        {"title": "TARJETA", "url": "https://x.com/tarjeta"},
    ]


def test_answer_without_citations_has_no_sources():
    assert cited_sources("No encontré esa información.", CHUNKS) == []


def test_history_formatting():
    history = [
        {"role": "user", "content": "¿Qué es un CDT?"},
        {"role": "assistant", "content": "Es..."},
    ]
    assert format_history(history) == "Usuario: ¿Qué es un CDT?\nAsistente: Es..."
    assert format_history([]) == "(sin mensajes previos)"


def test_answer_prompt_separates_rules_from_data():
    messages = answer_messages("¿Qué es un CDT?", CHUNKS[:1])
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], HumanMessage)
    assert "[1] CDT" in messages[1].content
    assert "Pregunta: ¿Qué es un CDT?" in messages[1].content


def test_query_analysis_rejects_unknown_intent():
    with pytest.raises(ValueError):
        QueryAnalysis(intent="weather", standalone_question="¿Lloverá?")


def test_factory_requires_api_key():
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        create_chat_model(Settings(_env_file=None, openai_api_key=None))
