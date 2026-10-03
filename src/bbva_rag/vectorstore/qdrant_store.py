"""Capa de almacenamiento e indexación en la Base de Datos Vectorial
(Qdrant) vectores densos y dispersos"""

from qdrant_client import QdrantClient, models

from bbva_rag.embeddings.sparse_bm25 import SparseVector

DENSE = "dense"
SPARSE = "bm25"
PAYLOAD_FIELDS = ("url", "title", "section", "fetched_at", "position", "text")


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
                    SPARSE: models.SparseVector(indices=sparse.indices, values=sparse.values),
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
