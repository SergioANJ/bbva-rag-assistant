
"""Conexiones de grafos: nodos, aristas y aristas condicionales."""

from langgraph.graph import END, START, StateGraph

from bbva_rag.config import Settings
from bbva_rag.embeddings.factory import create_embedder
from bbva_rag.embeddings.sparse_bm25 import BM25Encoder
from bbva_rag.graph.nodes import RAGNodes
from bbva_rag.graph.state import RAGState
from bbva_rag.llm.factory import create_chat_model
from bbva_rag.retrieval.factory import create_retriever
from bbva_rag.retrieval.reranker import CrossEncoderReranker
from bbva_rag.vectorstore.qdrant_store import QdrantStore


def build_graph(nodes: RAGNodes):
    graph = StateGraph(RAGState)

    graph.add_node("analyze_query", nodes.analyze_query)
    graph.add_node("retrieve", nodes.retrieve)
    graph.add_node("rerank", nodes.rerank)
    graph.add_node("rewrite_query", nodes.rewrite_query)
    graph.add_node("generate", nodes.generate)
    graph.add_node("no_answer", nodes.no_answer)
    graph.add_node("direct_reply", nodes.direct_reply)

    graph.add_edge(START, "analyze_query")
    graph.add_conditional_edges(
        "analyze_query",
        nodes.route_by_intent,
        {"retrieve": "retrieve", "direct_reply": "direct_reply"},
    )
    graph.add_edge("retrieve", "rerank")
    graph.add_conditional_edges(
        "rerank",
        nodes.route_after_rerank,
        {"generate": "generate", "rewrite_query": "rewrite_query", "no_answer": "no_answer"},
    )
    graph.add_edge("rewrite_query", "retrieve")
    for final_node in ("generate", "no_answer", "direct_reply"):
        graph.add_edge(final_node, END)

    return graph.compile()


def create_rag_graph(settings: Settings):
    """Ensambla todas las dependencias y devuelve el grafo compilado."""
    cache_dir = str(settings.models_cache_dir)
    store = QdrantStore(settings.qdrant_url, settings.qdrant_collection)
    bm25 = BM25Encoder(settings.sparse_model, settings.sparse_language, cache_dir)
    retriever = create_retriever(
        settings.retrieval_strategy, store, create_embedder(settings), bm25
    )
    reranker = CrossEncoderReranker(settings.reranker_model, cache_dir)
    nodes = RAGNodes(create_chat_model(settings), retriever, reranker, settings)
    return build_graph(nodes)