import pytest
from qdrant_client import QdrantClient

from bbva_rag.embeddings.sparse_bm25 import SparseVector
from bbva_rag.vectorstore.qdrant_store import QdrantStore

CHUNKS = [
    {
        "chunk_id": "3f6a1c2e-8b4d-5e7f-9a01-23456789abcd",
        "url": "https://x.com/cdt",
        "title": "CDT",
        "section": "personas",
        "fetched_at": "2026-10-03",
        "position": 0,
        "text": "Fuente: CDT (personas)\n\nInvierte en un CDT",
    },
    {
        "chunk_id": "9b1e2d3c-4a5f-5b6c-8d7e-0f1a2b3c4d5e",
        "url": "https://x.com/tarjeta",
        "title": "Tarjeta",
        "section": "personas",
        "fetched_at": "2026-10-03",
        "position": 0,
        "text": "Fuente: Tarjeta (personas)\n\nCuota de manejo",
    },
]
DENSE = [[0.1, 0.2, 0.3], [0.3, 0.2, 0.1]]
SPARSE = [SparseVector([1, 2], [1.0, 0.5]), SparseVector([3], [1.0])]


def make_store() -> QdrantStore:
    store = QdrantStore("unused", "test_chunks", client=QdrantClient(":memory:"))
    store.recreate_collection(dense_dimensions=3)
    return store


def test_upsert_stores_every_chunk():
    store = make_store()
    store.upsert_chunks(CHUNKS, DENSE, SPARSE)
    assert store.count() == 2


def test_recreate_starts_from_an_empty_collection():
    store = make_store()
    store.upsert_chunks(CHUNKS, DENSE, SPARSE)
    store.recreate_collection(dense_dimensions=3)
    assert store.count() == 0


def test_misaligned_vectors_raise_an_error():
    store = make_store()
    with pytest.raises(ValueError):
        store.upsert_chunks(CHUNKS, DENSE[:1], SPARSE)
