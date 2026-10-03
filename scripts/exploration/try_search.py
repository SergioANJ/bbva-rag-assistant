"""Exploración: comparación de la búsqueda semántica, BM25 e híbrida (RRF) en preguntas reales"""


from qdrant_client import QdrantClient, models

from bbva_rag.config import get_settings
from bbva_rag.embeddings.factory import create_embedder
from bbva_rag.embeddings.sparse_bm25 import BM25Encoder
from bbva_rag.vectorstore.qdrant_store import DENSE, SPARSE

QUESTIONS = [
    "¿Cómo abro un CDT?",
    "¿Cuánto me cobran por tener la tarjeta de crédito?",
    "¿Cuánto cuesta retirar en un cajero de otro banco?",
    "¿Qué es Bre-B?",
    "¿Qué es el fleteo?",
]
TOP_K = 3


def show(label: str, points) -> None:
    print(f"  {label}")
    for point in points:
        path = point.payload["url"].split("bancolombia.com")[-1]
        print(f"    {point.score:6.3f}  {point.payload['title'][:40]:40}  {path[:60]}")


def main() -> None:
    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url)
    embedder = create_embedder(settings)
    bm25 = BM25Encoder(settings.sparse_model, settings.sparse_language)
    collection = settings.qdrant_collection

    for question in QUESTIONS:
        dense = embedder.embed_query(question)
        sparse_raw = bm25.embed_query(question)
        sparse = models.SparseVector(indices=sparse_raw.indices, values=sparse_raw.values)
        print(f"\n=== {question}")

        semantic = client.query_points(
            collection, query=dense, using=DENSE, limit=TOP_K, with_payload=True
        ).points
        show("Semántica", semantic)

        keyword = client.query_points(
            collection, query=sparse, using=SPARSE, limit=TOP_K, with_payload=True
        ).points
        show("BM25", keyword)

        hybrid = client.query_points(
            collection,
            prefetch=[
                models.Prefetch(query=dense, using=DENSE, limit=20),
                models.Prefetch(query=sparse, using=SPARSE, limit=20),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=TOP_K,
            with_payload=True,
        ).points
        show("Híbrida (RRF)", hybrid)


if __name__ == "__main__":
    main()