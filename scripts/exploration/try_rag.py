"""Exploration: the full RAG flow (no graph yet) for one question."""

import sys
import time

from bbva_rag.llm.prompts import analyze_messages, answer_messages

from bbva_rag.config import get_settings
from bbva_rag.embeddings.factory import create_embedder
from bbva_rag.embeddings.sparse_bm25 import BM25Encoder
from bbva_rag.llm.context import cited_sources
from bbva_rag.llm.factory import create_chat_model
from bbva_rag.llm.schemas import QueryAnalysis
from bbva_rag.retrieval.factory import create_retriever
from bbva_rag.retrieval.reranker import CrossEncoderReranker
from bbva_rag.vectorstore.qdrant_store import QdrantStore


def main(question: str) -> None:
    settings = get_settings()
    cache_dir = str(settings.models_cache_dir)
    store = QdrantStore(settings.qdrant_url, settings.qdrant_collection)
    bm25 = BM25Encoder(settings.sparse_model, settings.sparse_language, cache_dir)
    retriever = create_retriever(
        settings.retrieval_strategy, store, create_embedder(settings), bm25
    )
    reranker = CrossEncoderReranker(settings.reranker_model, cache_dir)
    llm = create_chat_model(settings)
    timings = {}

    # 1. Analyze the question
    started = time.perf_counter()
    analysis: QueryAnalysis = llm.with_structured_output(QueryAnalysis).invoke(
        analyze_messages(question, history=[])
    )
    timings["analyze"] = time.perf_counter() - started
    print(f"Intención: {analysis.intent}")
    print(f"Pregunta reescrita: {analysis.standalone_question}\n")
    if analysis.intent != "bank_query":
        print(f"Respuesta directa: {analysis.reply}")
        return

    # 2. Retrieve candidates and rerank them
    started = time.perf_counter()
    candidates = retriever.retrieve(analysis.standalone_question, settings.retrieval_top_k)
    timings["retrieve"] = time.perf_counter() - started

    started = time.perf_counter()
    context = reranker.rerank(analysis.standalone_question, candidates, settings.rerank_top_n)
    timings["rerank"] = time.perf_counter() - started
    print("Contexto (después del reranker):")
    for number, chunk in enumerate(context, start=1):
        print(f"  [{number}] {chunk.score:6.2f}  {chunk.title[:50]}")

    # 3. Generate the answer
    started = time.perf_counter()
    answer = llm.invoke(answer_messages(question, context)).content
    timings["generate"] = time.perf_counter() - started

    print(f"\nRespuesta:\n{answer}\n")
    print("Fuentes citadas:")
    for source in cited_sources(answer, context):
        print(f"  - {source['title']}: {source['url']}")
    print("\nTiempos: " + "  ".join(f"{step}={seconds:.1f}s" for step, seconds in timings.items()))


if __name__ == "__main__":
    main(sys.argv[1].strip())
