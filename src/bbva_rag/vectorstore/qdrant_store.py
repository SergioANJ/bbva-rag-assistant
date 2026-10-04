"""Capa de almacenamiento e indexación en la Base de Datos Vectorial
(Qdrant) vectores densos y dispersos"""

import time

from qdrant_client import QdrantClient, models

from bbva_rag.embeddings.sparse_bm25 import SparseVector
from bbva_rag.retrieval.base import RetrievedChunk

DENSE = "dense"
SPARSE = "bm25"
PAYLOAD_FIELDS = ("url", "title", "section", "fetched_at", "position", "text")


def _to_qdrant_sparse(vector: SparseVector) -> models.SparseVector:
    return models.SparseVector(indices=vector.indices, values=vector.values)


def _to_chunk(point: models.ScoredPoint) -> RetrievedChunk:
    payload = point.payload or {}
    return RetrievedChunk(
        chunk_id=str(point.id),
        url=payload["url"],
        title=payload["title"],
        section=payload["section"],
        text=payload["text"],
        score=point.score,
    )


class QdrantStore:
    def __init__(self, url: str, collection: str, client: QdrantClient | None = None):
        self.collection = collection
        self._client = client or QdrantClient(url=url, timeout=30)

    # Este método limpia y configuta la base de datos desde cero
    def recreate_collection(self, dense_dimensions: int) -> None:
        """Reconstrucción completa: elimine la colección si existe y créela vacía"""
        if self._client.collection_exists(self.collection):
            self._client.delete_collection(self.collection)
        self._client.create_collection(
            collection_name=self.collection,
            vectors_config={
                DENSE: models.VectorParams(size=dense_dimensions, distance=models.Distance.COSINE)
            },
            sparse_vectors_config={SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)},
        )
        self._client.create_payload_index(
            collection_name=self.collection,
            field_name="section",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

    def upsert_chunks(
        self,
        chunks: list[dict],
        dense_vectors: list[list[float]],
        sparse_vectors: list[SparseVector],
        batch_size: int = 256,
    ) -> None:
        points = [
            models.PointStruct(
                id=chunk["chunk_id"],
                vector={
                    DENSE: dense,
                    SPARSE: _to_qdrant_sparse(sparse),
                },
                payload={field: chunk[field] for field in PAYLOAD_FIELDS},
            )
            for chunk, dense, sparse in zip(chunks, dense_vectors, sparse_vectors, strict=True)
        ]
        for start in range(0, len(points), batch_size):
            self._client.upsert(
                collection_name=self.collection,
                points=points[start : start + batch_size],
                wait=True,
            )

    def count(self) -> int:
        return self._client.count(collection_name=self.collection, exact=True).count

    def search_dense(self, vector: list[float], limit: int) -> list[RetrievedChunk]:
        response = self._client.query_points(
            collection_name=self.collection,
            query=vector,
            using=DENSE,
            limit=limit,
            with_payload=True,
        )
        return [_to_chunk(point) for point in response.points]

    def search_sparse(self, vector: SparseVector, limit: int) -> list[RetrievedChunk]:
        response = self._client.query_points(
            collection_name=self.collection,
            query=_to_qdrant_sparse(vector),
            using=SPARSE,
            limit=limit,
            with_payload=True,
        )
        return [_to_chunk(point) for point in response.points]

    def search_hybrid(
        self, dense: list[float], sparse: SparseVector, limit: int
    ) -> list[RetrievedChunk]:
        prefetch_limit = limit * 2
        response = self._client.query_points(
            collection_name=self.collection,
            prefetch=[
                models.Prefetch(query=dense, using=DENSE, limit=prefetch_limit),
                models.Prefetch(
                    query=_to_qdrant_sparse(sparse), using=SPARSE, limit=prefetch_limit
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=limit,
            with_payload=True,
        )
        return [_to_chunk(point) for point in response.points]
    
    def wait_until_ready(self, timeout_seconds: float = 60, interval_seconds: float = 2) -> None:
        deadline = time.monotonic() + timeout_seconds
        while True:
            try:
                self._client.get_collections()
                return
            except Exception as error:
                if time.monotonic() > deadline:
                    raise RuntimeError("Qdrant is not reachable") from error
                time.sleep(interval_seconds)

    def is_populated(self) -> bool:
        return self._client.collection_exists(self.collection) and self.count() > 0