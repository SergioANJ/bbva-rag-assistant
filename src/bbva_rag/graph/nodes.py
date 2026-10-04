"""Nodes and routing functions of the RAG graph."""

import time

from langchain_core.language_models import BaseChatModel

from bbva_rag.config import Settings
from bbva_rag.graph.state import RAGState
from bbva_rag.llm.context import cited_sources
from bbva_rag.llm.prompts import analyze_messages, answer_messages, rewrite_messages
from bbva_rag.llm.schemas import QueryAnalysis
from bbva_rag.retrieval.base import Retriever
from bbva_rag.retrieval.reranker import CrossEncoderReranker

NO_ANSWER_MESSAGE = (
    "No encontré información sobre eso en el contenido publicado en el sitio de Bancolombia. "
    "Puedes intentar con otras palabras o consultar directamente los canales oficiales del banco."
)


class RAGNodes:
    """Cada método público es un nodo del grafo: recibe el estado y 
       devuelve solo lo que cambia"""

    def __init__(
        self,
        llm: BaseChatModel,
        retriever: Retriever,
        reranker: CrossEncoderReranker,
        settings: Settings,
    ):
        self._llm = llm
        self._retriever = retriever
        self._reranker = reranker
        self._settings = settings

    # ---------- Nodos ----------

    def analyze_query(self, state: RAGState) -> dict:
        started = time.perf_counter()
        analysis: QueryAnalysis = self._llm.with_structured_output(QueryAnalysis).invoke(
            analyze_messages(state["question"], state.get("history", []))
        )
        return {
            "intent": analysis.intent,
            "standalone_question": analysis.standalone_question,
            "answer": analysis.reply or "",
            "attempts": 0,
            "timings": {"analyze": time.perf_counter() - started},
        }

    def retrieve(self, state: RAGState) -> dict:
        started = time.perf_counter()
        attempt = state["attempts"] + 1
        candidates = self._retriever.retrieve(
            state["standalone_question"], self._settings.retrieval_top_k
        )
        return {
            "candidates": candidates,
            "attempts": attempt,
            "timings": {f"retrieve_{attempt}": time.perf_counter() - started},
        }

    def rerank(self, state: RAGState) -> dict:
        started = time.perf_counter()
        context = self._reranker.rerank(
            state["standalone_question"], state["candidates"], self._settings.rerank_top_n
        )
        return {
            "context": context,
            "timings": {f"rerank_{state['attempts']}": time.perf_counter() - started},
        }

    def rewrite_query(self, state: RAGState) -> dict:
        started = time.perf_counter()
        rewritten = self._llm.invoke(rewrite_messages(state["standalone_question"])).content
        return {
            "standalone_question": rewritten.strip(),
            "timings": {"rewrite": time.perf_counter() - started},
        }

    def generate(self, state: RAGState) -> dict:
        started = time.perf_counter()
        answer = self._llm.invoke(answer_messages(state["question"], state["context"])).content
        return {
            "answer": answer,
            "sources": cited_sources(answer, state["context"]),
            "timings": {"generate": time.perf_counter() - started},
        }

    def no_answer(self, state: RAGState) -> dict:
        return {"answer": NO_ANSWER_MESSAGE, "sources": []}

    def direct_reply(self, state: RAGState) -> dict:
        # La respuesta ya fue escrita por analyze_query
        return {"sources": []}

    # ---------- Enrutamiento (es la arista condicional) ----------

    def route_by_intent(self, state: RAGState) -> str:
        return "retrieve" if state["intent"] == "bank_query" else "direct_reply"

    def route_after_rerank(self, state: RAGState) -> str:
        context = state.get("context", [])
        if context and context[0].score >= self._settings.relevance_threshold:
            return "generate"
        if state["attempts"] <= self._settings.max_query_rewrites:
            return "rewrite_query"
        return "no_answer"