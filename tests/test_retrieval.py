from qdrant_client import QdrantClient

from bbva_rag.embeddings.sparse_bm25 import SparseVector
from bbva_rag.retrieval.factory import create_retriever
from bbva_rag.retrieval.strategies import HybridRetriever, KeywordRetriever, SemanticRetriever
from bbva_rag.vectorstore.qdrant_store import QdrantStore


def make_chunk(chunk_id: str, name: str) -> dict:
    return {
        "chunk_id": chunk_id,
        "url": f"https://x.com/{name}",
        "title": name,
        "section": "personas",
        "fetched_at": "2026-10-03",
        "position": 0,
        "text": f"Fuente: {name}",
    }


# Tres fragmentos: "cdt" apunta a [1, 0], "tarjeta" a [0, 1]; cada uno tiene s
# su propio índice de palabras clave.
CHUNKS = [
    make_chunk("00000000-0000-0000-0000-000000000001", "cdt"),
    make_chunk("00000000-0000-0000-0000-000000000002", "tarjeta"),
    make_chunk("00000000-0000-0000-0000-000000000003", "cuenta"),
]
DENSE = [[1.0, 0.0], [0.0, 1.0], [0.7, 0.7]]
SPARSE = [SparseVector([1], [1.0]), SparseVector([2], [1.0]), SparseVector([3], [1.0])]


class FakeEmbedder:
    dimensions = 2

    def embed_query(self, text: str) -> list[float]:
        return [1.0, 0.0]  # siempre "significa" cdt


class FakeBM25:
    def embed_query(self, text: str) -> SparseVector:
        return SparseVector([2], [1.0])  # siempre contiene la palabra clave "tarjeta"


def make_store() -> QdrantStore:
    store = QdrantStore("unused", "test_chunks", client=QdrantClient(":memory:"))
    store.recreate_collection(dense_dimensions=2)
    store.upsert_chunks(CHUNKS, DENSE, SPARSE)
    return store


def test_semantic_returns_the_closest_meaning():
    results = SemanticRetriever(make_store(), FakeEmbedder()).retrieve("q", limit=1)
    assert results[0].title == "cdt"


def test_keyword_returns_the_exact_term_match():
    results = KeywordRetriever(make_store(), FakeBM25()).retrieve("q", limit=3)
    assert [r.title for r in results] == ["tarjeta"]


def test_hybrid_combines_both_searches():
    results = HybridRetriever(make_store(), FakeEmbedder(), FakeBM25()).retrieve("q", limit=2)
    assert {r.title for r in results} == {"cdt", "tarjeta"}


def test_factory_builds_the_configured_strategy():
    store = make_store()
    retriever = create_retriever("bm25", store, FakeEmbedder(), FakeBM25())
    assert retriever.name == "bm25"
