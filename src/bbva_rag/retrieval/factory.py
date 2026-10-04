"""Fábrica: construye la estrategia de recuperación seleccionada
   en la configuración"""

from bbva_rag.embeddings.base import Embedder
from bbva_rag.embeddings.sparse_bm25 import BM25Encoder
from bbva_rag.retrieval.base import Retriever
from bbva_rag.retrieval.strategies import HybridRetriever, KeywordRetriever, SemanticRetriever
from bbva_rag.vectorstore.qdrant_store import QdrantStore


def create_retriever(
    strategy: str, store: QdrantStore, embedder: Embedder, bm25: BM25Encoder
) -> Retriever:
    if strategy == "semantic":
        return SemanticRetriever(store, embedder)
    if strategy == "bm25":
        return KeywordRetriever(store, bm25)
    if strategy == "hybrid":
        return HybridRetriever(store, embedder, bm25)
    raise ValueError(f"Unsupported retrieval strategy: {strategy}")