"""Estrategias de recuperación (Patrón de estrategia):
   misma interfaz, diferentes métodos de búsqueda"""


from bbva_rag.embeddings.base import Embedder
from bbva_rag.embeddings.sparse_bm25 import BM25Encoder
from bbva_rag.retrieval.base import RetrievedChunk
from bbva_rag.vectorstore.qdrant_store import QdrantStore


class SemanticRetriever:
    name = "semantic"

    def __init__(self, store: QdrantStore, embedder: Embedder):
        self._store = store
        self._embedder = embedder

    def retrieve(self, query: str, limit: int) -> list[RetrievedChunk]:
        return self._store.search_dense(self._embedder.embed_query(query), limit)


class KeywordRetriever:
    name = "bm25"

    def __init__(self, store: QdrantStore, bm25: BM25Encoder):
        self._store = store
        self._bm25 = bm25

    def retrieve(self, query: str, limit: int) -> list[RetrievedChunk]:
        return self._store.search_sparse(self._bm25.embed_query(query), limit)


class HybridRetriever:
    name = "hybrid"

    def __init__(self, store: QdrantStore, embedder: Embedder, bm25: BM25Encoder):
        self._store = store
        self._embedder = embedder
        self._bm25 = bm25

    def retrieve(self, query: str, limit: int) -> list[RetrievedChunk]:
        dense = self._embedder.embed_query(query)
        sparse = self._bm25.embed_query(query)
        return self._store.search_hybrid(dense, sparse, limit)